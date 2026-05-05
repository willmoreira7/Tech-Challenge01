"""FastAPI — API de predição de churn com carregamento de modelo via MLflow."""
import ast
import os
import tempfile
import time
from contextlib import asynccontextmanager
from pathlib import Path

import joblib
import mlflow
import mlflow.artifacts
import mlflow.tracking
import pandas as pd
import structlog
import torch
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

from src.api.middleware import LatencyLogMiddleware
from src.api.schemas import (
    HealthResponse,
    PredictRequest,
    PredictResponse,
)
from src.models.mlp import ChurnMLP

load_dotenv()  # no-op em produção (Docker já injeta env vars)

log = structlog.get_logger()

MLFLOW_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000/mlflow")
TRAIN_EXPERIMENT = "churn-mlp"
MLFLOW_RUN_ID = os.getenv("MLFLOW_RUN_ID", "")

_state: dict = {
    "model": None,
    "pipeline": None,
    "run_id": None,
    "threshold": 0.5,
    "ready": False,
    "started_at": 0.0,
}


# ── Carregamento do modelo ────────────────────────────────────────────────

def _find_best_run() -> str | None:
    client = mlflow.tracking.MlflowClient()
    try:
        exp = client.get_experiment_by_name(TRAIN_EXPERIMENT)
        if not exp:
            log.warning("mlflow.experiment_not_found", name=TRAIN_EXPERIMENT)
            return None
        runs = client.search_runs(
            experiment_ids=[exp.experiment_id],
            filter_string="tags.recall_target_met = 'True'",
            order_by=["start_time DESC"],
            max_results=1,
        )
        return runs[0].info.run_id if runs else None
    except Exception as exc:
        log.warning("mlflow.find_run_failed", error=str(exc))
        return None


def _load_model(run_id: str | None = None) -> bool:
    global _state
    run_id = run_id or MLFLOW_RUN_ID or _find_best_run()
    if not run_id:
        log.warning("model.no_run_found")
        return False

    try:
        client = mlflow.tracking.MlflowClient()
        run = client.get_run(run_id)
        params = run.data.params
        metrics = run.data.metrics

        input_dim = int(params.get("input_dim", 30))
        hidden = ast.literal_eval(params.get("hidden_dims", "[64, 32]"))
        dropout = ast.literal_eval(params.get("dropout", "[0.3, 0.2]"))
        threshold = float(metrics.get("best_threshold", 0.5))

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            mlflow.artifacts.download_artifacts(
                run_id=run_id, artifact_path="mlp_best.pt", dst_path=tmp
            )
            mlflow.artifacts.download_artifacts(
                run_id=run_id, artifact_path="pipeline.pkl", dst_path=tmp
            )
            model = ChurnMLP(input_dim, hidden, dropout)
            model.load_state_dict(
                torch.load(tmp_path / "mlp_best.pt", map_location="cpu", weights_only=True)
            )
            model.eval()
            pipeline = joblib.load(tmp_path / "pipeline.pkl")

        _state.update({
            "model": model,
            "pipeline": pipeline,
            "run_id": run_id,
            "threshold": threshold,
            "ready": True,
        })
        log.info("model.loaded", run_id=run_id, threshold=threshold)
        return True

    except Exception as exc:
        log.error("model.load_failed", run_id=run_id, error=str(exc))
        _state["ready"] = False
        return False


# ── Lifespan ─────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    _state["started_at"] = time.time()
    mlflow.set_tracking_uri(MLFLOW_URI)
    _load_model()
    yield


# ── App ───────────────────────────────────────────────────────────────────

app = FastAPI(title="Churn Prediction API", version="1.0.0", lifespan=lifespan)
app.add_middleware(LatencyLogMiddleware)


# ── Endpoints ─────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
def health():
    # Retorna 200 sempre: ALB precisa de 2xx para marcar o target como healthy.
    # status="starting" sinaliza que o modelo ainda não foi carregado sem derrubar o tráfego.
    return HealthResponse(
        status="ok" if _state["ready"] else "starting",
        model_version=_state["run_id"],
        uptime_seconds=round(time.time() - _state["started_at"], 1),
    )


@app.post("/predict", response_model=PredictResponse)
def predict(body: PredictRequest):
    if not _state["ready"]:
        raise HTTPException(status_code=503, detail="Modelo não carregado.")

    df = pd.DataFrame([body.customer.model_dump()])

    try:
        X = _state["pipeline"].transform(df)
    except Exception as exc:
        log.error("pipeline.transform_failed", error=str(exc))
        raise HTTPException(status_code=500, detail="Erro interno na transformação.") from exc

    with torch.no_grad():
        logit = _state["model"](torch.tensor(X, dtype=torch.float32))
        prob = float(torch.sigmoid(logit).squeeze().item())

    log.info(
        "predict.done",
        probability=round(prob, 4),
        predicted=prob >= _state["threshold"],
        threshold=_state["threshold"],
    )

    return PredictResponse(
        churn_probability=round(prob, 4),
        churn_predicted=prob >= _state["threshold"],
        model_version=_state["run_id"] or "unknown",
    )


@app.post("/model/reload")
def reload_model(run_id: str | None = None):
    """Força recarga do modelo após novo treino."""
    ok = _load_model(run_id)
    if not ok:
        raise HTTPException(status_code=503, detail="Nenhum run qualificado encontrado.")
    return {"loaded": True, "run_id": _state["run_id"], "threshold": _state["threshold"]}
