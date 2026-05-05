#!/bin/bash
set -euo pipefail
exec > >(tee /var/log/user_data.log) 2>&1

# ---------------------------------------------------------------------------
# System packages
# ---------------------------------------------------------------------------
apt-get update -y
apt-get install -y \
  ca-certificates \
  curl \
  gnupg \
  lsb-release \
  python3 \
  python3-pip \
  python3-venv \
  git \
  htop \
  unzip

# ---------------------------------------------------------------------------
# Docker
# ---------------------------------------------------------------------------
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" \
  > /etc/apt/sources.list.d/docker.list

apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

systemctl enable docker
systemctl start docker

usermod -aG docker ubuntu

# ---------------------------------------------------------------------------
# Project structure
# ---------------------------------------------------------------------------
PROJECT_DIR=/opt/mlflow-fastapi
mkdir -p "$PROJECT_DIR"
chown -R ubuntu:ubuntu "$PROJECT_DIR"

# ---------------------------------------------------------------------------
# docker-compose.yml
# ---------------------------------------------------------------------------
ARTIFACT_STORE="${mlflow_artifact_bucket}"
if [ -n "$ARTIFACT_STORE" ]; then
  ARTIFACT_URI="s3://$ARTIFACT_STORE/mlflow-artifacts"
else
  ARTIFACT_URI="/mlflow/artifacts"
fi

cat > "$PROJECT_DIR/docker-compose.yml" <<COMPOSE
version: "3.9"

services:
  mlflow:
    image: ghcr.io/mlflow/mlflow:v2.19.0
    container_name: mlflow
    restart: unless-stopped
    ports:
      - "${mlflow_port}:5000"
    volumes:
      - mlflow_data:/mlflow
    environment:
      - AWS_DEFAULT_REGION=${aws_region}
    command: >
      mlflow server
        --host 0.0.0.0
        --port 5000
        --backend-store-uri sqlite:////mlflow/mlflow.db
        --default-artifact-root $ARTIFACT_URI
        --static-prefix /mlflow
        --allowed-hosts "*"
        --cors-allowed-origins "*"
    networks:
      - app-net

  fastapi:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: fastapi
    restart: unless-stopped
    ports:
      - "${flask_port}:8080"
    environment:
      - MLFLOW_TRACKING_URI=http://mlflow:5000/mlflow
      - MLFLOW_EXPERIMENT_NAME=churn-mlp
    depends_on:
      - mlflow
    networks:
      - app-net

volumes:
  mlflow_data:

networks:
  app-net:
    driver: bridge
COMPOSE

# ---------------------------------------------------------------------------
# Dockerfile e placeholder — substituídos pelo CI/CD no primeiro deploy
# ---------------------------------------------------------------------------
cat > "$PROJECT_DIR/Dockerfile" <<'DOCKERFILE'
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
COPY placeholder.py ./src/api/app.py
ENV PYTHONPATH=/app
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1
CMD ["python", "-m", "uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8080"]
DOCKERFILE

cat > "$PROJECT_DIR/placeholder.py" <<'PYTHON'
from fastapi import FastAPI
app = FastAPI()

@app.get("/health")
def health():
    return {"status": "starting", "detail": "aguardando deploy via CI/CD"}
PYTHON

# Cria diretórios que o CI/CD vai popular
mkdir -p "$PROJECT_DIR/src/api"
mkdir -p "$PROJECT_DIR/configs"

chown -R ubuntu:ubuntu "$PROJECT_DIR"

# ---------------------------------------------------------------------------
# Sobe MLflow agora; FastAPI sobe após o primeiro deploy do CI/CD
# ---------------------------------------------------------------------------
cd "$PROJECT_DIR"
docker compose up -d --build

# ---------------------------------------------------------------------------
# systemd service — reinicia stack após reboot
# ---------------------------------------------------------------------------
cat > /etc/systemd/system/mlflow-fastapi.service <<SERVICE
[Unit]
Description=MLflow + FastAPI stack
After=docker.service network-online.target
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$PROJECT_DIR
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable mlflow-fastapi

echo "=== user_data finished ==="
