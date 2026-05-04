"""
Model training script for churn prediction MLP.

Treina modelo MLP com hiperparametros otimizados do mlp_config.json.
Salva artefatos (modelo, pipeline, config) para uso pela API.
Registra experimento no MLflow para rastreabilidade.
"""

import json
import pickle
import sys
from pathlib import Path
from typing import Any

import joblib
import mlflow
import mlflow.pytorch
import numpy as np
import pandas as pd
import structlog
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.metrics import (
    auc,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader, TensorDataset

# Setup
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)
torch.manual_seed(RANDOM_SEED)

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

DATA_DIR = PROJECT_ROOT / "data" / "processed"
MODELS_DIR = PROJECT_ROOT / "models"
CONFIG_FILE = MODELS_DIR / "mlp_config.json"

log = structlog.get_logger()

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# ============================================================================
# MODEL DEFINITION
# ============================================================================


class MLPChurnModel(nn.Module):
    """MLP model for churn prediction."""

    def __init__(
        self,
        input_dim: int,
        hidden_layers: int = 2,
        hidden_dim: int = 64,
        dropout: float = 0.3,
        activation: str = "relu",
    ):
        super().__init__()

        self.net = nn.ModuleList()
        self.batch_norms = nn.ModuleList()
        self.dropouts = nn.ModuleList()

        if activation == "relu":
            self.activation = nn.ReLU()
        elif activation == "tanh":
            self.activation = nn.Tanh()
        else:
            self.activation = nn.ELU()

        layer_dims = [input_dim]
        if hidden_layers == 1:
            layer_dims.extend([hidden_dim, 1])
        elif hidden_layers == 2:
            layer_dims.extend([hidden_dim, hidden_dim // 2, 1])
        elif hidden_layers == 3:
            layer_dims.extend([hidden_dim, hidden_dim // 2, hidden_dim // 4, 1])

        for i in range(len(layer_dims) - 1):
            self.net.append(nn.Linear(layer_dims[i], layer_dims[i + 1]))
            if i < len(layer_dims) - 2:
                self.batch_norms.append(nn.BatchNorm1d(layer_dims[i + 1]))
                self.dropouts.append(nn.Dropout(dropout))

    def forward(self, x):
        for i, layer in enumerate(self.net[:-1]):
            x = layer(x)
            x = self.batch_norms[i](x)
            x = self.activation(x)
            x = self.dropouts[i](x)
        x = self.net[-1](x)
        return x


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def load_config(config_path: Path) -> dict[str, Any]:
    """Load configuration from mlp_config.json."""
    if not config_path.exists():
        log.error("config_file_not_found", path=str(config_path))
        sys.exit(1)

    with open(config_path) as f:
        config = json.load(f)

    log.info("config_loaded", path=str(config_path))
    return config


def load_processed_data(data_path: Path) -> pd.DataFrame:
    """Load processed dataset."""
    if not data_path.exists():
        log.error("dataset_not_found", path=str(data_path))
        sys.exit(1)

    df = pd.read_csv(data_path)
    log.info("dataset_loaded", shape=df.shape, columns=len(df.columns))
    return df


def build_pipeline():
    """Build scikit-learn preprocessing pipeline."""
    from src.features.pipeline import build_pipeline as build_feature_pipeline

    return build_feature_pipeline()


def train_epoch(
    model: nn.Module,
    train_loader: DataLoader,
    optimizer: optim.Optimizer,
    criterion: nn.Module,
    device: torch.device,
) -> float:
    """Train one epoch."""
    model.train()
    total_loss = 0.0

    for batch_X, batch_y in train_loader:
        batch_X, batch_y = batch_X.to(device), batch_y.to(device)
        outputs = model(batch_X).squeeze(-1)
        loss = criterion(outputs, batch_y)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        total_loss += loss.item() * batch_X.size(0)

    return total_loss / len(train_loader.dataset)


def validate_epoch(
    model: nn.Module,
    val_loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
) -> float:
    """Validate one epoch."""
    model.eval()
    total_loss = 0.0

    with torch.no_grad():
        for batch_X, batch_y in val_loader:
            batch_X, batch_y = batch_X.to(device), batch_y.to(device)
            outputs = model(batch_X).squeeze(-1)
            loss = criterion(outputs, batch_y)
            total_loss += loss.item() * batch_X.size(0)

    return total_loss / len(val_loader.dataset)


def train_best_model(
    X_train: np.ndarray,
    y_train: np.ndarray,
    config: dict[str, Any],
    device: torch.device,
) -> tuple[torch.nn.Module, dict[str, list]]:
    """Train model with configured hyperparameters."""
    batch_size = config["batch_size"]
    learning_rate = config["learning_rate"]
    epochs = config["epochs"]
    patience = config["early_stopping_patience"]
    hidden_dim = config["hidden_dim"]
    hidden_layers = config["hidden_layers"]
    dropout = config["dropout"]
    activation = config["activation"]

    # Split for validation during training
    train_size = int(0.7 * len(X_train))
    val_size = len(X_train) - train_size
    X_tr, X_val, y_tr, y_val = train_test_split(
        X_train, y_train, test_size=val_size / len(X_train), random_state=RANDOM_SEED, stratify=y_train
    )

    train_loader = DataLoader(
        TensorDataset(torch.FloatTensor(X_tr), torch.FloatTensor(y_tr)),
        batch_size=batch_size,
        shuffle=True,
    )
    val_loader = DataLoader(
        TensorDataset(torch.FloatTensor(X_val), torch.FloatTensor(y_val)),
        batch_size=batch_size,
        shuffle=False,
    )

    model = MLPChurnModel(
        input_dim=X_train.shape[1],
        hidden_layers=hidden_layers,
        hidden_dim=hidden_dim,
        dropout=dropout,
        activation=activation,
    )
    model.to(device)

    optimizer = optim.Adam(model.parameters(), lr=learning_rate)

    # Calculate pos_weight for imbalanced data
    n_neg = (y_train == 0).sum()
    n_pos = (y_train == 1).sum()
    pos_weight = torch.tensor([n_neg / n_pos]).to(device)

    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)

    train_losses = []
    val_losses = []
    best_val_loss = float("inf")
    patience_counter = 0
    best_model_state = None
    best_epoch = 0

    log.info("training_started", epochs=epochs, batch_size=batch_size, lr=learning_rate)

    for epoch in range(epochs):
        train_loss = train_epoch(model, train_loader, optimizer, criterion, device)
        val_loss = validate_epoch(model, val_loader, criterion, device)

        train_losses.append(train_loss)
        val_losses.append(val_loss)

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            best_model_state = model.state_dict().copy()
            best_epoch = epoch
        else:
            patience_counter += 1

        if (epoch + 1) % 10 == 0:
            log.info(
                "epoch_checkpoint",
                epoch=epoch + 1,
                train_loss=f"{train_loss:.4f}",
                val_loss=f"{val_loss:.4f}",
                patience=f"{patience_counter}/{patience}",
            )

        if patience_counter >= patience:
            log.info("early_stopping", epoch=epoch + 1, best_epoch=best_epoch + 1)
            break

    model.load_state_dict(best_model_state)
    log.info("training_completed", best_epoch=best_epoch + 1, best_val_loss=f"{best_val_loss:.4f}")

    return model, {"train_loss": train_losses, "val_loss": val_losses, "best_epoch": best_epoch}


def evaluate_model(
    model: nn.Module, X_test: np.ndarray, y_test: np.ndarray, device: torch.device
) -> dict[str, float]:
    """Evaluate model on test set."""
    model.eval()

    with torch.no_grad():
        logits = (
            model(torch.FloatTensor(X_test).to(device)).squeeze(-1).cpu().numpy()
        )

    probabilities = 1 / (1 + np.exp(-logits))
    predictions = (probabilities >= 0.5).astype(int)

    metrics = {
        "auc_roc": roc_auc_score(y_test, probabilities)
        if len(np.unique(y_test)) > 1
        else 0,
        "f1": f1_score(y_test, predictions, zero_division=0),
        "recall": recall_score(y_test, predictions, zero_division=0),
        "precision": precision_score(y_test, predictions, zero_division=0),
    }

    if len(np.unique(y_test)) > 1:
        prec_vals, rec_vals, _ = precision_recall_curve(y_test, probabilities)
        metrics["pr_auc"] = auc(rec_vals, prec_vals)
    else:
        metrics["pr_auc"] = 0

    tn, fp, fn, tp = confusion_matrix(y_test, predictions).ravel()
    metrics["specificity"] = tn / (tn + fp) if (tn + fp) > 0 else 0
    metrics["sensitivity"] = tp / (tp + fn) if (tp + fn) > 0 else 0
    metrics["tn"] = int(tn)
    metrics["fp"] = int(fp)
    metrics["fn"] = int(fn)
    metrics["tp"] = int(tp)

    return metrics


def save_artifacts(
    model: nn.Module,
    pipeline,
    config: dict[str, Any],
    metrics: dict[str, float],
) -> None:
    """Save model, pipeline, and configuration."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    # Save model
    torch.save(model.state_dict(), MODELS_DIR / "mlp_best.pt")
    log.info("model_saved", path=str(MODELS_DIR / "mlp_best.pt"))

    # Save pipeline
    joblib.dump(pipeline, MODELS_DIR / "pipeline.pkl")
    log.info("pipeline_saved", path=str(MODELS_DIR / "pipeline.pkl"))

    # Update config with metrics
    config_to_save = config.copy()
    config_to_save["metrics"] = {k: v for k, v in metrics.items() if k not in ["tn", "fp", "fn", "tp"]}

    # Save config
    with open(MODELS_DIR / "mlp_config.json", "w") as f:
        json.dump(config_to_save, f, indent=2)
    log.info("config_saved", path=str(MODELS_DIR / "mlp_config.json"))

    # Save test results
    test_results = {
        k: float(v) if isinstance(v, (int, float, np.number)) else v
        for k, v in metrics.items()
    }
    with open(MODELS_DIR / "test_results.json", "w") as f:
        json.dump(test_results, f, indent=2)
    log.info("test_results_saved", path=str(MODELS_DIR / "test_results.json"))


def register_in_mlflow(
    model: nn.Module,
    config: dict[str, Any],
    metrics: dict[str, float],
) -> None:
    """Register experiment and model in MLflow."""
    try:
        experiment_name = "churn-mlp-training"
        mlflow.set_experiment(experiment_name)

        with mlflow.start_run(run_name="train-best-model"):
            # Log hyperparameters
            mlflow.log_param("input_dim", config["input_dim"])
            mlflow.log_param("hidden_dim", config["hidden_dim"])
            mlflow.log_param("hidden_layers", config["hidden_layers"])
            mlflow.log_param("dropout", config["dropout"])
            mlflow.log_param("activation", config["activation"])
            mlflow.log_param("batch_size", config["batch_size"])
            mlflow.log_param("learning_rate", config["learning_rate"])
            mlflow.log_param("epochs", config["epochs"])
            mlflow.log_param("early_stopping_patience", config["early_stopping_patience"])

            # Log metrics
            for metric_name, metric_value in metrics.items():
                if (
                    metric_name not in ["tn", "fp", "fn", "tp"]
                    and isinstance(metric_value, (int, float, np.number))
                ):
                    mlflow.log_metric(metric_name, float(metric_value))

            # Log model
            mlflow.pytorch.log_model(model, "model", pickle_module=pickle)

            # Log artifacts
            mlflow.log_artifact(str(MODELS_DIR / "mlp_config.json"))
            mlflow.log_artifact(str(MODELS_DIR / "test_results.json"))

            # Set tags
            mlflow.set_tag("model_type", "MLP")
            mlflow.set_tag("status", "training-completed")
            mlflow.set_tag("dataset", "Telco Customer Churn")
            mlflow.set_tag("random_seed", str(RANDOM_SEED))

        log.info("mlflow_registration_completed", experiment=experiment_name)
    except Exception as e:
        log.warning("mlflow_registration_failed", error=str(e))


def validate_performance(metrics: dict[str, float]) -> bool:
    """Validate model performance against business metric."""
    recall = metrics.get("recall", 0)

    if recall < 0.75:
        log.error(
            "recall_threshold_not_met",
            recall=f"{recall:.4f}",
            required=0.75,
        )
        return False

    log.info("recall_threshold_met", recall=f"{recall:.4f}")
    return True


def log_summary(metrics: dict[str, float]) -> None:
    """Log training summary."""
    log.info(
        "training_summary",
        auc_roc=f"{metrics.get('auc_roc', 0):.4f}",
        recall=f"{metrics.get('recall', 0):.4f}",
        precision=f"{metrics.get('precision', 0):.4f}",
        pr_auc=f"{metrics.get('pr_auc', 0):.4f}",
        f1=f"{metrics.get('f1', 0):.4f}",
        specificity=f"{metrics.get('specificity', 0):.4f}",
        sensitivity=f"{metrics.get('sensitivity', 0):.4f}",
    )


def main():
    """Main training pipeline."""
    log.info("training_pipeline_started", seed=RANDOM_SEED, device=str(DEVICE))

    # 1. Load config
    config = load_config(CONFIG_FILE)
    log.info("config_loaded", config_keys=list(config.keys()))

    # 2. Load data
    df = load_processed_data(DATA_DIR / "telco_churn_cleaned.csv")
    X = df.drop(columns=["Churn"])
    y = df["Churn"].astype(int).values

    # 3. Split estratificado
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=RANDOM_SEED, stratify=y
    )
    log.info("data_split", train_size=len(X_train), test_size=len(X_test))

    # 4. Build pipeline and transform
    pipeline = build_pipeline()
    X_train_processed = pipeline.fit_transform(X_train)
    X_test_processed = pipeline.transform(X_test)
    log.info("pipeline_fitted", input_dim=X_train_processed.shape[1])

    # 5. Train model
    model, history = train_best_model(X_train_processed, y_train, config, DEVICE)

    # 6. Evaluate on test set
    metrics = evaluate_model(model, X_test_processed, y_test, DEVICE)

    # 7. Validate performance
    if not validate_performance(metrics):
        log.error("model_validation_failed")
        sys.exit(2)

    # 8. Save artifacts
    save_artifacts(model, pipeline, config, metrics)

    # 9. Register in MLflow
    register_in_mlflow(model, config, metrics)

    # 10. Log summary
    log_summary(metrics)

    log.info("training_pipeline_completed", status="success")
    return 0


if __name__ == "__main__":
    sys.exit(main())
