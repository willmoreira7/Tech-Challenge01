"""Utilitários para a API: middleware, logging, carregamento de modelos."""

import json
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

import joblib
import structlog
import torch
import torch.nn as nn
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

log = structlog.get_logger()


class MLPChurnModel(nn.Module):
    """Modelo MLP para predição de churn."""

    def __init__(
        self,
        input_dim: int = 30,
        hidden_dim: int = 64,
        hidden_layers: int = 2,
        dropout: float = 0.4,
    ):
        super().__init__()
        layers = []

        # Primeira camada
        layers.append(nn.Linear(input_dim, hidden_dim))
        layers.append(nn.BatchNorm1d(hidden_dim))
        layers.append(nn.ReLU())
        layers.append(nn.Dropout(dropout))

        # Camada intermediária
        layers.append(nn.Linear(hidden_dim, hidden_dim // 2))
        layers.append(nn.BatchNorm1d(hidden_dim // 2))
        layers.append(nn.ReLU())
        layers.append(nn.Dropout(dropout))

        # Camada de saída
        layers.append(nn.Linear(hidden_dim // 2, 1))

        self.net = nn.Sequential(*layers)

    def forward(self, x):
        """Forward pass."""
        return self.net(x)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limit: 10 requests por 30 segundos por IP."""

    def __init__(self, app, max_requests: int = 10, window_seconds: int = 30, enabled: bool = True):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.enabled = enabled
        self.requests = defaultdict(list)  # {ip: [timestamp1, timestamp2, ...]}

    async def dispatch(self, request: Request, call_next):
        """Verificar rate limit e processar request."""
        # Skipar rate limit se desabilitado
        if not self.enabled:
            response = await call_next(request)
            return response

        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()

        # Limpar timestamps expirados
        self.requests[client_ip] = [
            ts for ts in self.requests[client_ip]
            if current_time - ts < self.window_seconds
        ]

        # Verificar limite
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
                    "detail": "Rate limit exceeded: 10 requests per 30 seconds",
                    "retry_after": self.window_seconds,
                    "status_code": 429,
                },
            )

        # Registrar novo request
        self.requests[client_ip].append(current_time)

        response = await call_next(request)
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware para logging de requests e responses com timing."""

    async def dispatch(self, request: Request, call_next):
        """Logar request e response com timing."""
        start_time = time.time()
        path = request.url.path
        method = request.method

        log.info(
            "api.request",
            path=path,
            method=method,
            timestamp=datetime.utcnow().isoformat(),
        )

        try:
            response = await call_next(request)
            latency_ms = (time.time() - start_time) * 1000

            log.info(
                "api.response",
                path=path,
                method=method,
                status=response.status_code,
                latency_ms=round(latency_ms, 2),
            )
            return response
        except Exception as exc:
            latency_ms = (time.time() - start_time) * 1000
            log.error(
                "api.error",
                path=path,
                method=method,
                latency_ms=round(latency_ms, 2),
                error=str(exc),
            )
            raise


def load_model(model_path: str | None = None, config_path: str | None = None):
    """Carregar modelo MLP com arquitetura definida.

    Args:
        model_path: Caminho para modelo (usa padrão baseado em projeto se None)
        config_path: Caminho para config (usa padrão baseado em projeto se None)
    """
    try:
        # Resolver caminhos baseados no projeto raiz
        project_root = Path(__file__).parent.parent.parent
        if model_path is None:
            model_path = str(project_root / "models" / "mlp_best.pt")
        if config_path is None:
            config_path = str(project_root / "models" / "mlp_config.json")

        # Carregar configuração
        with open(config_path) as f:
            config = json.load(f)

        # Criar arquitetura do modelo
        model = MLPChurnModel(
            input_dim=config.get("input_dim", 30),
            hidden_dim=config.get("hidden_dim", 32),
            hidden_layers=config.get("hidden_layers", 2),
            dropout=config.get("dropout", 0.4),
        )

        # Carregar pesos
        state_dict = torch.load(model_path, weights_only=True)
        model.load_state_dict(state_dict, strict=False)

        # Colocar em modo de avaliação
        model.eval()

        log.info("model.loaded", path=model_path, config=config_path)
        return model
    except Exception as exc:
        log.error("model.load_failed", path=model_path, error=str(exc))
        raise


def load_pipeline(pipeline_path: str | None = None):
    """Carregar pipeline scikit-learn.

    Args:
        pipeline_path: Caminho para pipeline (usa padrão baseado em projeto se None)
    """
    try:
        # Resolver caminho baseado no projeto raiz
        if pipeline_path is None:
            project_root = Path(__file__).parent.parent.parent
            pipeline_path = str(project_root / "models" / "pipeline.pkl")

        pipeline = joblib.load(pipeline_path)
        log.info("pipeline.loaded", path=pipeline_path)
        return pipeline
    except Exception as exc:
        log.error("pipeline.load_failed", path=pipeline_path, error=str(exc))
        raise


def get_lifespan():
    """Criar lifespan context manager para FastAPI."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Startup
        try:
            app.state.model = load_model()
            app.state.pipeline = load_pipeline()
            app.state.start_time = time.time()
            log.info("app.startup", model="mlp_best.pt", pipeline="pipeline.pkl")
        except Exception as exc:
            log.error("app.startup_failed", error=str(exc))
            raise

        yield

        # Shutdown
        log.info("app.shutdown")

    return lifespan
