"""Treina ChurnMLP com StratifiedKFold(5) e registra experimento no MLflow."""
import argparse
import os
import sys
from pathlib import Path

import mlflow
import numpy as np
import structlog
import torch
import torch.nn as nn
from dotenv import load_dotenv
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, train_test_split
from torch.utils.data import DataLoader, TensorDataset

from src.config import load_config
from src.data.loader import load_raw
from src.features.pipeline import (
    build_pipeline,
    fit_transform,
    save_pipeline,
    transform,
)
from src.models.mlp import ChurnMLP

load_dotenv()

RANDOM_SEED = 42
POS_WEIGHT = 2.7683
TEST_SIZE = 0.2
N_FOLDS = 5
MODELS_DIR = Path("models")
RECALL_TARGET = 0.75

log = structlog.get_logger()


def _seed_everything(seed: int) -> None:
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def _make_loader(X: np.ndarray, y: np.ndarray, batch_size: int, *, shuffle: bool) -> DataLoader:
    Xt = torch.tensor(X, dtype=torch.float32)
    yt = torch.tensor(y, dtype=torch.float32).unsqueeze(1)
    return DataLoader(TensorDataset(Xt, yt), batch_size=batch_size, shuffle=shuffle)


def _best_threshold(probs: np.ndarray, y_true: np.ndarray) -> tuple[float, float]:
    """Maximiza Expected Profit = TP×1140 − FP×60 − FN×1200."""
    best_profit, best_t = -np.inf, 0.5
    for t in np.arange(0.05, 0.95, 0.01):
        preds = (probs >= t).astype(int)
        tp = int(((preds == 1) & (y_true == 1)).sum())
        fp = int(((preds == 1) & (y_true == 0)).sum())
        fn = int(((preds == 0) & (y_true == 1)).sum())
        profit = tp * 1140 - fp * 60 - fn * 1200
        if profit > best_profit:
            best_profit, best_t = profit, t
    return float(best_t), float(best_profit)


def _eval_metrics(probs: np.ndarray, y_true: np.ndarray) -> dict:
    threshold, profit = _best_threshold(probs, y_true)
    preds = (probs >= threshold).astype(int)
    return {
        "roc_auc": float(roc_auc_score(y_true, probs)),
        "pr_auc": float(average_precision_score(y_true, probs)),
        "recall": float(recall_score(y_true, preds)),
        "precision": float(precision_score(y_true, preds, zero_division=0)),
        "f1": float(f1_score(y_true, preds, zero_division=0)),
        "accuracy": float(accuracy_score(y_true, preds)),
        "best_threshold": threshold,
        "expected_profit": profit,
    }


def _run_training_loop(
    X_train_np: np.ndarray,
    y_train: np.ndarray,
    X_val_np: np.ndarray,
    y_val: np.ndarray,
    cfg: dict,
    input_dim: int,
    device: torch.device,
) -> tuple[dict, dict]:
    """Treina o modelo em um split (fold ou final). Retorna (state_dict, métricas)."""
    hidden_dims: list[int] = cfg["model"]["hidden_dims"]
    dropout_rates: list[float] = cfg["model"]["dropout"]
    lr: float = cfg["training"]["learning_rate"]
    weight_decay: float = cfg["training"]["weight_decay"]
    batch_size: int = cfg["training"]["batch_size"]
    epochs: int = cfg["training"]["epochs"]
    es_patience: int = cfg["training"]["early_stopping_patience"]
    sched_patience: int = cfg["training"]["scheduler_patience"]

    model = ChurnMLP(input_dim, hidden_dims, dropout_rates).to(device)
    criterion = nn.BCEWithLogitsLoss(pos_weight=torch.tensor([POS_WEIGHT], device=device))
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=sched_patience)

    train_loader = _make_loader(X_train_np, y_train, batch_size, shuffle=True)
    X_val_t = torch.tensor(X_val_np, dtype=torch.float32).to(device)
    y_val_t = torch.tensor(y_val, dtype=torch.float32).unsqueeze(1).to(device)

    best_val_loss = float("inf")
    patience_counter = 0
    best_state: dict = {}

    for _epoch in range(1, epochs + 1):
        model.train()
        train_loss = 0.0
        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)
            optimizer.zero_grad()
            loss = criterion(model(xb), yb)
            loss.backward()
            optimizer.step()
            train_loss += loss.item() * xb.size(0)
        train_loss /= len(train_loader.dataset)

        model.eval()
        with torch.no_grad():
            val_loss = criterion(model(X_val_t), y_val_t).item()

        scheduler.step(val_loss)

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
        else:
            patience_counter += 1

        if patience_counter >= es_patience:
            break

    model.load_state_dict(best_state)
    model.eval()

    with torch.no_grad():
        probs = torch.sigmoid(model(X_val_t)).cpu().numpy().ravel()

    return best_state, _eval_metrics(probs, y_val)


def train(config_path: Path | None = None, run_name: str = "mlp_train") -> str:
    _seed_everything(RANDOM_SEED)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    cfg = load_config(config_path) if config_path else load_config()
    experiment = os.getenv("MLFLOW_EXPERIMENT_NAME", "churn-mlp")
    mlflow.set_experiment(experiment)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    log.info("train.start", device=str(device), experiment=experiment)

    # ── Dados ──────────────────────────────────────────────────────────────
    df, dataset_hash = load_raw()
    X = df.drop(columns=["Churn"])
    y = df["Churn"].values

    # Hold-out test set — não entra no CV
    X_train_df, X_test_df, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_SEED, stratify=y,
    )
    log.info("data.split", train=len(X_train_df), test=len(X_test_df))

    # ── StratifiedKFold (k=5) no conjunto de treino ────────────────────────
    kf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=RANDOM_SEED)
    fold_metrics: list[dict] = []

    log.info("cv.start", n_folds=N_FOLDS)
    for fold, (tr_idx, val_idx) in enumerate(kf.split(X_train_df, y_train)):
        X_fold_tr = X_train_df.iloc[tr_idx]
        X_fold_val = X_train_df.iloc[val_idx]
        y_fold_tr = y_train[tr_idx]
        y_fold_val = y_train[val_idx]

        fold_pipe = build_pipeline()
        X_fold_tr_np = fit_transform(fold_pipe, X_fold_tr)
        X_fold_val_np = transform(fold_pipe, X_fold_val)
        input_dim = X_fold_tr_np.shape[1]

        _, metrics = _run_training_loop(
            X_fold_tr_np, y_fold_tr, X_fold_val_np, y_fold_val, cfg, input_dim, device,
        )
        fold_metrics.append(metrics)
        log.info("cv.fold_done", fold=fold, recall=round(metrics["recall"], 4),
                 pr_auc=round(metrics["pr_auc"], 4), roc_auc=round(metrics["roc_auc"], 4))

    cv_summary = {
        f"cv_{k}_mean": float(np.mean([m[k] for m in fold_metrics]))
        for k in fold_metrics[0]
    }
    cv_summary |= {
        f"cv_{k}_std": float(np.std([m[k] for m in fold_metrics]))
        for k in fold_metrics[0]
    }
    log.info("cv.done", cv_recall_mean=round(cv_summary["cv_recall_mean"], 4),
             cv_pr_auc_mean=round(cv_summary["cv_pr_auc_mean"], 4))

    # ── Modelo final — treinado no conjunto completo de treino ─────────────
    final_pipe = build_pipeline()
    X_train_np = fit_transform(final_pipe, X_train_df)
    X_test_np = transform(final_pipe, X_test_df)
    input_dim = X_train_np.shape[1]
    save_pipeline(final_pipe)

    final_state, test_metrics = _run_training_loop(
        X_train_np, y_train, X_test_np, y_test, cfg, input_dim, device,
    )
    log.info("final.metrics", **{k: round(v, 4) for k, v in test_metrics.items()})

    recall_ok = test_metrics["recall"] >= RECALL_TARGET
    if not recall_ok:
        log.warning("eval.recall_below_target", recall=test_metrics["recall"], target=RECALL_TARGET)

    # ── Artefatos ──────────────────────────────────────────────────────────
    model_path = MODELS_DIR / "mlp_best.pt"
    pipeline_path = MODELS_DIR / "pipeline.pkl"

    final_model = ChurnMLP(input_dim, cfg["model"]["hidden_dims"], cfg["model"]["dropout"])
    final_model.load_state_dict(final_state)
    torch.save(final_model.state_dict(), model_path)

    # ── MLflow ─────────────────────────────────────────────────────────────
    with mlflow.start_run(run_name=run_name) as run:
        mlflow.log_params({
            "input_dim": input_dim,
            "hidden_dims": str(cfg["model"]["hidden_dims"]),
            "dropout": str(cfg["model"]["dropout"]),
            "learning_rate": cfg["training"]["learning_rate"],
            "weight_decay": cfg["training"]["weight_decay"],
            "batch_size": cfg["training"]["batch_size"],
            "epochs_max": cfg["training"]["epochs"],
            "early_stopping_patience": cfg["training"]["early_stopping_patience"],
            "n_folds": N_FOLDS,
            "test_size": TEST_SIZE,
            "random_seed": RANDOM_SEED,
            "pos_weight": POS_WEIGHT,
        })

        # métricas por fold
        for fold, fm in enumerate(fold_metrics):
            mlflow.log_metrics({f"fold{fold}_{k}": v for k, v in fm.items()}, step=fold)

        # CV agregado + teste final
        mlflow.log_metrics(cv_summary)
        mlflow.log_metrics(test_metrics)

        mlflow.set_tag("dataset_hash", dataset_hash)
        mlflow.set_tag("recall_target_met", str(recall_ok))

        mlflow.log_artifact(str(model_path))
        mlflow.log_artifact(str(pipeline_path))

        run_id = run.info.run_id

    log.info("mlflow.run_logged", run_id=run_id, experiment=experiment,
             recall_ok=recall_ok, recall=round(test_metrics["recall"], 4))
    return run_id


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Treinar ChurnMLP")
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--run-name", default=os.getenv("MLFLOW_RUN_NAME", "mlp_train"))
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    train(config_path=args.config, run_name=args.run_name)
    sys.exit(0)
