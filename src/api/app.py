"""FastAPI application com middleware, lifespan e rotas."""

from fastapi import FastAPI
from starlette.middleware import Middleware

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
from src.config import configure_logging

# Configurar logging estruturado
configure_logging()

# Configurar middlewares
def get_middlewares(enable_rate_limit: bool = True) -> list:
    """Retornar lista de middlewares."""
    middlewares = [
        Middleware(LoggingMiddleware),
        Middleware(RateLimitMiddleware, max_requests=10, window_seconds=30, enabled=enable_rate_limit),
    ]
    return middlewares


def create_app(enable_rate_limit: bool = True) -> FastAPI:
    """Criar e configurar aplicação FastAPI.

    Args:
        enable_rate_limit: Se True, habilita o middleware de rate limiting (padrão).
                         Se False, desabilita para testes.
    """
    middlewares = get_middlewares(enable_rate_limit=enable_rate_limit)
    app = FastAPI(
        title="Churn Prediction API",
        version="1.0.0",
        description="API para predição de churn de clientes de telecomunicações",
        middleware=middlewares,
        lifespan=get_lifespan(),
    )

    # Rotas
    @app.get("/", response_model=RootResponse)
    async def root():
        """Rota raiz com informações da API."""
        return await handle_root()

    @app.get("/health", response_model=HealthResponse)
    async def health():
        """Health check do serviço."""
        return await handle_health(app)

    @app.post("/api/v1/predict", response_model=PredictResponse)
    async def predict(request: PredictRequest):
        """Predição individual de churn."""
        return await handle_predict(app, request)

    @app.post("/api/v1/predict_batch", response_model=PredictBatchResponse)
    async def predict_batch(request: PredictBatchRequest):
        """Predição em batch de churn."""
        return await handle_predict_batch(app, request)

    return app


# Criar app global
app = create_app()
