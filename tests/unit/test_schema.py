"""Validação de schema do dataset com pandera."""

import pandera.pandas as pa
import pytest

from src.data.loader import load_raw

RAW_SCHEMA = pa.DataFrameSchema(
    columns={
        "gender": pa.Column(str, pa.Check.isin(["Male", "Female"])),
        "SeniorCitizen": pa.Column(int, pa.Check.isin([0, 1])),
        "Partner": pa.Column(str, pa.Check.isin(["Yes", "No"])),
        "Dependents": pa.Column(str, pa.Check.isin(["Yes", "No"])),
        "tenure": pa.Column(int, pa.Check.ge(0)),
        "PhoneService": pa.Column(str, pa.Check.isin(["Yes", "No"])),
        "MultipleLines": pa.Column(str),
        "InternetService": pa.Column(str, pa.Check.isin(["DSL", "Fiber optic", "No"])),
        "OnlineSecurity": pa.Column(str),
        "OnlineBackup": pa.Column(str),
        "DeviceProtection": pa.Column(str),
        "TechSupport": pa.Column(str),
        "StreamingTV": pa.Column(str),
        "StreamingMovies": pa.Column(str),
        "Contract": pa.Column(str, pa.Check.isin(["Month-to-month", "One year", "Two year"])),
        "PaperlessBilling": pa.Column(str, pa.Check.isin(["Yes", "No"])),
        "PaymentMethod": pa.Column(str),
        "MonthlyCharges": pa.Column(float, pa.Check.ge(0)),
        "TotalCharges": pa.Column(float, pa.Check.ge(0)),
        "Churn": pa.Column(int, pa.Check.isin([0, 1])),
    },
    checks=[
        pa.Check(lambda df: len(df) >= 5000, error="Dataset deve ter >= 5000 registros"),
        pa.Check(lambda df: df.isnull().sum().sum() == 0, error="Sem nulos permitidos após load"),
    ],
    coerce=False,
)


@pytest.fixture(scope="module")
def raw_df():
    df, _ = load_raw()
    return df


def test_raw_schema_columns_present(raw_df):
    expected = set(RAW_SCHEMA.columns.keys())
    actual = set(raw_df.columns)
    missing = expected - actual
    assert not missing, f"Colunas ausentes: {missing}"


def test_raw_schema_types_and_values(raw_df):
    RAW_SCHEMA.validate(raw_df)


def test_churn_binary(raw_df):
    assert set(raw_df["Churn"].unique()).issubset({0, 1})


def test_tenure_non_negative(raw_df):
    assert (raw_df["tenure"] >= 0).all()


def test_monthly_charges_positive(raw_df):
    assert (raw_df["MonthlyCharges"] > 0).all()


def test_dataset_min_size(raw_df):
    assert len(raw_df) >= 5000


def test_customer_count_in_expected_range(raw_df):
    # Dataset IBM Telco tem ~7043 registros
    assert 5000 <= len(raw_df) <= 10000
