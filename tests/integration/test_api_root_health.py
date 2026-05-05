"""Testes para root endpoint e health check."""

import pytest


class TestRoot:
    """Testes para rota GET /."""

    def test_root_returns_ok(self, client):
        """GET / retorna 200 com informações da API."""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert data["app"] == "Churn Prediction API"
        assert data["version"] == "1.0.0"
        assert "documentation" in data
        assert "endpoints" in data

    def test_root_has_all_fields(self, client):
        """GET / retorna todos os campos obrigatórios."""
        response = client.get("/")
        data = response.json()

        required_fields = ["app", "version", "description", "documentation", "endpoints"]
        for field in required_fields:
            assert field in data, f"Campo obrigatório ausente: {field}"

    def test_root_endpoints_info(self, client):
        """GET / contém informações de endpoints."""
        response = client.get("/")
        data = response.json()
        endpoints = data["endpoints"]

        assert "health" in endpoints
        assert "predict_single" in endpoints
        assert "predict_batch" in endpoints


class TestHealth:
    """Testes para rota GET /health."""

    def test_health_returns_ok(self, client):
        """GET /health retorna 200 com status healthy quando modelo está carregado."""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        # Status deve ser "healthy" se modelo e pipeline estão carregados
        assert data["status"] in ["healthy", "degraded"]

    def test_health_has_uptime(self, client):
        """GET /health contém uptime positivo."""
        response = client.get("/health")
        data = response.json()

        assert "uptime_seconds" in data
        assert data["uptime_seconds"] >= 0

    def test_health_has_model_version(self, client):
        """GET /health contém model_version e model_source."""
        response = client.get("/health")
        data = response.json()

        assert "model_version" in data
        assert data["model_version"] == "1.0.0"
        assert "model_source" in data
        assert data["model_source"] in ("mlflow_registry", "local_file", "unknown")

    def test_health_has_timestamp(self, client):
        """GET /health contém timestamp ISO 8601."""
        response = client.get("/health")
        data = response.json()

        assert "timestamp" in data
        # Verificar se é um timestamp válido (contém T e Z)
        assert "T" in data["timestamp"]
        assert "Z" in data["timestamp"]

    def test_health_status_healthy_with_loaded_model(self, client):
        """GET /health retorna status 'healthy' quando modelo está carregado."""
        response = client.get("/health")
        data = response.json()
        # Esperamos 'healthy' pois o client fixture já carrega o modelo
        assert data["status"] == "healthy"

    def test_health_status_degraded_without_model(self, client):
        """GET /health retorna status 'degraded' quando modelo não está carregado."""
        from src.api.app import create_app

        # Cria app sem carregar modelo
        app = create_app()
        from fastapi.testclient import TestClient
        test_client = TestClient(app)

        response = test_client.get("/health")
        data = response.json()
        # Esperamos 'degraded' pois modelo não foi carregado
        assert data["status"] == "degraded"
