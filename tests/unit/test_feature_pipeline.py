import numpy as np
import pandas as pd
import pytest

from src.data.loader import load_raw
from src.features.pipeline import (
    build_pipeline,
    engineer_features,
    fit_transform,
    transform,
)


@pytest.fixture(scope="module")
def data():
    df, _ = load_raw()
    X = df.drop(columns=["Churn"])
    return X


@pytest.fixture(scope="module")
def engineered_data(data):
    return engineer_features(data)


@pytest.fixture(scope="module")
def fitted_pipeline(data):
    pipeline = build_pipeline()
    fit_transform(pipeline, data)
    return pipeline


# ---- Pipeline integration tests ----


def test_pipeline_fit_transform_shape(data):
    pipeline = build_pipeline()
    result = fit_transform(pipeline, data)
    assert result.shape[0] == len(data)
    assert result.shape[1] > 0


def test_pipeline_no_nan_output(data):
    pipeline = build_pipeline()
    result = fit_transform(pipeline, data)
    assert not np.isnan(result).any()


def test_pipeline_deterministic(data):
    p1 = build_pipeline()
    p2 = build_pipeline()
    r1 = fit_transform(p1, data)
    r2 = fit_transform(p2, data)
    np.testing.assert_array_almost_equal(r1, r2)


def test_unknown_category_handled(data, fitted_pipeline):
    row = data.iloc[[0]].copy()
    row["InternetService"] = "UnknownProvider"
    result = transform(fitted_pipeline, row)
    assert not np.isnan(result).any()


# ---- Feature engineering unit tests ----


def test_engineer_features_creates_expected_columns(engineered_data):
    expected_present = ["log_tenure", "is_fiber", "n_add_on_services"]
    expected_absent = [
        "gender", "PhoneService", "MultipleLines", "TotalCharges", "tenure",
        "StreamingTV", "StreamingMovies",
    ]

    for col in expected_present:
        assert col in engineered_data.columns, f"Missing expected column: {col}"
    for col in expected_absent:
        assert col not in engineered_data.columns, f"Column should have been dropped: {col}"


def test_engineer_features_log_tenure_range(engineered_data):
    assert (engineered_data["log_tenure"] >= 0).all()


def test_engineer_features_n_add_on_range(engineered_data):
    assert (engineered_data["n_add_on_services"] >= 0).all()
    assert (engineered_data["n_add_on_services"] <= 6).all()
