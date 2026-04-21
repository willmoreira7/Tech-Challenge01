"""
Baseline de Regressão Logística — Telco Customer Churn
======================================================
Fluxo didático:
  1. Carregar e inspecionar
  2. Limpeza mínima (TotalCharges, drop customerID, encode target)
  3. Separar features por tipo (numéricas, binárias, categóricas)
  4. train_test_split estratificado (80/20)
  5. Pipeline sklearn (preprocessor + modelo) — sem data leakage
  6. Treinar e avaliar (accuracy, precision, recall, f1, roc_auc)
  7. Matriz de confusão
  8. Persistir dataframe processado e registrar modelo no MLflow
"""

from pathlib import Path

import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
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
print(f"Shape original: {df.shape}")
print(f"Colunas: {list(df.columns)}\n")

# ── 2. Limpeza mínima ───────────────────────────────────────────────────────
df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
n_missing = df["TotalCharges"].isna().sum()
print(f"TotalCharges com valores vazios convertidos a NaN: {n_missing}")

df[TARGET] = df[TARGET].map({"Yes": 1, "No": 0})
df = df.drop(columns=["customerID"])

print(f"Shape após limpeza: {df.shape}")
print(f"Distribuição do target:\n{df[TARGET].value_counts(normalize=True).to_string()}\n")

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

# ── 4. Split estratificado ───────────────────────────────────────────────────
X = df.drop(columns=[TARGET])
y = df[TARGET]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=TEST_SIZE, random_state=RANDOM_SEED, stratify=y,
)
print(f"Treino: {X_train.shape[0]} amostras | Teste: {X_test.shape[0]} amostras")
print(f"Proporção churn treino: {y_train.mean():.3f}")
print(f"Proporção churn teste:  {y_test.mean():.3f}\n")

# ── 5. Pipeline (preprocessor + modelo) ─────────────────────────────────────
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

pipe = Pipeline([
    ("preprocessor", preprocessor),
    ("classifier", LogisticRegression(
        max_iter=1000,
        random_state=RANDOM_SEED,
        class_weight="balanced",
    )),
])

# ── 6. Treinar e avaliar ────────────────────────────────────────────────────
pipe.fit(X_train, y_train)

y_pred = pipe.predict(X_test)
y_prob = pipe.predict_proba(X_test)[:, 1]

print("=" * 60)
print("RESULTADOS — Regressão Logística (baseline)")
print("=" * 60)

print(f"\nAccuracy:  {accuracy_score(y_test, y_pred):.4f}")
print(f"ROC AUC:   {roc_auc_score(y_test, y_prob):.4f}")

print(f"\nClassification Report:\n{classification_report(y_test, y_pred, target_names=['No Churn', 'Churn'])}")

# ── 7. Matriz de confusão ───────────────────────────────────────────────────
cm = confusion_matrix(y_test, y_pred)
print("Matriz de Confusão:")
print(f"  TN={cm[0,0]:4d}  FP={cm[0,1]:4d}")
print(f"  FN={cm[1,0]:4d}  TP={cm[1,1]:4d}")

recall = cm[1, 1] / (cm[1, 0] + cm[1, 1])
precision = cm[1, 1] / (cm[0, 1] + cm[1, 1])
print(f"\nRecall (sensibilidade):  {recall:.4f}")
print(f"Precision:               {precision:.4f}")

# ── 8. Persistir dataframe processado ────────────────────────────────────────
processed_path = PROJECT_ROOT / "data" / "processed" / "telco_churn_cleaned.csv"
df.to_csv(processed_path, index=False)
print(f"\nDataframe processado salvo em: {processed_path}")

# ── 9. Registrar modelo no MLflow ────────────────────────────────────────────
mlflow.set_tracking_uri(f"sqlite:///{PROJECT_ROOT / 'mlflow.db'}")
mlflow.set_experiment("churn-baselines")

metrics = {
    "accuracy": accuracy_score(y_test, y_pred),
    "roc_auc": roc_auc_score(y_test, y_prob),
    "recall": recall,
    "precision": precision,
}

with mlflow.start_run(run_name="logistic_regression_baseline"):
    mlflow.log_params({
        "model": "LogisticRegression",
        "class_weight": "balanced",
        "max_iter": 1000,
        "random_seed": RANDOM_SEED,
        "test_size": TEST_SIZE,
    })
    mlflow.log_metrics(metrics)
    mlflow.sklearn.log_model(pipe, "model")
    mlflow.log_artifact(str(processed_path), artifact_path="data")
    print(f"Run MLflow registrado: {mlflow.active_run().info.run_id}")
