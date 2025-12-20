# kubectl kustomize 的12种常见用法，编排效率直线提升

## 1. 资源文件任意组合

通过 `resources` 字段组合多个 YAML 文件：

```yaml
resources:
  - deployment.yaml
  - service.yaml
  - configmap.yaml
```

## 2. 统一命名前缀和后缀

为所有资源添加统一的前缀或后缀，避免命名冲突：

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - deployment.yaml

namePrefix: dev-
nameSuffix: -v1
# 结果：dev-nginx-deployment-v1
```

## 3. 统一设置命名空间

为所有资源设置相同的命名空间：

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - deployment.yaml
  - service.yaml

namespace: production
```

## 4. 镜像替换

批量替换容器镜像，支持标签更新：

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - deployment.yaml

images:
  - name: nginx # 这里是镜像名字，不是容器名字
    newName: nginx
    newTag: "1.21.0"
```

## 5. 批量定义标签和注解

为容器注入环境变量：

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - deployment.yaml

commonLabels:
  app: nginx
  env: production

commonAnnotations:
  description: "Production environment"
```

## 6. ConfigMap 和 Secret 生成器

动态生成 ConfigMap 和 Secret：

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - deployment.yaml

# 从文件生成 ConfigMap
configMapGenerator:
  - name: app-config
    files:
      - application.yaml
    # 或者从字面量生成
    literals:
      - DB_HOST=mysql
      - DB_PORT=3306

# 从文件生成 Secret
secretGenerator:
  - name: app-secret
    files:
      - password.txt
    literals:
      - user=foo
      - password=bar
    type: Opaque

#选择指定，禁用secret或configmap生成hash
generatorOptions:
  disableNameSuffixHash: true

```

## 7. 策略合并补丁

使用 `patchesStrategicMerge` 进行策略合并补丁：

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - deployment.yaml

patchesStrategicMerge:
  - increase-replicas.yaml
```

`affinity-patches.yaml` 示例：
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
          - matchExpressions:
              - key: kubernetes.io/hostname
                operator: In
                values: ["minkube"]
```

## 8. JSON 6902 补丁

使用 JSON Patch 格式进行精确补丁：

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - deployment.yaml

patchesJson6902:
  - target:
      group: apps
      version: v1
      kind: Deployment
      name: nginx-deployment
    path: add-env-patch.yaml
```

`add-env-patch.yaml` 示例：
```yaml
- op: add
  path: /spec/template/spec/containers/0/env
  value:
    - name: ENV
      value: production
```

```
- op: add
  path: /spec/replicas
  value: 3
```

## 9. Inline 补丁

直接在 kustomization.yaml 中定义补丁，无需额外文件：

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - deployment.yaml

patches:
  - target:
      kind: Deployment
      name: nginx-deployment
    patch: |-
      - op: replace
        path: /spec/replicas
        value: 3
  # 或者使用策略合并方式
  - patch: |-
      apiVersion: apps/v1
      kind: Deployment
      metadata:
        name: nginx-deployment
      spec:
        replicas: 3
    target:
      kind: Deployment
```

## 10. 副本数修改

直接修改 Deployment 的副本数：

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - deployment.yaml

replicas:
  - name: nginx-deployment
    count: 5
```

- op: replace
  path: /spec/ports/0/nodePort
  value: 32080

## 11. 多环境管理（Base + Overlay）

使用 base 和 overlay 模式管理不同环境：

**base/kustomization.yaml:**
```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - deployment.yaml
  - service.yaml

commonLabels:
  app: nginx
```

**overlays/dev/kustomization.yaml:**
```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - ../../base

namePrefix: dev-
namespace: dev

replicas:
  - name: nginx-deployment
    count: 2

images:
  - name: nginx
    newTag: "dev-latest"

configMapGenerator:
  - name: app-config
    literals:
      - ENV=development
```

**overlays/prod/kustomization.yaml:**
```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - ../../base

namePrefix: prod-
namespace: production

replicas:
  - name: nginx-deployment
    count: 5

images:
  - name: nginx
    newTag: "1.21.0"

configMapGenerator:
  - name: app-config
    literals:
      - ENV=production
```

## 使用示例

### 预览生成的 YAML
```bash
kubectl kustomize kustomize_usage/demo/
```

### 直接应用到集群
```bash
kubectl apply -k kustomize_usage/demo/
```

### 多环境部署
```bash
# 开发环境
kubectl apply -k overlays/dev/

# 生产环境
kubectl apply -k overlays/prod/
```

## 最佳实践

1. **使用 base + overlay 模式**：将通用配置放在 base，环境特定配置放在 overlay
2. **版本控制**：将 base 和所有 overlay 都纳入版本控制
3. **补丁顺序**：了解补丁应用的顺序（resources → patches → replicas → images → namespace → namePrefix）
4. **测试验证**：使用 `kubectl kustomize` 预览生成的 YAML 再应用
5. **避免重复**：利用 commonLabels 和 commonAnnotations 统一标签和注解