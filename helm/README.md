

## Helm 介绍
Helm 用来把一堆 K8s YAML，做成一个可参数化、可复用、可版本管理、可一键安装/升级/回滚的“应用包”

## Helm安装
直接去GitHub下载

## Helm 结构解析
解析每个文件的作用

## Helm 渲染语法
include
with
.values直接引用

## Helm 管理服务版本
安装
```
helm install <name> .
```
升级
```
# 只要自行就会触发
helm upgrade web --atomic
```
回滚
```
# 默认回滚到上一个版本
helm rollout 
# 回滚到指定版本
helm rollout web 2
```

## Helm 仓库
谷歌搜索helm repo