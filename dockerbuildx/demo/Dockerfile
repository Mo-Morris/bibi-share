# 使用轻量级官方镜像
FROM python:3.10-slim

# 设置时区为亚洲时区（可选）
ENV TZ=Asia/Shanghai

# 创建工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 默认使用 Uvicorn 启动 FastAPI 服务
# 监听 0.0.0.0:8000，容器外部可访问
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]