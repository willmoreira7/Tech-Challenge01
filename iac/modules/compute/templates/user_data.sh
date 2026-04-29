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

# Allow ubuntu user to use Docker without sudo
usermod -aG docker ubuntu

# ---------------------------------------------------------------------------
# Project structure
# ---------------------------------------------------------------------------
PROJECT_DIR=/opt/mlflow-flask
mkdir -p "$PROJECT_DIR"/mlflow
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
    image: ghcr.io/mlflow/mlflow:latest
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
        --allowed-hosts "*"
        --cors-allowed-origins "*"
    networks:
      - app-net

  flask-app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: flask-app
    restart: unless-stopped
    ports:
      - "${flask_port}:8080"
    environment:
      - MLFLOW_TRACKING_URI=http://mlflow:5000
      - FLASK_ENV=production
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
# Starter Flask app
# ---------------------------------------------------------------------------
cat > "$PROJECT_DIR/app.py" <<'PYTHON'
import os
import mlflow
from flask import Flask, jsonify, request

app = Flask(__name__)

mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000"))
mlflow.set_experiment("flask-app")


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json(force=True)

    with mlflow.start_run():
        mlflow.log_params(data.get("params", {}))
        result = {"prediction": "replace with your model logic", "input": data}
        mlflow.log_metrics({"requests": 1})

    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
PYTHON

cat > "$PROJECT_DIR/requirements.txt" <<'REQ'
flask>=3.0
mlflow>=2.12
gunicorn>=21.0
REQ

cat > "$PROJECT_DIR/Dockerfile" <<'DOCKERFILE'
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "app:app"]
DOCKERFILE

chown -R ubuntu:ubuntu "$PROJECT_DIR"

# ---------------------------------------------------------------------------
# Sobe os containers agora (user_data roda como root — sem problema de grupo)
# ---------------------------------------------------------------------------
cd "$PROJECT_DIR"
docker compose up -d --build

# ---------------------------------------------------------------------------
# systemd service — garante que sobe novamente após reboot
# ---------------------------------------------------------------------------
cat > /etc/systemd/system/mlflow-flask.service <<SERVICE
[Unit]
Description=MLflow + Flask stack
After=docker.service network-online.target
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$PROJECT_DIR
ExecStart=/usr/bin/docker compose up -d --build
ExecStop=/usr/bin/docker compose down

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable mlflow-flask

echo "=== user_data finished ==="
