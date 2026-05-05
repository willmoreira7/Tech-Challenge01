import hashlib
from pathlib import Path

import pandas as pd
import structlog

log = structlog.get_logger()

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RAW_PATH = _PROJECT_ROOT / "data" / "raw" / "WA_Fn-UseC_-Telco-Customer-Churn.csv"

try:
    import pandera as pa
    from pandera import Check, Column
    PANDERA_AVAILABLE = True
except Exception:
    pa = None
    Column = None
    Check = None
    PANDERA_AVAILABLE = False

def load_raw(path: Path | str = RAW_PATH) -> tuple[pd.DataFrame, str]:
    """Carrega, limpa e retorna o dataset + hash MD5 do conteúdo."""
    df = pd.read_csv(path)
    log.info("data.loaded", path=str(path), shape=df.shape)

    df = _fix_total_charges(df)
    df = _encode_target(df)
    df = df.drop(columns=["customerID"])
    # validate schema if pandera is available
    if PANDERA_AVAILABLE:
        df = _validate_df_pandera(df)
    dataset_hash = _compute_hash(df)
    log.info("data.ready", shape=df.shape, hash=dataset_hash)
    return df, dataset_hash


def _fix_total_charges(df: pd.DataFrame) -> pd.DataFrame:
    blanks = int((df["TotalCharges"].str.strip() == "").sum())
    df = df.copy()
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"].str.strip(), errors="coerce")
    median_tc = float(df["TotalCharges"].median())
    df["TotalCharges"] = df["TotalCharges"].fillna(median_tc)
    log.info("data.total_charges_fixed", blanks=blanks, imputed_with=round(median_tc, 2))
    return df


def _encode_target(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Churn"] = df["Churn"].map({"Yes": 1, "No": 0})
    return df


def _compute_hash(df: pd.DataFrame) -> str:
    raw = pd.util.hash_pandas_object(df, index=True).values.tobytes()
    return hashlib.md5(raw).hexdigest()


def _validate_df_pandera(df: pd.DataFrame) -> pd.DataFrame:
    """Validate the dataframe structure and basic checks using Pandera.

    This validation is lightweight and focuses on types and simple bounds
    so it won't be overly strict while still catching common data problems.
    """
    if not PANDERA_AVAILABLE:
        log.debug("pandera.not_available", message="Skipping dataframe validation")
        return df

    schema = pa.DataFrameSchema(
        {
            "gender": Column(pa.String, Check.isin(["Male", "Female"])),
            "SeniorCitizen": Column(pa.Int, Check.isin([0, 1])),
            "Partner": Column(pa.String, Check.isin(["Yes", "No"])),
            "Dependents": Column(pa.String, Check.isin(["Yes", "No"])),
            "tenure": Column(pa.Int, Check.ge(0)),
            "PhoneService": Column(pa.String, Check.isin(["Yes", "No"])),
            "MultipleLines": Column(pa.String),
            "InternetService": Column(pa.String),
            "OnlineSecurity": Column(pa.String),
            "OnlineBackup": Column(pa.String),
            "DeviceProtection": Column(pa.String),
            "TechSupport": Column(pa.String),
            "StreamingTV": Column(pa.String),
            "StreamingMovies": Column(pa.String),
            "Contract": Column(pa.String),
            "PaperlessBilling": Column(pa.String, Check.isin(["Yes", "No"])),
            "PaymentMethod": Column(pa.String),
            "MonthlyCharges": Column(pa.Float, Check.ge(0)),
            "TotalCharges": Column(pa.Float, Check.ge(0)),
            "Churn": Column(pa.Int, Check.isin([0, 1])),
        },
        coerce=True,
    )

    try:
        validated = schema.validate(df, lazy=True)
        log.info("data.validated", shape=validated.shape)
        return validated
    except pa.errors.SchemaErrors as e:
        # Log details and re-raise so CI or pipeline can catch the issue
        log.error("data.validation_failed", errors=str(e))
        raise
