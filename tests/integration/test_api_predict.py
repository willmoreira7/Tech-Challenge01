"""Testes para endpoint POST /api/v1/predict."""

import pytest


class TestPredict:
    """Testes para rota POST /api/v1/predict."""

    def test_predict_valid_payload(self, client, valid_predict_payload):
        """POST /api/v1/predict com payload válido retorna 200."""
        response = client.post("/api/v1/predict", json=valid_predict_payload)
        assert response.status_code == 200

        data = response.json()
        assert "churn_probability" in data
        assert "churn_predicted" in data
        assert "model_version" in data
        assert "processing_time_ms" in data

    def test_predict_returns_probability_in_range(self, client, valid_predict_payload):
        """Probabilidade de churn está entre 0 e 1."""
        response = client.post("/api/v1/predict", json=valid_predict_payload)
        data = response.json()

        assert 0 <= data["churn_probability"] <= 1

    def test_predict_returns_bool_prediction(self, client, valid_predict_payload):
        """Predição binária é boolean."""
        response = client.post("/api/v1/predict", json=valid_predict_payload)
        data = response.json()

        assert isinstance(data["churn_predicted"], bool)

    def test_predict_processing_time_positive(self, client, valid_predict_payload):
        """Tempo de processamento é positivo."""
        response = client.post("/api/v1/predict", json=valid_predict_payload)
        data = response.json()

        assert data["processing_time_ms"] > 0

    def test_predict_missing_field(self, client, valid_predict_payload):
        """POST /api/v1/predict sem campo obrigatório retorna 422."""
        invalid_payload = valid_predict_payload.copy()
        del invalid_payload["tenure"]

        response = client.post("/api/v1/predict", json=invalid_payload)
        assert response.status_code == 422

    def test_predict_invalid_type(self, client, valid_predict_payload):
        """POST /api/v1/predict com tipo inválido retorna 422."""
        invalid_payload = valid_predict_payload.copy()
        invalid_payload["tenure"] = "not_a_number"

        response = client.post("/api/v1/predict", json=invalid_payload)
        assert response.status_code == 422

    def test_predict_invalid_literal(self, client, valid_predict_payload):
        """POST /api/v1/predict com literal inválido retorna 422."""
        invalid_payload = valid_predict_payload.copy()
        invalid_payload["gender"] = "Invalid"

        response = client.post("/api/v1/predict", json=invalid_payload)
        assert response.status_code == 422

    def test_predict_negative_tenure(self, client, valid_predict_payload):
        """POST /api/v1/predict com tenure negativo retorna 422."""
        invalid_payload = valid_predict_payload.copy()
        invalid_payload["tenure"] = -1

        response = client.post("/api/v1/predict", json=invalid_payload)
        assert response.status_code == 422

    def test_predict_negative_charges(self, client, valid_predict_payload):
        """POST /api/v1/predict com charges negativo retorna 422."""
        invalid_payload = valid_predict_payload.copy()
        invalid_payload["MonthlyCharges"] = -10.0

        response = client.post("/api/v1/predict", json=invalid_payload)
        assert response.status_code == 422

    def test_predict_senior_citizen_invalid(self, client, valid_predict_payload):
        """POST /api/v1/predict com SeniorCitizen inválido retorna 422."""
        invalid_payload = valid_predict_payload.copy()
        invalid_payload["SeniorCitizen"] = 2  # Deve ser 0 ou 1

        response = client.post("/api/v1/predict", json=invalid_payload)
        assert response.status_code == 422

    def test_predict_model_version_correct(self, client, valid_predict_payload):
        """POST /api/v1/predict retorna model_version correto."""
        response = client.post("/api/v1/predict", json=valid_predict_payload)
        data = response.json()

        assert data["model_version"] == "1.0.0"
