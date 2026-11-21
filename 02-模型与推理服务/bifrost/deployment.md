# Bifrost 简单部署

本文只分两步：

1. 先用 Docker Compose 跑起来，把数据挂载到宿主机，并初始化管理员账号和密码。
2. 简单看一下 SQLite 和 PostgreSQL 的配置写法，不实际部署数据库。

## 第一步：先跑起来

创建目录：

```bash
mkdir -p bifrost/data
cd bifrost
```

目录结构：

```text
bifrost/
├── compose.yaml
├── .env
└── data/
    └── config.json
```

### compose.yaml

```yaml
services:
  bifrost:
    image: maximhq/bifrost:v1.6.2
    container_name: bifrost
    ports:
      - "8080:8080"
    environment:
      BIFROST_ADMIN_USERNAME: ${BIFROST_ADMIN_USERNAME}
      BIFROST_ADMIN_PASSWORD: ${BIFROST_ADMIN_PASSWORD}
    volumes:
      - ./data:/app/data
    restart: unless-stopped
```

`./data:/app/data` 会把 Bifrost 的配置库和日志库挂载到当前目录的 `data` 文件夹。

### .env

```dotenv
BIFROST_ADMIN_USERNAME=admin
BIFROST_ADMIN_PASSWORD=change-this-password
```

把示例密码换成自己的强密码。

可以这样生成随机密码：

```bash
openssl rand -base64 24
```

### data/config.json

```json
{
  "$schema": "https://www.getbifrost.ai/schema",
  "governance": {
    "auth_config": {
      "is_enabled": true,
      "admin_username": "env.BIFROST_ADMIN_USERNAME",
      "admin_password": "env.BIFROST_ADMIN_PASSWORD"
    }
  }
}
```

这个配置会：

- 初始化管理员账号和密码。
- 保护 Bifrost Web UI 和管理接口。
- 不预先添加模型、Provider API Key 或 Virtual Key。



### 启动

```bash
docker compose up -d
```

检查状态：

```bash
docker compose ps
curl http://127.0.0.1:8080/health
```

浏览器打开：

```text
http://服务器地址:8080
```

使用 `.env` 中的管理员账号和密码登录，然后在页面上依次操作：

1. 进入 `Providers`，添加 OpenAI、Anthropic 或其他模型供应商。
2. 填写供应商提供的 API Key，并选择允许使用的模型。
3. 进入 `Governance → Virtual Keys`，创建给调用方使用的 API Key。
4. 给 Virtual Key 选择允许访问的 Provider 和模型。
5. 进入安全设置，打开 `Enforce Virtual Keys on Inference`，要求推理请求必须携带 Virtual Key。

管理员账号密码只用于登录和管理；调用模型使用页面创建的 Virtual Key。

### 测试 API Key

把 `sk-bf-your-api-key` 替换成页面创建的 Virtual Key：

```bash
curl http://127.0.0.1:8080/v1/models \
  -H "Authorization: Bearer sk-bf-30bc90a6-32eb-4d8d-9417-e6f61c816ebc"
```

如果返回可用模型列表，说明 API Key 有效；如果返回 `401`，检查是否复制了完整的 Virtual Key。

### 流式调用模型

把 API Key 和模型名替换成页面中实际配置的值：

```bash
curl -N http://127.0.0.1:8080/v1/chat/completions \
  -H "Authorization: Bearer sk-bf-30bc90a6-32eb-4d8d-9417-e6f61c816ebc" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek/deepseek-v4-flash",
    "messages": [
      {
        "role": "user",
        "content": "请用一句话介绍你自己"
      }
    ],
    "stream": true
  }'
```

`-N` 会关闭 curl 的输出缓冲，让模型返回的内容实时显示在终端中。

运行后，数据会出现在：

```text
./data/config.db
./data/logs.db
```



## 第二步：SQLite 或 PostgreSQL 配置参考

如果以后实际使用下面的配置，需要把数据库字段合并进第一步的 `config.json`，不要覆盖掉第一步的 `governance` 管理员配置。

### 使用 SQLite

SQLite 最简单，适合单机部署。

配置结构如下：

```json
{
  "$schema": "https://www.getbifrost.ai/schema",
  "config_store": {
    "enabled": true,
    "type": "sqlite",
    "config": {
      "path": "/app/data/config.db"
    }
  },
  "logs_store": {
    "enabled": true,
    "type": "sqlite",
    "config": {
      "path": "/app/data/logs.db"
    }
  }
}
```

其中：

- `config.db` 保存 Provider、Virtual Key 等配置。
- `logs.db` 保存请求日志。

实际上即使不写这段，Bifrost 默认也会在 `/app/data` 中使用 SQLite。

### 使用 PostgreSQL

PostgreSQL 适合多实例或数据量较大的部署。

配置写法如下：

```json
{
  "$schema": "https://www.getbifrost.ai/schema",
  "config_store": {
    "enabled": true,
    "type": "postgres",
    "config": {
      "host": "env.PG_HOST",
      "port": "5432",
      "user": "env.PG_USER",
      "password": "env.PG_PASSWORD",
      "db_name": "bifrost",
      "ssl_mode": "disable"
    }
  },
  "logs_store": {
    "enabled": true,
    "type": "postgres",
    "config": {
      "host": "env.PG_HOST",
      "port": "5432",
      "user": "env.PG_USER",
      "password": "env.PG_PASSWORD",
      "db_name": "bifrost",
      "ssl_mode": "disable"
    }
  }
}
```

对应环境变量：

```dotenv
PG_HOST=postgres
PG_USER=bifrost
PG_PASSWORD=change-this-password
```

生产环境连接外部 PostgreSQL 时，建议根据数据库要求把 `ssl_mode` 改成 `require`。