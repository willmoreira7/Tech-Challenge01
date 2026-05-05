"""Handlers para endpoints da API."""

import time
from datetime import datetime

import numpy as np
import pandas as pd
import structlog
import torch
from fastapi import FastAPI, HTTPException

from src.api.schemas import (
    HealthResponse,
    PredictBatchRequest,
    PredictBatchResponse,
    PredictionRecord,
    PredictRequest,
    PredictResponse,
    RootResponse,
)

log = structlog.get_logger()


def _check_model_ready(app: FastAPI) -> None:
    """Lança 503 se modelo ou pipeline não estiverem carregados."""
    model_ok = hasattr(app.state, "model") and app.state.model is not None
    pipeline_ok = hasattr(app.state, "pipeline") and app.state.pipeline is not None
    if not model_ok or not pipeline_ok:
        raise HTTPException(status_code=503, detail="Model or pipeline not loaded")


def _run_inference(app: FastAPI, df: pd.DataFrame) -> np.ndarray:
    """Aplica pipeline e retorna probabilidades como array flat."""
    X = app.state.pipeline.transform(df)
    with torch.no_grad():
        logits = app.state.model(torch.FloatTensor(X))
        return torch.sigmoid(logits).numpy().flatten()


async def handle_root() -> RootResponse:
    return RootResponse(
        app="Churn Prediction API",
        version="1.0.0",
        description="API para predição de churn de clientes de telecomunicações",
        documentation="/docs",
        endpoints={
            "health": "GET /health",
            "predict_single": "POST /api/v1/predict",
            "predict_batch": "POST /api/v1/predict_batch",
        },
    )


async def handle_health(app: FastAPI) -> HealthResponse:
    """Handler para GET /health com verificação de modelo."""
    start_time = getattr(app.state, "start_time", None)
    uptime = time.time() - start_time if start_time is not None else 0.0

    # Verifica se modelo e pipeline estão carregados
    model_loaded = hasattr(app.state, "model") and app.state.model is not None
    pipeline_loaded = hasattr(app.state, "pipeline") and app.state.pipeline is not None

    # Determina o status baseado no carregamento dos componentes
    if model_loaded and pipeline_loaded:
        status = "healthy"
    else:
        status = "degraded"
        if not model_loaded:
            log.warning("health_check.model_not_loaded")
        if not pipeline_loaded:
            log.warning("health_check.pipeline_not_loaded")

    return HealthResponse(
        status=status,
        model_version="1.0.0",
        uptime_seconds=round(uptime, 2),
        timestamp=datetime.utcnow().isoformat() + "Z",
    )


async def handle_predict(app: FastAPI, request: PredictRequest) -> PredictResponse:
    """Handler para POST /api/v1/predict."""
    start_time = time.time()
    try:
        _check_model_ready(app)
        df = pd.DataFrame([request.model_dump()])
        probs = _run_inference(app, df)
        churn_prob = float(probs[0])
        churn_pred = bool(churn_prob >= 0.5)
        latency_ms = (time.time() - start_time) * 1000
        log.info("predict.success", churn_probability=churn_prob, churn_predicted=churn_pred, latency_ms=round(latency_ms, 2))
        return PredictResponse(
            churn_probability=round(churn_prob, 3),
            churn_predicted=churn_pred,
            model_version="1.0.0",
            processing_time_ms=round(latency_ms, 2),
        )
    except HTTPException:
        raise
    except Exception as exc:
        log.error("predict.failed", error=str(exc))
        raise HTTPException(status_code=500, detail="Internal server error during prediction") from exc


async def handle_predict_batch(app: FastAPI, request: PredictBatchRequest) -> PredictBatchResponse:
    """Handler para POST /api/v1/predict_batch."""
    start_time = time.time()
    try:
        _check_model_ready(app)
        num_records = len(request.records)
        df = pd.DataFrame([r.model_dump() for r in request.records])
        probs = _run_inference(app, df)
        batch_id = datetime.utcnow().strftime("batch_%Y%m%d_%H%M%S")
        predictions = [
            PredictionRecord(
                record_index=i,
                churn_probability=round(float(probs[i]), 3),
                churn_predicted=bool(probs[i] >= 0.5),
            )
            for i in range(num_records)
        ]
        latency_ms = (time.time() - start_time) * 1000
        log.info("predict_batch.success", batch_id=batch_id, total_records=num_records, latency_ms=round(latency_ms, 2))
        return PredictBatchResponse(
            batch_id=batch_id,
            predictions=predictions,
            model_version="1.0.0",
            total_records=num_records,
            processing_time_ms=round(latency_ms, 2),
        )
    except HTTPException:
        raise
    except Exception as exc:
        log.error("predict_batch.failed", error=str(exc))
        raise HTTPException(status_code=500, detail="Internal server error during prediction") from exc
