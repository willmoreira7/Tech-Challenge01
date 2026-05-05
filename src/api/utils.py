"""Utilitários para a API: middleware e carregamento de modelos."""

import json
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

import structlog
import torch
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from src.features.pipeline import (
    load_pipeline,  # noqa: F401 — re-exported para callers da API
)
from src.models.mlp import ChurnMLP

log = structlog.get_logger()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limit: 10 requests por 30 segundos por IP."""

    def __init__(self, app, max_requests: int = 10, window_seconds: int = 30, enabled: bool = True):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.enabled = enabled
        self.requests: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        if not self.enabled:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()

        self.requests[client_ip] = [
            ts for ts in self.requests[client_ip]
            if current_time - ts < self.window_seconds
        ]

        if len(self.requests[client_ip]) >= self.max_requests:
            log.warning(
                "rate_limit.exceeded",
                client_ip=client_ip,
                requests_count=len(self.requests[client_ip]),
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too Many Requests",
                    "detail": f"Rate limit exceeded: {self.max_requests} requests per {self.window_seconds} seconds",
                    "retry_after": self.window_seconds,
                    "status_code": 429,
                },
            )

        self.requests[client_ip].append(current_time)
        return await call_next(request)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware para logging de requests e responses com timing."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        path = request.url.path
        method = request.method

        log.info("api.request", path=path, method=method, timestamp=datetime.utcnow().isoformat())

        try:
            response = await call_next(request)
            latency_ms = (time.time() - start_time) * 1000
            log.info("api.response", path=path, method=method, status=response.status_code, latency_ms=round(latency_ms, 2))
            return response
        except Exception as exc:
            latency_ms = (time.time() - start_time) * 1000
            log.error("api.error", path=path, method=method, latency_ms=round(latency_ms, 2), error=str(exc))
            raise


def load_model(model_path: str | None = None, config_path: str | None = None) -> ChurnMLP:
    """Carregar modelo MLP com arquitetura definida pelo config JSON."""
    try:
        project_root = Path(__file__).parent.parent.parent
        if model_path is None:
            model_path = str(project_root / "models" / "mlp_best.pt")
        if config_path is None:
            config_path = str(project_root / "models" / "mlp_config.json")

        with open(config_path) as f:
            config = json.load(f)

        model = ChurnMLP(
            input_dim=config.get("input_dim", 30),
            hidden=config.get("hidden_dims", [64, 32]),
            dropout=config.get("dropout", [0.3, 0.2]),
        )

        state_dict = torch.load(model_path, weights_only=True)
        model.load_state_dict(state_dict)
        model.eval()

        log.info("model.loaded", path=model_path, config=config_path)
        return model
    except Exception as exc:
        log.error("model.load_failed", path=model_path, error=str(exc))
        raise


def get_lifespan():
    """Criar lifespan context manager para FastAPI."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        try:
            app.state.model = load_model()
            app.state.pipeline = load_pipeline()
            app.state.start_time = time.time()
            log.info("app.startup", model="mlp_best.pt", pipeline="pipeline.pkl")
        except Exception as exc:
            log.error("app.startup_failed", error=str(exc))
            raise

        yield

        log.info("app.shutdown")

    return lifespan
