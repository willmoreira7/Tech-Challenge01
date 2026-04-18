import numpy as np
import pandas as pd
import pytest

from src.data.loader import load_raw
from src.features.pipeline import build_pipeline, fit_transform, transform


@pytest.fixture(scope="module")
def data():
    df, _ = load_raw()
    X = df.drop(columns=["Churn"])
    return X


@pytest.fixture(scope="module")
def fitted_pipeline(data):
    pipeline = build_pipeline()
    fit_transform(pipeline, data)
    return pipeline


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
