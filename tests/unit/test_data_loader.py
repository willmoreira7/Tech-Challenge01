import pandas as pd
import pytest

from src.data.loader import _encode_target, _fix_total_charges, load_raw


@pytest.fixture
def raw_df():
    df, _ = load_raw()
    return df


def test_load_returns_dataframe(raw_df):
    assert isinstance(raw_df, pd.DataFrame)
    assert len(raw_df) > 0


def test_load_drops_customer_id(raw_df):
    assert "customerID" not in raw_df.columns


def test_churn_encoded_as_int(raw_df):
    assert raw_df["Churn"].dtype in (int, "int64", "int32")
    assert set(raw_df["Churn"].unique()).issubset({0, 1})


def test_total_charges_coercion():
    df = pd.DataFrame({
        "customerID": ["A", "B"],
        "TotalCharges": [" ", "100.5"],
        "Churn": ["No", "Yes"],
    })
    fixed = _fix_total_charges(df)
    assert fixed["TotalCharges"].isnull().sum() == 0
    assert fixed["TotalCharges"].dtype == float


def test_no_nulls_after_load(raw_df):
    assert raw_df.isnull().sum().sum() == 0


def test_dataset_hash_is_deterministic():
    _, h1 = load_raw()
    _, h2 = load_raw()
    assert h1 == h2
