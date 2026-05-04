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

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)
torch.manual_seed(RANDOM_SEED)


async def handle_root() -> RootResponse:
    """Handler para GET /."""
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
    """Handler para GET /health."""
    uptime = time.time() - app.state.start_time
    return HealthResponse(
        status="ok",
        model_version="1.0.0",
        uptime_seconds=round(uptime, 2),
        timestamp=datetime.utcnow().isoformat() + "Z",
    )


async def handle_predict(app: FastAPI, request: PredictRequest) -> PredictResponse:
    """Handler para POST /api/v1/predict."""
    start_time = time.time()

    try:
        # Verificar se modelo está carregado
        if not hasattr(app.state, "model") or app.state.model is None:
            log.error("predict.model_not_loaded")
            raise HTTPException(
                status_code=503,
                detail="Model or pipeline not loaded",
            )

        if not hasattr(app.state, "pipeline") or app.state.pipeline is None:
            log.error("predict.pipeline_not_loaded")
            raise HTTPException(
                status_code=503,
                detail="Model or pipeline not loaded",
            )

        # Converter request para DataFrame
        df = pd.DataFrame([request.model_dump()])

        # Aplicar pipeline (preprocessamento)
        X = app.state.pipeline.transform(df)

        # Inferência
        with torch.no_grad():
            X_tensor = torch.FloatTensor(X)
            logits = app.state.model(X_tensor)
            probabilities = torch.sigmoid(logits).numpy()

        churn_prob = float(probabilities[0][0])
        churn_pred = bool(churn_prob >= 0.5)

        latency_ms = (time.time() - start_time) * 1000

        log.info(
            "predict.success",
            churn_probability=churn_prob,
            churn_predicted=churn_pred,
            latency_ms=round(latency_ms, 2),
        )

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


async def handle_predict_batch(
    app: FastAPI, request: PredictBatchRequest
) -> PredictBatchResponse:
    """Handler para POST /api/v1/predict_batch."""
    start_time = time.time()

    try:
        # Verificar se modelo está carregado
        if not hasattr(app.state, "model") or app.state.model is None:
            log.error("predict_batch.model_not_loaded")
            raise HTTPException(
                status_code=503,
                detail="Model or pipeline not loaded",
            )

        if not hasattr(app.state, "pipeline") or app.state.pipeline is None:
            log.error("predict_batch.pipeline_not_loaded")
            raise HTTPException(
                status_code=503,
                detail="Model or pipeline not loaded",
            )

        # Validar tamanho do batch
        num_records = len(request.records)
        if num_records == 0:
            raise HTTPException(
                status_code=400,
                detail="Batch cannot be empty",
            )
        if num_records > 10000:
            raise HTTPException(
                status_code=400,
                detail="Batch size exceeds maximum of 10000 records",
            )

        # Converter requests para DataFrame
        records_data = [record.model_dump() for record in request.records]
        df = pd.DataFrame(records_data)

        # Aplicar pipeline
        X = app.state.pipeline.transform(df)

        # Inferência
        with torch.no_grad():
            X_tensor = torch.FloatTensor(X)
            logits = app.state.model(X_tensor)
            probabilities = torch.sigmoid(logits).numpy().flatten()

        # Gerar batch_id com timestamp
        batch_id = datetime.utcnow().strftime("batch_%Y%m%d_%H%M%S")

        # Estruturar predictions
        predictions = [
            PredictionRecord(
                record_index=i,
                churn_probability=round(float(probabilities[i]), 3),
                churn_predicted=bool(probabilities[i] >= 0.5),
            )
            for i in range(num_records)
        ]

        latency_ms = (time.time() - start_time) * 1000

        log.info(
            "predict_batch.success",
            batch_id=batch_id,
            total_records=num_records,
            latency_ms=round(latency_ms, 2),
        )

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
