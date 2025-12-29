# Kubernetes 调度详解

## 何为调度

Kubernetes 调度（Scheduling）是指将 Pod 分配到集群中合适节点的过程。调度器（Scheduler）是 Kubernetes 控制平面的核心组件之一，负责根据资源需求、约束条件、亲和性规则等，为每个新创建的 Pod 选择一个最优的节点运行。

调度器的工作流程：
1. **过滤（Filtering）**：根据硬性约束条件（如资源需求、节点选择器等）过滤掉不满足条件的节点
2. **评分（Scoring）**：对剩余的节点进行评分，选择得分最高的节点
3. **绑定（Binding）**：将 Pod 绑定到选中的节点

## 基于Kind搭建多节点环境

### 配置文件

创建 `kind-config.yaml` 文件：

```yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
name: cluster
nodes:
- role: control-plane
- role: control-plane
- role: worker
- role: worker
- role: worker
- role: worker
- role: worker
- role: worker
```

### 节点的个数分配，保证下面的演示能完成

- **1个控制平面节点（master）**：运行 Kubernetes 控制平面组件
- **3个工作节点（worker）**：用于运行 Pod，分布在不同的 zone（zone-a、zone-b、zone-c）

使用以下命令创建集群：

```bash
kind create cluster --config kind-config.yaml
```

验证节点：

```bash
kubectl get nodes --show-labels
```

## 污点与容忍

**污点（Taint）**用于标记节点，表示该节点不接受某些 Pod。**容忍（Toleration）**用于标记 Pod，允许 Pod 调度到带有特定污点的节点上。

### 给节点添加污点

```bash
# 添加污点：key=value:effect
kubectl taint nodes <node-name> key=value:NoSchedule

# 示例：标记节点为专用节点
kubectl taint nodes worker-1 gpu=true:NoSchedule
```

污点效果（effect）：
- **NoSchedule**：不会调度新的 Pod（除非有容忍）
- **PreferNoSchedule**：尽量不调度，但不是强制
- **NoExecute**：不仅不调度新 Pod，还会驱逐现有 Pod（除非有容忍）

### 移除污点

```bash
kubectl taint nodes <node-name> key=value:NoSchedule-
```

### Pod 添加容忍

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: gpu-pod
spec:
  containers:
  - name: nginx
    image: nginx
  tolerations:
  - key: "gpu"
    operator: "Equal" # Exists
    value: "true"
    effect: "NoSchedule"
```

## 节点名称调度

使用 `nodeName` 直接指定 Pod 运行的节点（跳过调度器）。

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx-pod
spec:
  nodeName: worker-1  # 直接指定节点名称
  containers:
  - name: nginx
    image: nginx
```

**注意**：`nodeName` 是硬性约束，如果指定的节点不存在或不可用，Pod 将无法运行。

## 节点标签筛选调度

使用 `nodeSelector` 根据节点标签选择节点。

### 给节点添加标签

```bash
kubectl label nodes worker-1 disktype=ssd
kubectl label nodes worker-2 disktype=hdd
kubectl label nodes worker-1 zone=beijing
kubectl label nodes worker-2 zone=shanghai
kubectl label nodes worker-3 zone=hangzhou
```

### 使用 nodeSelector

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx-pod
spec:
  nodeSelector:
    disktype: ssd  # 只调度到带有 disktype=ssd 标签的节点
  containers:
  - name: nginx
    image: nginx
```

## 节点硬性约束亲和调度

使用 `nodeAffinity` 的 `requiredDuringSchedulingIgnoredDuringExecution` 实现硬性约束。

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx-pod
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: zone
            operator: In
            values:
            - beijing
            - shanghai
  containers:
  - name: nginx
    image: nginx
```

**说明**：
- `requiredDuringSchedulingIgnoredDuringExecution`：调度时必须满足，运行后不再检查
- `operator` 支持：In、NotIn、Exists、DoesNotExist、Gt、Lt

## 节点软性约束亲和调度

使用 `nodeAffinity` 的 `preferredDuringSchedulingIgnoredDuringExecution` 实现软性约束。

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx-pod
spec:
  affinity:
    nodeAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        preference:
          matchExpressions:
          - key: zone
            operator: In
            values:
            - beijing
      - weight: 50
        preference:
          matchExpressions:
          - key: disktype
            operator: In
            values:
            - shanghai
  containers:
  - name: nginx
    image: nginx
```

**说明**：
- `preferredDuringSchedulingIgnoredDuringExecution`：优先满足，但不强制
- `weight`：权重值（1-100），权重越高优先级越高

## Pod硬性约束亲和调度

使用 `podAffinity` 的 `requiredDuringSchedulingIgnoredDuringExecution` 实现 Pod 之间的硬性亲和。

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx-pod
  labels:
    app: nginx
spec:
  affinity:
    podAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchExpressions:
          - key: app
            operator: In
            values:
            - redis
        topologyKey: zone  # 必须与匹配的 Pod 在同一个 zone
  containers:
  - name: nginx
    image: nginx
```

**说明**：
- `topologyKey`：拓扑域键，如 `zone`、`node`、`rack` 等
- 此 Pod 必须与带有 `app=redis` 标签的 Pod 运行在同一个 `zone`

## Pod软性约束亲和调度

使用 `podAffinity` 的 `preferredDuringSchedulingIgnoredDuringExecution` 实现 Pod 之间的软性亲和。

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx-pod
  labels:
    app: nginx
spec:
  affinity:
    podAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        podAffinityTerm:
          labelSelector:
            matchExpressions:
            - key: app
              operator: In
              values:
              - redis
          topologyKey: zone
  containers:
  - name: nginx
    image: nginx
```

**说明**：优先与带有 `app=redis` 标签的 Pod 运行在同一个 `zone`，但不强制。

## Pod硬性约束反亲和调度

使用 `podAntiAffinity` 的 `requiredDuringSchedulingIgnoredDuringExecution` 实现 Pod 之间的硬性反亲和。

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx-pod-1
  labels:
    app: nginx
spec:
  affinity:
    podAntiAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchExpressions:
          - key: app
            operator: In
            values:
            - nginx
        topologyKey: zone  # 不能与匹配的 Pod 在同一个 zone
  containers:
  - name: nginx
    image: nginx
```

**说明**：此 Pod 不能与带有 `app=nginx` 标签的 Pod 运行在同一个 `zone`。常用于实现高可用部署。

## Pod软性约束反亲和调度

使用 `podAntiAffinity` 的 `preferredDuringSchedulingIgnoredDuringExecution` 实现 Pod 之间的软性反亲和。

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx-pod-1
  labels:
    app: nginx
spec:
  affinity:
    podAntiAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        podAffinityTerm:
          labelSelector:
            matchExpressions:
            - key: app
              operator: In
              values:
              - nginx
          topologyKey: zone
  containers:
  - name: nginx
    image: nginx
```

**说明**：尽量不与带有 `app=nginx` 标签的 Pod 运行在同一个 `zone`，但不强制。

## 总结

| 调度方式 | 类型 | 用途 |
|---------|------|------|
| nodeName | 硬性 | 直接指定节点 |
| nodeSelector | 硬性 | 基于节点标签简单选择 |
| nodeAffinity (required) | 硬性 | 复杂的节点选择规则 |
| nodeAffinity (preferred) | 软性 | 节点偏好选择 |
| podAffinity (required) | 硬性 | Pod 必须与某些 Pod 在同一拓扑域 |
| podAffinity (preferred) | 软性 | Pod 优先与某些 Pod 在同一拓扑域 |
| podAntiAffinity (required) | 硬性 | Pod 不能与某些 Pod 在同一拓扑域 |
| podAntiAffinity (preferred) | 软性 | Pod 尽量不与某些 Pod 在同一拓扑域 |
| Taint & Toleration | 硬性 | 节点拒绝/接受特定 Pod |

## 实践建议

1. **生产环境**：优先使用软性约束（preferred），避免 Pod 无法调度
2. **高可用部署**：使用 `podAntiAffinity` 确保 Pod 分布在不同节点/区域
3. **专用节点**：使用 Taint 和 Toleration 实现节点专用
4. **资源优化**：结合节点标签和亲和性规则，实现资源的最优分配
