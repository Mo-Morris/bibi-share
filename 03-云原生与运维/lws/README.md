# LWS 安装与资源操作

[知识首页](../../README.md) / [云原生与运维](../README.md)

## 教程与示例索引

- [安装 LWS](#1-安装-lws)：安装 CRD 和控制器，并检查就绪状态。
- [资源操作](#2-资源操作)：部署示例、观察启动、查看日志和整组扩缩容。
- [演示 YAML](./demo/lws-demo.yaml)：包含命名空间和 LeaderWorkerSet，使用 BusyBox 演示 1 个 Leader 与 2 个 Worker。

## 开篇

LeaderWorkerSet（LWS）把 **1 个 Leader + 若干 Worker** 作为一个完整小组管理。本教程使用 [BusyBox 示例](./demo/lws-demo.yaml)，演示两个行为：Leader 就绪后再创建 Worker，以及按完整小组扩缩容。

示例使用 `busybox:1.37` 镜像和几行 shell 命令，单节点 Kubernetes 集群即可运行，镜像由集群拉取。

## 1. 安装 LWS

Kubernetes 默认不认识 `LeaderWorkerSet`。安装 LWS 会补上两部分：

| 组件 | 作用 |
| --- | --- |
| CRD | 注册 `LeaderWorkerSet` 资源类型，让 API 接受示例 YAML |
| 控制器 | 根据配置创建和管理 Leader、Worker，执行启动策略和整组扩缩容 |

在当前集群安装官方发布版本：

```bash
LWS_VERSION=v1.0.0
kubectl apply --server-side -f \
  "https://github.com/kubernetes-sigs/lws/releases/download/${LWS_VERSION}/manifests.yaml"

# 等待自定义资源类型注册完成。
kubectl wait crd/leaderworkersets.leaderworkerset.x-k8s.io \
  --for=condition=Established --timeout=60s

# 等待控制器就绪。
kubectl -n lws-system rollout status deployment/lws-controller-manager \
  --timeout=300s
```

检查安装结果：

```bash
kubectl get crd leaderworkersets.leaderworkerset.x-k8s.io
kubectl -n lws-system get pods
```

能够查到 CRD，且控制器 Pod 已就绪，才继续部署示例。控制器安装在 `lws-system`，示例资源放在 `lws-demo`。

## 2. 资源操作

以下命令在仓库的 `03-云原生与运维/lws/` 目录执行。`get pods -w` 持续观察变化，按 `Ctrl+C` 结束观察。

### 部署并观察启动

```bash
kubectl apply -f demo/lws-demo.yaml
kubectl -n lws-demo get pods -w
```

Leader 就绪后，两个 Worker 才会出现，最终共 3 个 Pod。

### 查看资源与日志

```bash
kubectl -n lws-demo get leaderworkerset busybox-demo
kubectl -n lws-demo get statefulsets,pods,services

# 显示小组编号和组内索引。
kubectl -n lws-demo get pods \
  -L leaderworkerset.sigs.k8s.io/group-index,leaderworkerset.sigs.k8s.io/worker-index

# 查看 Leader 和 Worker 的启动日志。
kubectl -n lws-demo logs busybox-demo-0 --timestamps
kubectl -n lws-demo logs busybox-demo-0-1 --timestamps
kubectl -n lws-demo logs busybox-demo-0-2 --timestamps
```

### 扩缩容

扩为 2 组，共 6 个 Pod：

```bash
kubectl -n lws-demo scale leaderworkerset/busybox-demo --replicas=2
kubectl -n lws-demo get pods -w
```

缩回 1 组，共 3 个 Pod：

```bash
kubectl -n lws-demo scale leaderworkerset/busybox-demo --replicas=1
kubectl -n lws-demo get pods -w
```

`scale` 不会修改本地 YAML；再次 `apply` 会按文件中的 `replicas` 设置组数。
