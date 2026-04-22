
拉取镜像[Dockerhub](https://hub.docker.com/r/nousresearch/hermes-agent/tags)最新镜像。
```shell
docker pull nousresearch/hermes-agent:v2026.4.16
```
创建配置文件目录
```shell
mkdir -p ~/.hermes
```
初始化，配置模型，聊天机器人等
```shell
docker run -it --rm \
  -v ~/.hermes:/opt/data \
  nousresearch/hermes-agent:v2026.4.16 setup
```
同步openclaw的配置(如果已经安装了openclaw)
```shell
# 查看迁移项
docker run -it --rm \
  -v ~/.hermes:/opt/data \
  -v ~/.openclaw:/opt/data/.openclaw \
  nousresearch/hermes-agent:v2026.4.16 claw migrate --dry-run
# 同步数据
docker run -it --rm \
  -v ~/.hermes:/opt/data \
  -v ~/.openclaw:/opt/data/.openclaw \
  nousresearch/hermes-agent:v2026.4.16 claw migrate --preset full
```

创建 docker 网络（只需执行一次）
```shell
docker network create hermes-net
```

启动 gateway（加入 hermes-net）
```shell
docker run -d \
  --name hermes \
  --restart unless-stopped \
  --network hermes-net \
  -v ~/.hermes:/opt/data \
  -p 8642:8642 \
  nousresearch/hermes-agent:v2026.4.16 gateway run
```

启动 dashboard（通过容器名访问 gateway）
```shell
docker run -d \
  --name hermes-dashboard \
  --restart unless-stopped \
  --network hermes-net \
  -v ~/.hermes:/opt/data \
  -p 9119:9119 \
  -e GATEWAY_HEALTH_URL=http://hermes:8642 \
  nousresearch/hermes-agent:v2026.4.16 dashboard --host 0.0.0.0 --insecure
```
> --insecure 表示该面板无强认证地暴露配置和密钥相关能力，不要直接暴露到公网。建议至少做一层保护：
仅本机访问（不对外网开放 9119）
或放到反向代理后，加 Basic Auth / SSO / IP 白名单

