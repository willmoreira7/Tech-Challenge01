"""
Baselines — Telco Customer Churn
=================================
  - DummyClassifier (most_frequent, stratified)
  - LogisticRegression (balanced)
"""

from pathlib import Path

import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler

RANDOM_SEED = 42
TARGET = "Churn"
TEST_SIZE = 0.2
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ── 1. Carregar ──────────────────────────────────────────────────────────────
DATA_PATH = PROJECT_ROOT / "data" / "raw" / "WA_Fn-UseC_-Telco-Customer-Churn.csv"
df = pd.read_csv(DATA_PATH)

# ── 2. Limpeza mínima ───────────────────────────────────────────────────────
df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
df[TARGET] = df[TARGET].map({"Yes": 1, "No": 0})
df = df.drop(columns=["customerID"])

# ── 3. Definir colunas por tipo ──────────────────────────────────────────────
NUM_COLS = ["tenure", "MonthlyCharges", "TotalCharges", "SeniorCitizen"]
BIN_COLS = ["gender", "Partner", "Dependents", "PhoneService", "PaperlessBilling"]
BIN_CATEGORIES = [
    ["Female", "Male"],
    ["No", "Yes"],
    ["No", "Yes"],
    ["No", "Yes"],
    ["No", "Yes"],
]
CAT_COLS = [
    "MultipleLines", "InternetService", "OnlineSecurity", "OnlineBackup",
    "DeviceProtection", "TechSupport", "StreamingTV", "StreamingMovies",
    "Contract", "PaymentMethod",
]

# ── 4. Split estratificado ───────────────────────────────────────────────────
X = df.drop(columns=[TARGET])
y = df[TARGET]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=TEST_SIZE, random_state=RANDOM_SEED, stratify=y,
)
print(f"Treino: {X_train.shape[0]} | Teste: {X_test.shape[0]}")
print(f"Proporção churn: treino={y_train.mean():.3f}, teste={y_test.mean():.3f}\n")

# ── 5. Pipeline para Regressão Logística ─────────────────────────────────────
num_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler", StandardScaler()),
])

preprocessor = ColumnTransformer(
    transformers=[
        ("num", num_pipeline, NUM_COLS),
        ("bin", OrdinalEncoder(categories=BIN_CATEGORIES), BIN_COLS),
        ("cat", OneHotEncoder(drop="if_binary", sparse_output=False, handle_unknown="ignore"), CAT_COLS),
    ],
    remainder="drop",
)

lr_pipe = Pipeline([
    ("preprocessor", preprocessor),
    ("classifier", LogisticRegression(
        max_iter=1000, random_state=RANDOM_SEED, class_weight="balanced",
    )),
])

# ── 6. Definir modelos ──────────────────────────────────────────────────────
models = {
    "dummy_most_frequent": DummyClassifier(strategy="most_frequent", random_state=RANDOM_SEED),
    "dummy_stratified": DummyClassifier(strategy="stratified", random_state=RANDOM_SEED),
    "logistic_regression": lr_pipe,
}

# ── 7. Treinar, avaliar e registrar no MLflow ───────────────────────────────
mlflow.set_tracking_uri(f"sqlite:///{PROJECT_ROOT / 'mlflow.db'}")
mlflow.set_experiment("churn-baselines")

processed_path = PROJECT_ROOT / "data" / "processed" / "telco_churn_cleaned.csv"
df.to_csv(processed_path, index=False)

for name, model in models.items():
    print("=" * 60)
    print(name)
    print("=" * 60)

    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    acc = accuracy_score(y_test, y_pred)
    roc = roc_auc_score(y_test, y_prob)
    cm = confusion_matrix(y_test, y_pred)
    recall = cm[1, 1] / (cm[1, 0] + cm[1, 1]) if (cm[1, 0] + cm[1, 1]) > 0 else 0.0
    prec = cm[1, 1] / (cm[0, 1] + cm[1, 1]) if (cm[0, 1] + cm[1, 1]) > 0 else 0.0

    print(f"\nAccuracy:  {acc:.4f}")
    print(f"ROC AUC:   {roc:.4f}")
    print(f"\n{classification_report(y_test, y_pred, target_names=['No Churn', 'Churn'], zero_division=0)}")
    print(f"Matriz de Confusão:")
    print(f"  TN={cm[0,0]:4d}  FP={cm[0,1]:4d}")
    print(f"  FN={cm[1,0]:4d}  TP={cm[1,1]:4d}\n")

    metrics = {"accuracy": acc, "roc_auc": roc, "recall": recall, "precision": prec}

    with mlflow.start_run(run_name=name):
        mlflow.log_params({
            "model": name,
            "random_seed": RANDOM_SEED,
            "test_size": TEST_SIZE,
        })
        mlflow.log_metrics(metrics)
        mlflow.sklearn.log_model(model, "model")
        if name == "logistic_regression":
            mlflow.log_artifact(str(processed_path), artifact_path="data")
        print(f"MLflow run: {mlflow.active_run().info.run_id}")
    print()
