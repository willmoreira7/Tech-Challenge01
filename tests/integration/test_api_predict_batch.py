"""Testes para endpoint POST /api/v1/predict_batch."""

import pytest


class TestPredictBatch:
    """Testes para rota POST /api/v1/predict_batch."""

    def test_predict_batch_valid_payload(self, client, valid_batch_payload):
        """POST /api/v1/predict_batch com payload válido retorna 200."""
        response = client.post("/api/v1/predict_batch", json=valid_batch_payload)
        assert response.status_code == 200

        data = response.json()
        assert "batch_id" in data
        assert "predictions" in data
        assert "model_version" in data
        assert "total_records" in data
        assert "processing_time_ms" in data

    def test_predict_batch_returns_all_predictions(self, client, valid_batch_payload):
        """POST /api/v1/predict_batch retorna todas as predições."""
        response = client.post("/api/v1/predict_batch", json=valid_batch_payload)
        data = response.json()

        num_records = len(valid_batch_payload["records"])
        assert len(data["predictions"]) == num_records
        assert data["total_records"] == num_records

    def test_predict_batch_record_index_matches(self, client, valid_batch_payload):
        """Índices dos records correspondem aos originais."""
        response = client.post("/api/v1/predict_batch", json=valid_batch_payload)
        data = response.json()

        for i, pred in enumerate(data["predictions"]):
            assert pred["record_index"] == i

    def test_predict_batch_predictions_valid_range(self, client, valid_batch_payload):
        """Todas as probabilidades estão entre 0 e 1."""
        response = client.post("/api/v1/predict_batch", json=valid_batch_payload)
        data = response.json()

        for pred in data["predictions"]:
            assert 0 <= pred["churn_probability"] <= 1
            assert isinstance(pred["churn_predicted"], bool)

    def test_predict_batch_single_record(self, client, valid_predict_payload):
        """POST /api/v1/predict_batch com 1 record retorna 200."""
        payload = {"records": [valid_predict_payload]}
        response = client.post("/api/v1/predict_batch", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["total_records"] == 1

    def test_predict_batch_empty(self, client):
        """POST /api/v1/predict_batch com array vazio retorna 422."""
        payload = {"records": []}
        response = client.post("/api/v1/predict_batch", json=payload)
        assert response.status_code == 422

    def test_predict_batch_exceeds_limit(self, client, valid_predict_payload):
        """POST /api/v1/predict_batch com > 10k records retorna 422."""
        # Criar payload com 10001 records
        payload = {"records": [valid_predict_payload] * 10001}
        response = client.post("/api/v1/predict_batch", json=payload)
        assert response.status_code == 422

    def test_predict_batch_invalid_record(self, client, valid_predict_payload):
        """POST /api/v1/predict_batch com 1 record inválido retorna 422."""
        invalid_record = valid_predict_payload.copy()
        del invalid_record["tenure"]

        payload = {"records": [valid_predict_payload, invalid_record]}
        response = client.post("/api/v1/predict_batch", json=payload)
        assert response.status_code == 422

    def test_predict_batch_batch_id_format(self, client, valid_batch_payload):
        """batch_id segue o formato batch_YYYYMMDD_HHMMSS."""
        response = client.post("/api/v1/predict_batch", json=valid_batch_payload)
        data = response.json()

        batch_id = data["batch_id"]
        assert batch_id.startswith("batch_")
        # Verificar se contém timestamp
        parts = batch_id.split("_")
        assert len(parts) == 3  # batch, YYYYMMDD, HHMMSS

    def test_predict_batch_processing_time_positive(self, client, valid_batch_payload):
        """Tempo de processamento é positivo."""
        response = client.post("/api/v1/predict_batch", json=valid_batch_payload)
        data = response.json()

        assert data["processing_time_ms"] > 0

    def test_predict_batch_model_version(self, client, valid_batch_payload):
        """POST /api/v1/predict_batch retorna model_version correto."""
        response = client.post("/api/v1/predict_batch", json=valid_batch_payload)
        data = response.json()

        assert data["model_version"] == "1.0.0"
