"""API package para inferência de churn."""

from src.api.app import app
from src.api.handlers import (
    handle_health,
    handle_predict,
    handle_predict_batch,
    handle_root,
)
from src.api.schemas import (
    HealthResponse,
    PredictBatchRequest,
    PredictBatchResponse,
    PredictRequest,
    PredictResponse,
    RootResponse,
)
from src.api.utils import LoggingMiddleware, RateLimitMiddleware, get_lifespan

__all__ = [
    "app",
    "handle_root",
    "handle_health",
    "handle_predict",
    "handle_predict_batch",
    "PredictRequest",
    "PredictResponse",
    "PredictBatchRequest",
    "PredictBatchResponse",
    "HealthResponse",
    "RootResponse",
    "RateLimitMiddleware",
    "LoggingMiddleware",
    "get_lifespan",
]
