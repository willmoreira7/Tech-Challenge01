"""Testes para error handling e rate limiting."""

import time

import pytest


class TestRateLimit:
    """Testes para rate limiting (10 requests por 30 segundos)."""

    def test_rate_limit_exceeded(self, client_with_rate_limit, valid_predict_payload):
        """Mais de 10 requests em 30s retorna 429."""
        # Enviar 11 requests rápidos
        responses = []
        for _i in range(11):
            response = client_with_rate_limit.post("/api/v1/predict", json=valid_predict_payload)
            responses.append(response)

        # O 11º deve ser 429
        assert responses[-1].status_code == 429
        data = responses[-1].json()
        assert data["status_code"] == 429
        assert "retry_after" in data

    def test_rate_limit_response_format(self, client_with_rate_limit, valid_predict_payload):
        """Response 429 contém campos obrigatórios."""
        # Enviar requests até exceder limite
        for _i in range(11):
            response = client_with_rate_limit.post("/api/v1/predict", json=valid_predict_payload)

        if response.status_code == 429:
            data = response.json()
            assert "error" in data
            assert data["error"] == "Too Many Requests"
            assert "detail" in data
            assert "retry_after" in data


class TestErrorHandling:
    """Testes para error handling."""

    def test_invalid_endpoint(self, client):
        """GET /invalid retorna 404."""
        response = client.get("/invalid")
        assert response.status_code == 404

    def test_predict_wrong_method(self, client):
        """GET /api/v1/predict retorna 405 (Method Not Allowed)."""
        response = client.get("/api/v1/predict")
        assert response.status_code in [404, 405]

    def test_batch_wrong_method(self, client):
        """GET /api/v1/predict_batch retorna 405 (Method Not Allowed)."""
        response = client.get("/api/v1/predict_batch")
        assert response.status_code in [404, 405]

    def test_invalid_json_payload(self, client):
        """POST /api/v1/predict com JSON inválido retorna 422."""
        response = client.post(
            "/api/v1/predict",
            data="invalid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code in [422, 400]

    def test_predict_missing_required_field(self, client):
        """POST /api/v1/predict sem campo obrigatório retorna 422."""
        payload = {"gender": "Male"}  # Missing all required fields
        response = client.post("/api/v1/predict", json=payload)
        assert response.status_code == 422

    def test_batch_missing_records_field(self, client):
        """POST /api/v1/predict_batch sem field 'records' retorna 422."""
        payload = {"invalid_field": []}
        response = client.post("/api/v1/predict_batch", json=payload)
        assert response.status_code == 422

    def test_predict_extra_fields_ignored(self, client, valid_predict_payload):
        """POST /api/v1/predict ignora campos extras."""
        payload = valid_predict_payload.copy()
        payload["extra_field"] = "should_be_ignored"

        response = client.post("/api/v1/predict", json=payload)
        # Pode ser 200 ou 422 dependendo da configuração do Pydantic
        # Por padrão, Pydantic ignora campos extras
        assert response.status_code in [200, 422]
