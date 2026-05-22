# Hermes自定义运行终端

## 背景说明

Hermes可以自定义运行终端，这样可以灵活的将Agent运行在指定的环境。例如本地电脑、容器环境、远程节点等。

下面通过三个实战例子来演示：

- Local：开发一个todolist项目，并结合git worktree并行开发。
- Docker：把测试环境封装到本地Docker中，让Hermes在容器里跑测试。
- SSH：通过远程主机操作K8S集群，部署一个Nginx服务。

## Local backend terminal：本地开发实战

Local运行终端适合本地代码开发。
这个例子演示一个`todolist`项目：先让Hermes在`main`分支完成API接口，然后用`git worktree`创建两个独立工作区，一个让Hermes开发前端页面，一个让Hermes补充自动化测试。

这样演示的重点不是`todolist`本身有多复杂，而是让大家看到Hermes可以在不同本地目录中推进任务，不需要反复`git checkout`，也不会让多个需求互相污染。

### 第一步：进入Hermes并初始化Todo API

这里假设`hermes-todolist`项目已经提前在GitHub创建好。先把项目克隆到本地，然后进入Hermes：

```shell
git clone git@github.com:<your-name>/hermes-todolist.git
cd hermes-todolist
hermes
```

进入Hermes对话后，直接输入提示词：

```md
用fastapi帮我实现一个todolist的后端API，接口包括对任务的增删改查操作。实现完成后，请编写对应的API接口文档。
```

### 第二步：API实现完成后，让Hermes创建两个worktree，分别实现前端开发和接口测试

```shell
git worktree add ../hermes-todolist-web -b feature/web-ui
git worktree add ../hermes-todolist-test -b feature/api-test
git worktree list
```

预期可以看到三个目录：

```text
hermes-todolist       main
hermes-todolist-web   feature/web-ui
hermes-todolist-test  feature/api-test
```

git worktreee的好处：不是在同一个目录里来回切分支，而是让Hermes分别进入不同worktree完成不同任务。

### 第三步：在前端worktree中让Hermes开发页面

新开一个终端，进入前端worktree，并启动Hermes：

```shell
cd ../hermes-todolist-web
hermes
```

输入提示词：

```md
请基于当前todolist API补充一个基于react+typescript实现的前端项目。
```

Hermes预期会自己修改Express静态资源配置、创建前端页面、启动服务并给出验证方式。

### 第四步：在测试worktree中让Hermes补充测试

再开一个终端，进入测试worktree，并启动Hermes：

```shell
cd ../hermes-todolist-test
hermes
```

输入提示词：

```md
请基于该项目编写api接口测试，测试完毕后，请生成对应的测试报告。
```

### Local小结

Local运行终端的优势：

- Hermes可以直接使用本机已有的Node、Git、浏览器等环境。
- `git worktree`让多个需求并行推进，不需要频繁切换分支。
- 前端开发和测试修复可以在两个独立目录里进行，互不影响。

## Docker backend terminal：测试实战演示


准备一个包含了项目所需依赖的镜像。

hermes

创建一个agent，并修改其执行的backend



### Docker小结

Docker运行终端的优势：

- Hermes执行命令时使用的是容器环境，不依赖本机Python版本。
- 数据库、运行时、系统依赖都由`docker-compose.yml`固定下来。
- 团队成员只要使用同一份Docker配置，就能复现同样的测试结果。
- 对有数据库、消息队列、系统包依赖的项目，Docker比直接在本机跑更稳定。

## SSH backend terminal：远程运维管理实战

第一步如何配置

```shell
xxx
```

---

第二步演示

SSH运行终端适合远程服务器运维、集群操作、线上环境排查等场景。
这个例子演示：Hermes通过SSH进入远程主机，在远程主机上操作K8S集群，部署一个Nginx服务并验证运行状态。

这里默认SSH和K8S权限都已经配置好，远程主机上可以直接执行`kubectl`。

### 第一步：进入SSH运行终端中的Hermes

切换到SSH运行终端后，执行：

```shell
hermes
```

进入Hermes对话后，先让它检查远程环境：

```md
请检查当前远程主机上的K8S环境是否可用。

要求：
1. 执行kubectl version --client。
2. 执行kubectl get nodes。
3. 如果集群不可用，请只说明问题，不要继续部署。
4. 如果集群可用，请总结当前节点状态。
```

Hermes预期会执行：

```shell
kubectl version --client
kubectl get nodes
```

预期输出类似：

```text
NAME          STATUS   ROLES           AGE   VERSION
k8s-master    Ready    control-plane   30d   v1.29.0
k8s-worker-1  Ready    <none>          30d   v1.29.0
```

### 第二步：让Hermes部署Nginx

确认集群可用后，继续输入：

```md
请在当前K8S集群中部署一个Nginx演示服务。

要求：
1. 创建namespace：hermes-demo。
2. 创建Deployment：nginx，镜像使用nginx:1.25-alpine，副本数为2。
3. 创建Service：nginx，类型使用ClusterIP，端口80。
4. 等待Deployment rollout完成。
5. 查看Pod和Service状态。
6. 如果可以，请用临时curl容器访问http://nginx验证服务。
7. 最后把执行过的关键命令和验证结果总结给我。
```

Hermes可以使用命令式方式完成：

```shell
kubectl create namespace hermes-demo
kubectl -n hermes-demo create deployment nginx --image=nginx:1.25-alpine --replicas=2
kubectl -n hermes-demo expose deployment nginx --port=80 --target-port=80 --type=ClusterIP
kubectl -n hermes-demo rollout status deployment/nginx
kubectl -n hermes-demo get pods -o wide
kubectl -n hermes-demo get svc
kubectl -n hermes-demo run curl --rm -it --image=curlimages/curl:8.8.0 --restart=Never -- http://nginx
```

也可以让Hermes生成YAML后再执行`kubectl apply -f`。为了现场演示更直观，命令式方式更短。

预期Pod状态：

```text
NAME                     READY   STATUS    RESTARTS   AGE
nginx-xxxxxxxxxx-xxxxx   1/1     Running   0          30s
nginx-xxxxxxxxxx-yyyyy   1/1     Running   0          30s
```

预期Service状态：

```text
NAME    TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)   AGE
nginx   ClusterIP   10.96.xxx.xxx   <none>        80/TCP    30s
```

如果临时curl容器可以访问服务，预期能看到Nginx默认欢迎页面中的内容：

```text
Welcome to nginx!
```

### 第三步：让Hermes清理演示资源

演示完成后，继续输入：

```md
请清理刚才创建的K8S演示资源。

要求：
1. 只删除namespace hermes-demo。
2. 删除后确认namespace已经不存在。
3. 不要删除其他namespace或集群资源。
4. 最后总结清理结果。
```

Hermes预期执行：

```shell
kubectl delete namespace hermes-demo
kubectl get namespace hermes-demo
```

namespace删除后，第二条命令预期会看到：

```text
Error from server (NotFound): namespaces "hermes-demo" not found
```

### SSH小结

SSH运行终端的优势：

- Hermes执行的是远程主机上的命令，可以直接使用远程机器已有的`kubectl`、内网权限和运维工具。
- 本机不需要暴露K8S配置，也不需要把集群凭证复制到本地。
- 适合远程排障、服务部署、日志查看、集群巡检等运维任务。
- 人只需要描述目标、边界和验证要求，Hermes负责在远程环境执行和确认结果。

## 总结

Hermes自定义运行终端的关键不是多一种配置，而是让Agent进入正确的执行环境：

- Local适合本地开发，尤其适合结合`git worktree`并行推进多个代码任务。
- Docker适合可复现测试环境，避免本机依赖污染，也方便团队统一运行结果。
- SSH适合远程运维和集群操作，让Hermes直接在目标机器上完成检查、部署和验证。

实际使用时，可以根据任务选择运行终端：代码在本机就用Local，环境复杂就用Docker，目标资源在远程就用SSH。进入对应终端后，执行`hermes`，再用自然语言把任务交给Hermes即可。