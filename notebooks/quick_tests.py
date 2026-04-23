"""
Baselines — Telco Customer Churn (StratifiedKFold k=5)
=======================================================
  - DummyClassifier (most_frequent, stratified)
  - LogisticRegression (balanced)
  - DecisionTreeClassifier (balanced)
  - RandomForestClassifier (balanced)
"""

from pathlib import Path

import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier

RANDOM_SEED = 42
TARGET = "Churn"
N_SPLITS = 5
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ── 1. Carregar ──────────────────────────────────────────────────────────────
DATA_PATH = PROJECT_ROOT / "data" / "raw" / "WA_Fn-UseC_-Telco-Customer-Churn.csv"
df = pd.read_csv(DATA_PATH)

# ── 2. Limpeza mínima ───────────────────────────────────────────────────────
df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
df[TARGET] = df[TARGET].map({"Yes": 1, "No": 0})
df = df.drop(columns=["customerID"])

X = df.drop(columns=[TARGET])
y = df[TARGET]

print(f"Dataset: {X.shape[0]} amostras | {X.shape[1]} features")
print(f"Churn: {y.mean():.3f} ({y.sum()}/{len(y)})\n")

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

# ── 4. Preprocessor ─────────────────────────────────────────────────────────
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

# ── 5. Definir modelos ──────────────────────────────────────────────────────
models = {
    "dummy_most_frequent": DummyClassifier(strategy="most_frequent", random_state=RANDOM_SEED),
    "dummy_stratified": DummyClassifier(strategy="stratified", random_state=RANDOM_SEED),
    "logistic_regression": Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", LogisticRegression(
            max_iter=1000, random_state=RANDOM_SEED, class_weight="balanced",
        )),
    ]),
    "decision_tree": Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", DecisionTreeClassifier(
            class_weight="balanced", random_state=RANDOM_SEED,
        )),
    ]),
    "random_forest": Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", RandomForestClassifier(
            n_estimators=100, class_weight="balanced", random_state=RANDOM_SEED,
        )),
    ]),
}

# ── 6. Validação cruzada (StratifiedKFold k=5) + MLflow ─────────────────────
skf = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=RANDOM_SEED)

mlflow.set_tracking_uri(f"sqlite:///{PROJECT_ROOT / 'mlflow.db'}")
mlflow.set_experiment("churn-baselines")

processed_path = PROJECT_ROOT / "data" / "processed" / "telco_churn_cleaned.csv"
df.to_csv(processed_path, index=False)

all_results = {}

for name, model in models.items():
    print("=" * 60)
    print(f"{name}  (StratifiedKFold k={N_SPLITS})")
    print("=" * 60)

    fold_metrics = {k: [] for k in ["accuracy", "roc_auc", "recall", "precision", "f1"]}

    for fold, (train_idx, val_idx) in enumerate(skf.split(X, y)):
        X_tr, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_tr, y_val = y.iloc[train_idx], y.iloc[val_idx]

        m = clone(model)
        m.fit(X_tr, y_tr)

        y_pred = m.predict(X_val)
        y_prob = m.predict_proba(X_val)[:, 1]

        fold_metrics["accuracy"].append(accuracy_score(y_val, y_pred))
        fold_metrics["roc_auc"].append(roc_auc_score(y_val, y_prob))
        fold_metrics["recall"].append(recall_score(y_val, y_pred, zero_division=0))
        fold_metrics["precision"].append(precision_score(y_val, y_pred, zero_division=0))
        fold_metrics["f1"].append(f1_score(y_val, y_pred, zero_division=0))

    means = {k: float(np.mean(v)) for k, v in fold_metrics.items()}
    stds = {k: float(np.std(v)) for k, v in fold_metrics.items()}
    all_results[name] = {**means, **{f"{k}_std": v for k, v in stds.items()}}

    for metric in ["accuracy", "roc_auc", "recall", "precision", "f1"]:
        print(f"  {metric:12s}: {means[metric]:.4f} +/- {stds[metric]:.4f}")

    with mlflow.start_run(run_name=name):
        mlflow.log_params({
            "model": name,
            "random_seed": RANDOM_SEED,
            "cv_folds": N_SPLITS,
        })
        mlflow.log_metrics(means)
        mlflow.log_metrics({f"{k}_std": v for k, v in stds.items()})
        final_model = clone(model).fit(X, y)
        mlflow.sklearn.log_model(final_model, "model")
        if name == "logistic_regression":
            mlflow.log_artifact(str(processed_path), artifact_path="data")
        print(f"  MLflow run: {mlflow.active_run().info.run_id}")
    print()

# ── 7. Tabela comparativa ───────────────────────────────────────────────────
print("=" * 60)
print("COMPARATIVO (média ± std)")
print("=" * 60)
header = f"{'Modelo':<25s} {'Accuracy':>10s} {'ROC AUC':>10s} {'Recall':>10s} {'Precision':>10s} {'F1':>10s}"
print(header)
print("-" * len(header))
for name, r in all_results.items():
    print(
        f"{name:<25s} "
        f"{r['accuracy']:.4f}±{r['accuracy_std']:.3f} "
        f"{r['roc_auc']:.4f}±{r['roc_auc_std']:.3f} "
        f"{r['recall']:.4f}±{r['recall_std']:.3f} "
        f"{r['precision']:.4f}±{r['precision_std']:.3f} "
        f"{r['f1']:.4f}±{r['f1_std']:.3f}"
    )
