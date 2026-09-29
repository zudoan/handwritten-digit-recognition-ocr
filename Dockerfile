# ====================================================================
# Dockerfile for NeuralVision Studio (FastAPI + TensorFlow CPU/GPU)
# ====================================================================

FROM python:3.11-slim

# Thiết lập biến môi trường
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    TF_ENABLE_ONEDNN_OPTS=0

# Cài đặt các thư viện hệ thống cần thiết cho OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Sao chép và cài đặt các thư viện phụ thuộc
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Sao chép toàn bộ mã nguồn ứng dụng
COPY . .

# Mở cổng 8080
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/api/health || exit 1

# Lệnh khởi chạy
CMD ["python", "run_server.py", "--host", "0.0.0.0", "--port", "8080", "--no-browser"]
