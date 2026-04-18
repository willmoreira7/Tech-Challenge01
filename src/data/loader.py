import hashlib

import pandas as pd
import structlog

log = structlog.get_logger()

RANDOM_SEED = 42
RAW_PATH = "data/raw/dataset.csv"


def load_raw(path: str = RAW_PATH) -> tuple[pd.DataFrame, str]:
    """Carrega, limpa e retorna o dataset + hash MD5 do conteúdo."""
    df = pd.read_csv(path)
    log.info("data.loaded", path=path, shape=df.shape)

    df = _fix_total_charges(df)
    df = _encode_target(df)
    df = df.drop(columns=["customerID"])

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
