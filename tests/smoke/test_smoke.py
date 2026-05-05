"""Smoke tests: validações rápidas de import, dados e pipeline (sem modelo treinado)."""

from pathlib import Path

import numpy as np
import pytest


@pytest.mark.smoke
def test_critical_imports():
    """Pacotes e módulos principais importam sem erro."""
    import fastapi  # noqa: F401
    import pandas  # noqa: F401
    import torch  # noqa: F401

    from src.api.app import create_app  # noqa: F401
    from src.data.loader import load_raw  # noqa: F401
    from src.features.pipeline import build_pipeline, engineer_features  # noqa: F401


@pytest.mark.smoke
def test_raw_dataset_present():
    """Arquivo bruto esperado existe no repositório (CI checkout)."""
    root = Path(__file__).resolve().parents[2]
    csv_path = root / "data" / "raw" / "WA_Fn-UseC_-Telco-Customer-Churn.csv"
    assert csv_path.is_file(), f"Dataset ausente: {csv_path}"


@pytest.mark.smoke
def test_load_raw_smoke():
    """Loader produz DataFrame não vazio e hash estável por formato."""
    from src.data.loader import RAW_PATH, load_raw

    df, dataset_hash = load_raw(str(RAW_PATH))
    assert len(df) > 0
    assert len(dataset_hash) == 32
    assert "Churn" in df.columns


@pytest.mark.smoke
def test_engineer_features_smoke():
    """Feature engineering roda em amostra pequena."""
    from src.data.loader import RAW_PATH, load_raw
    from src.features.pipeline import engineer_features

    df, _ = load_raw(str(RAW_PATH))
    sample = df.drop(columns=["Churn"]).head(20)
    out = engineer_features(sample)
    assert "log_tenure" in out.columns
    assert "is_fiber" in out.columns
    assert "n_add_on_services" in out.columns
    assert "tenure" not in out.columns


@pytest.mark.smoke
def test_build_pipeline_fit_transform_smoke():
    """Pipeline sklearn fit+transform em subset (sanidade de colunas)."""
    from src.data.loader import RAW_PATH, load_raw
    from src.features.pipeline import build_pipeline

    df, _ = load_raw(str(RAW_PATH))
    X = df.drop(columns=["Churn"]).head(100)
    pipe = build_pipeline()
    X_out = pipe.fit_transform(X)
    assert isinstance(X_out, np.ndarray)
    assert X_out.shape[0] == 100
    assert X_out.shape[1] >= 1
    assert np.isfinite(X_out).all()


@pytest.mark.smoke
def test_create_app_factory():
    """Factory da API retorna instância FastAPI configurada."""
    from fastapi import FastAPI

    from src.api.app import create_app

    app = create_app(enable_rate_limit=False)
    assert isinstance(app, FastAPI)
    assert app.title == "Churn Prediction API"
