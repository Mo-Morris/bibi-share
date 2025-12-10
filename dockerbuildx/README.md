# buildx 使用指南

以下操作在linux/amd64环境演示。

## 开启docker实验特性(docker 1.19以及以下的版本)

```
vim /etc/docker/daemon.json
```
添加配置：
```json
{
    ...
    "experimental": true,
    ...
}
```
重启docker
```
systemct restart docker
```
## 安装buildx

直接下载最新版
https://github.com/docker/buildx
```
wget https://github.com/docker/buildx/releases/download/v0.30.1/buildx-v0.30.1.linux-amd64
mv buildx-v0.30.1.linux-amd64 buildx
chmod +x buildx
mv buildx /usr/local/bin
```

## 跨架构配置
例如，在 x86_64 主机上构建和测试适用于 ARM 架构的镜像。

安装qemu
```bash
sudo apt install -y qemu-user-static binfmt-support
```

启用qemu
```bash
docker run --rm --privileged multiarch/qemu-user-static --reset -p yes
```

## 创建buildx构建实例

默认已经有了一个构建实例，但是默认的构建器不支持并发构建镜像。
```
# 创建
buildx create --driver-opt network=host --platform=linux/arm64,linux/amd64 --name my-builder
# 使用
buildx use my-builder
# 初始化
buildx inspect --bootstrap
```
其他命令：
```
# 查询构建器
buildx ls
# 删除构建器
buildx rm my-builder
```

## 用buildx构建镜像
构建amd64

构建amd64+arm64
```
buildx build -t momorris/fastapi-demo:v1 . --platform linux/arm64,linux/amd64 --no-cache --progress=plain --push
```

## 注意事项
1. buildx因为牵涉到指令集转换，所以是一个很耗CPU的操作，确保有足够的CPU
2. buildx构建的基础镜像，即使本地有也要去重新拉取
3. buildx构建的镜像，本地不保存
