

## 启动命令
```shell
OPENCLAW_GATEWAY_BIND=loopback ./docker-setup.sh
```

## 跳过访问来源校验
```shell
docker compose -f docker-compose.yml run --rm openclaw-cli \
  config set gateway.controlUi.allowedOrigins '["*"]' --strict-json
```

# 跳过设备校验
```shell
docker compose -f docker-compose.yml run --rm openclaw-cli \
    config set gateway.controlUi.dangerouslyDisableDeviceAuth true
```

# 网关安全校验降级
```shell
docker compose -f docker-compose.yml run --rm openclaw-cli \
`config set gateway.controlUi.allowInsecureAuth true
```
