import pandas as pd
import pytest

from src.data import loader


def _make_valid_df():
    # Minimal valid dataframe matching the schema in loader._validate_df_pandera
    data = {
        "gender": ["Male", "Female"],
        "SeniorCitizen": [0, 1],
        "Partner": ["Yes", "No"],
        "Dependents": ["No", "Yes"],
        "tenure": [10, 20],
        "PhoneService": ["Yes", "No"],
        "MultipleLines": ["No", "No phone service"],
        "InternetService": ["DSL", "Fiber optic"],
        "OnlineSecurity": ["Yes", "No"],
        "OnlineBackup": ["No", "Yes"],
        "DeviceProtection": ["No", "Yes"],
        "TechSupport": ["No", "Yes"],
        "StreamingTV": ["No", "Yes"],\
        "StreamingMovies": ["No", "Yes"],
        "Contract": ["Month-to-month", "One year"],
        "PaperlessBilling": ["Yes", "No"],
        "PaymentMethod": ["Electronic check", "Mailed check"],
        "MonthlyCharges": [29.85, 56.95],
        "TotalCharges": [29.85, 1889.50],
        "Churn": [0, 1],
    }
    return pd.DataFrame(data)


def test_validate_df_pandera_success():
    pytest.importorskip("pandas")
    pytest.importorskip("pandera")

    df = _make_valid_df()

    # Should not raise and should return a dataframe with same shape
    validated = loader._validate_df_pandera(df)
    assert validated.shape == df.shape


def test_validate_df_pandera_failure():
    pa = pytest.importorskip("pandera")

    df = _make_valid_df()
    # Introduce an invalid value for Churn (allowed are 0 or 1)
    df.loc[0, "Churn"] = 2

    with pytest.raises(pa.errors.SchemaErrors):
        loader._validate_df_pandera(df)
