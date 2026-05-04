"""Fixtures e configurações para testes da API."""

import time

import joblib
import pytest
import torch
from fastapi.testclient import TestClient

from src.api.app import create_app
from src.api.utils import load_model, load_pipeline


@pytest.fixture
def client():
    """Fixture para cliente HTTP de testes com rate limit desabilitado."""
    # Criar app de teste sem rate limiting para evitar acúmulo de requisições
    test_app = create_app(enable_rate_limit=False)

    # Carregar modelo e pipeline para testes
    try:
        test_app.state.model = load_model()
        test_app.state.pipeline = load_pipeline()
        test_app.state.start_time = time.time()
    except Exception as exc:
        # Se não conseguir carregar, criar mocks simples para testes
        print(f"Erro ao carregar modelo: {exc}")
        # Mock do modelo
        test_app.state.model = torch.nn.Linear(30, 1)
        test_app.state.model.eval()
        # Mock do pipeline
        test_app.state.pipeline = joblib.load("models/pipeline.pkl") if __name__ != "__main__" else None
        test_app.state.start_time = time.time()

    return TestClient(test_app)


@pytest.fixture
def client_with_rate_limit():
    """Fixture para cliente HTTP de testes com rate limit habilitado."""
    # Criar app de teste COM rate limiting para testar o rate limit
    test_app = create_app(enable_rate_limit=True)

    # Carregar modelo e pipeline para testes
    try:
        test_app.state.model = load_model()
        test_app.state.pipeline = load_pipeline()
        test_app.state.start_time = time.time()
    except Exception as exc:
        # Se não conseguir carregar, criar mocks simples para testes
        print(f"Erro ao carregar modelo: {exc}")
        # Mock do modelo
        test_app.state.model = torch.nn.Linear(30, 1)
        test_app.state.model.eval()
        # Mock do pipeline
        test_app.state.pipeline = joblib.load("models/pipeline.pkl") if __name__ != "__main__" else None
        test_app.state.start_time = time.time()

    return TestClient(test_app)


@pytest.fixture
def valid_predict_payload():
    """Fixture com payload válido para predição single."""
    return {
        "gender": "Male",
        "SeniorCitizen": 0,
        "Partner": "Yes",
        "Dependents": "No",
        "tenure": 12,
        "PhoneService": "Yes",
        "MultipleLines": "No phone service",
        "InternetService": "Fiber optic",
        "OnlineSecurity": "No",
        "OnlineBackup": "No",
        "DeviceProtection": "No",
        "TechSupport": "No",
        "StreamingTV": "No",
        "StreamingMovies": "No",
        "Contract": "Month-to-month",
        "PaperlessBilling": "Yes",
        "PaymentMethod": "Electronic check",
        "MonthlyCharges": 70.35,
        "TotalCharges": 844.20,
    }


@pytest.fixture
def valid_batch_payload(valid_predict_payload):
    """Fixture com payload válido para predição batch."""
    return {
        "records": [
            valid_predict_payload,
            {
                "gender": "Female",
                "SeniorCitizen": 1,
                "Partner": "No",
                "Dependents": "Yes",
                "tenure": 24,
                "PhoneService": "No",
                "MultipleLines": "No phone service",
                "InternetService": "DSL",
                "OnlineSecurity": "Yes",
                "OnlineBackup": "Yes",
                "DeviceProtection": "Yes",
                "TechSupport": "Yes",
                "StreamingTV": "Yes",
                "StreamingMovies": "Yes",
                "Contract": "Two year",
                "PaperlessBilling": "No",
                "PaymentMethod": "Automatic bank transfer",
                "MonthlyCharges": 85.50,
                "TotalCharges": 2050.00,
            },
        ]
    }
