from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import structlog
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import (
    FunctionTransformer,
    OneHotEncoder,
    OrdinalEncoder,
    StandardScaler,
)

log = structlog.get_logger()

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_DEFAULT_PIPELINE_PATH = _PROJECT_ROOT / "models" / "pipeline.pkl"

# ---------------------------------------------------------------------------
# Feature engineering constants
# ---------------------------------------------------------------------------
_ADD_ON_COLS = [
    "OnlineSecurity",
    "OnlineBackup",
    "DeviceProtection",
    "TechSupport",
    "StreamingTV",
    "StreamingMovies",
]

_DROP_COLS = [
    "gender", "PhoneService", "MultipleLines", "TotalCharges",
    "StreamingTV", "StreamingMovies",
]

# ---------------------------------------------------------------------------
# Column lists (post-engineering)
# ---------------------------------------------------------------------------
NUM_COLS = ["log_tenure", "MonthlyCharges", "SeniorCitizen", "n_add_on_services"]
BIN_COLS = ["Partner", "Dependents", "PaperlessBilling", "is_fiber"]
CAT_COLS = [
    "InternetService",
    "OnlineSecurity",
    "OnlineBackup",
    "DeviceProtection",
    "TechSupport",
    "Contract",
    "PaymentMethod",
]

_BIN_CATEGORIES = [
    ["No", "Yes"],  # Partner
    ["No", "Yes"],  # Dependents
    ["No", "Yes"],  # PaperlessBilling
    [0, 1],         # is_fiber (int after engineering)
]


# ---------------------------------------------------------------------------
# Feature engineering function
# ---------------------------------------------------------------------------
def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create derived features and drop low-signal columns.

    Receives the cleaned DataFrame (post-loader) and returns a
    DataFrame ready for the ColumnTransformer.
    """
    df = df.copy()

    df["log_tenure"] = np.log1p(df["tenure"])
    df = df.drop(columns=["tenure"])

    df["is_fiber"] = (df["InternetService"] == "Fiber optic").astype(int)

    df["n_add_on_services"] = sum(
        (df[col] == "Yes").astype(int) for col in _ADD_ON_COLS
    )

    df = df.drop(columns=[c for c in _DROP_COLS if c in df.columns])

    log.info(
        "features.engineered",
        shape=df.shape,
        new_cols=["log_tenure", "is_fiber", "n_add_on_services"],
        dropped=_DROP_COLS,
    )
    return df


# ---------------------------------------------------------------------------
# Pipeline builder
# ---------------------------------------------------------------------------
def build_pipeline() -> Pipeline:
    feature_eng = FunctionTransformer(engineer_features, validate=False)
    num_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])
    bin_pipeline = Pipeline([
        ("encoder", OrdinalEncoder(categories=_BIN_CATEGORIES)),
    ])
    cat_pipeline = Pipeline([
        ("encoder", OneHotEncoder(
            drop="if_binary", sparse_output=False, handle_unknown="ignore",
        )),
    ])
    preprocessor = ColumnTransformer([
        ("num", num_pipeline, NUM_COLS),
        ("bin", bin_pipeline, BIN_COLS),
        ("cat", cat_pipeline, CAT_COLS),
    ])
    return Pipeline([
        ("feature_eng", feature_eng),
        ("preprocessor", preprocessor),
    ])


def fit_transform(pipeline: Pipeline, X_train: pd.DataFrame) -> np.ndarray:
    result = pipeline.fit_transform(X_train)
    log.info("pipeline.fit_transform", output_shape=result.shape)
    return result


def transform(pipeline: Pipeline, X: pd.DataFrame) -> np.ndarray:
    return pipeline.transform(X)


def save_pipeline(pipeline: Pipeline, path: Path | str | None = None) -> None:
    dest = Path(path) if path else _DEFAULT_PIPELINE_PATH
    joblib.dump(pipeline, dest)
    log.info("pipeline.saved", path=str(dest))


def load_pipeline(path: Path | str | None = None) -> Pipeline:
    src_path = Path(path) if path else _DEFAULT_PIPELINE_PATH
    pipeline = joblib.load(src_path)
    log.info("pipeline.loaded", path=str(src_path))
    return pipeline
