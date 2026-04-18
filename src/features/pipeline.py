import joblib
import numpy as np
import pandas as pd
import structlog
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler

log = structlog.get_logger()

NUM_COLS = ["tenure", "MonthlyCharges", "TotalCharges", "SeniorCitizen"]
BIN_COLS = ["gender", "Partner", "Dependents", "PhoneService", "PaperlessBilling"]
CAT_COLS = [
    "MultipleLines",
    "InternetService",
    "OnlineSecurity",
    "OnlineBackup",
    "DeviceProtection",
    "TechSupport",
    "StreamingTV",
    "StreamingMovies",
    "Contract",
    "PaymentMethod",
]

_BIN_CATEGORIES = [
    ["Female", "Male"],
    ["No", "Yes"],
    ["No", "Yes"],
    ["No", "Yes"],
    ["No", "Yes"],
]


def build_pipeline() -> Pipeline:
    num_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])
    bin_pipeline = Pipeline([
        ("encoder", OrdinalEncoder(categories=_BIN_CATEGORIES)),
    ])
    cat_pipeline = Pipeline([
        ("encoder", OneHotEncoder(drop="if_binary", sparse_output=False, handle_unknown="ignore")),
    ])
    preprocessor = ColumnTransformer([
        ("num", num_pipeline, NUM_COLS),
        ("bin", bin_pipeline, BIN_COLS),
        ("cat", cat_pipeline, CAT_COLS),
    ])
    return Pipeline([("preprocessor", preprocessor)])


def fit_transform(pipeline: Pipeline, X_train: pd.DataFrame) -> np.ndarray:
    result = pipeline.fit_transform(X_train)
    log.info("pipeline.fit_transform", output_shape=result.shape)
    return result


def transform(pipeline: Pipeline, X: pd.DataFrame) -> np.ndarray:
    return pipeline.transform(X)


def save_pipeline(pipeline: Pipeline, path: str = "models/pipeline.pkl") -> None:
    joblib.dump(pipeline, path)
    log.info("pipeline.saved", path=path)


def load_pipeline(path: str = "models/pipeline.pkl") -> Pipeline:
    pipeline = joblib.load(path)
    log.info("pipeline.loaded", path=path)
    return pipeline
