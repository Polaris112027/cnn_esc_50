# 使用 Python 3.9
FROM python:3.10.10-slim

# 设置工作目录
WORKDIR /app

# 复制 CNN-ECS-50 文件夹到容器中
COPY . /app

# 更新 pip
RUN pip install --upgrade pip

# 安装依赖
RUN pip install --no-cache-dir -r /app/requirements.txt

EXPOSE 8000

# 设置容器启动命令
CMD ["python", "/app/Fastapi_with_registration.py"]
