FROM python:3.11-slim

WORKDIR /workspace

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 启动 Linux RQ Worker
CMD ["python", "-m", "backend.app.workers.worker"]