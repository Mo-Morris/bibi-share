

## 创建证书

```shell
mkdir -p certs
openssl req -x509 -nodes -newkey rsa:2048 -days 365 \
  -keyout certs/privkey.pem \
  -out certs/fullchain.pem \
  -subj "/CN=localhost"

```

## 添加nginx服务(nginx.conf在该目录下)

```yaml
  ....
  nginx:
    image: nginx:1.27-alpine
    container_name: openclaw-proxy-nginx
    restart: unless-stopped
    ports:
      - "8080:80"
      - "8443:443"
    depends_on:
      - openclaw-gateway
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - ./certs:/etc/nginx/certs:ro

```