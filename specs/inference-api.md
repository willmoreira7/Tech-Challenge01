# Spec: API de Inferência (FastAPI)

Predição de churn via REST API com suporte a predições individuais e em batch.

---

## Endpoints

### `GET /`

Rota raiz com informações básicas da API.

**Response 200**:

```json
{
  "app": "Churn Prediction API",
  "version": "1.0.0",
  "description": "API para predição de churn de clientes de telecomunicações",
  "documentation": "/docs",
  "endpoints": {
    "health": "GET /health",
    "predict_single": "POST /api/v1/predict",
    "predict_batch": "POST /api/v1/predict_batch"
  }
}
```

---

### `GET /health`

Verificação de saúde e status do serviço.

**Response 200**:

```json
{
  "status": "ok",
  "model_version": "1.0.0",
  "uptime_seconds": 123.4,
  "timestamp": "2026-05-03T15:45:30Z"
}
```

---

### `POST /api/v1/predict`

Predição individual de churn para um cliente.

**Request body** (Pydantic `PredictRequest`):

```json
{
  "gender": "Male",
  "SeniorCitizen": 0,
  "Partner": "Yes",
  "Dependents": "No",
  "tenure": 12,
  "PhoneService": "Yes",
  "MultipleLines": "No phone service",
  "InternetService": "Fiber optic",
  "OnlineSecurity": "No",
  "OnlineBackup": "No",
  "DeviceProtection": "No",
  "TechSupport": "No",
  "StreamingTV": "No",
  "StreamingMovies": "No",
  "Contract": "Month-to-month",
  "PaperlessBilling": "Yes",
  "PaymentMethod": "Electronic check",
  "MonthlyCharges": 70.35,
  "TotalCharges": 844.20
}
```

**Response 200** (`PredictResponse`):

```json
{
  "churn_probability": 0.823,
  "churn_predicted": true,
  "model_version": "1.0.0",
  "processing_time_ms": 45.2
}
```

**Erros:**

| Código | Causa |
|--------|-------|
| `422` | Campo ausente ou tipo inválido (Pydantic) |
| `500` | Falha interna no modelo |
| `503` | Modelo não carregado |

---

### `POST /api/v1/predict_batch`

Predição em batch para múltiplos clientes (até 10.000 registros).

**Request body** (`PredictBatchRequest`):

```json
{
  "records": [
    {
      "gender": "Male",
      "SeniorCitizen": 0,
      "Partner": "Yes",
      "Dependents": "No",
      "tenure": 12,
      "PhoneService": "Yes",
      "MultipleLines": "No phone service",
      "InternetService": "Fiber optic",
      "OnlineSecurity": "No",
      "OnlineBackup": "No",
      "DeviceProtection": "No",
      "TechSupport": "No",
      "StreamingTV": "No",
      "StreamingMovies": "No",
      "Contract": "Month-to-month",
      "PaperlessBilling": "Yes",
      "PaymentMethod": "Electronic check",
      "MonthlyCharges": 70.35,
      "TotalCharges": 844.20
    },
    {
      "gender": "Female",
      "SeniorCitizen": 1,
      "Partner": "No",
      "Dependents": "Yes",
      "tenure": 24,
      "PhoneService": "No",
      "MultipleLines": "No phone service",
      "InternetService": "DSL",
      "OnlineSecurity": "Yes",
      "OnlineBackup": "Yes",
      "DeviceProtection": "Yes",
      "TechSupport": "Yes",
      "StreamingTV": "Yes",
      "StreamingMovies": "Yes",
      "Contract": "Two year",
      "PaperlessBilling": "No",
      "PaymentMethod": "Automatic bank transfer",
      "MonthlyCharges": 85.50,
      "TotalCharges": 2050.00
    }
  ]
}
```

**Response 200** (`PredictBatchResponse`):

```json
{
  "batch_id": "batch_20260503_154530",
  "predictions": [
    {
      "record_index": 0,
      "churn_probability": 0.823,
      "churn_predicted": true
    },
    {
      "record_index": 1,
      "churn_probability": 0.142,
      "churn_predicted": false
    }
  ],
  "model_version": "1.0.0",
  "total_records": 2,
  "processing_time_ms": 78.5
}
```

**Constraints:**

- Máximo 10.000 registros por request
- Timeout: 60 segundos
- Recomendado: ≤ 1.000 para latência < 5s

**Erros:**

| Código | Causa |
|--------|-------|
| `400` | Array vazio ou mais de 10.000 registros |
| `422` | Campo ausente ou tipo inválido em qualquer record |
| `500` | Falha interna no modelo |
| `503` | Modelo não carregado |
| `504` | Timeout (processamento > 60s) |

---

## Validações Pydantic

### PredictRequest e registros em batch

- `gender`: `Literal["Male", "Female"]` (case-sensitive)
- `SeniorCitizen`: `int` com `ge=0, le=1`
- `Partner`: `Literal["Yes", "No"]`
- `Dependents`: `Literal["Yes", "No"]`
- `tenure`: `int` com `ge=0`
- `PhoneService`: `Literal["Yes", "No"]`
- `MultipleLines`: `Literal["Yes", "No", "No phone service"]`
- `InternetService`: `Literal["DSL", "Fiber optic", "No"]`
- `OnlineSecurity`, `OnlineBackup`, `DeviceProtection`, `TechSupport`, `StreamingTV`, `StreamingMovies`: `Literal["Yes", "No", "No internet service"]`
- `Contract`: `Literal["Month-to-month", "One year", "Two year"]`
- `PaperlessBilling`: `Literal["Yes", "No"]`
- `PaymentMethod`: `Literal["Electronic check", "Mailed check", "Bank transfer (automatic)", "Credit card (automatic)"]`
- `MonthlyCharges`: `float` com `ge=0`
- `TotalCharges`: `float` com `ge=0`

### PredictBatchRequest

- `records`: `list[PredictRequest]` com `min_items=1, max_items=10000`

---

## Middleware de Logging

Logar via structlog a cada request/response com timing:

```python
# Request
log.info(
    "api.request",
    path="/api/v1/predict",
    method="POST",
    timestamp=datetime.utcnow().isoformat(),
)

# Response
log.info(
    "api.response",
    path="/api/v1/predict",
    status=200,
    latency_ms=45.2,
    model_version="1.0.0",
)
```

---

## Middleware de Rate Limit

Limitar requisições a 10 requests a cada 30 segundos por cliente (identificado por IP).

**Implementação:**

```python
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from collections import defaultdict
import time
import structlog

log = structlog.get_logger()

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limit: 10 requests por 30 segundos por IP."""

    def __init__(self, app, max_requests: int = 10, window_seconds: int = 30):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)  # {ip: [timestamp1, timestamp2, ...]}

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
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
                    "retry_after": 30,
                },
            )
        
        # Registrar novo request
        self.requests[client_ip].append(current_time)
        
        response = await call_next(request)
        return response
```

**Configurar no FastAPI:**

```python
from starlette.middleware import Middleware

middlewares = [
    Middleware(RateLimitMiddleware, max_requests=10, window_seconds=30),
]

app = FastAPI(
    title="Churn Prediction API",
    version="1.0.0",
    middleware=middlewares,
    lifespan=lifespan,
)
```

**Response 429 — Too Many Requests:**

```json
{
  "error": "Too Many Requests",
  "detail": "Rate limit exceeded: 10 requests per 30 seconds",
  "retry_after": 30,
  "status_code": 429
}
```

---

## SLOs

- Latência p50 (individual) < 100ms
- Latência p99 (individual) < 500ms
- Latência p50 (batch até 1k) < 5s
- Uptime > 99.5%

---

## Startup e Lifespan

Carregar modelo e pipeline no `lifespan` do FastAPI (não por request):

```python
from contextlib import asynccontextmanager
import torch
import joblib
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: carregar modelo e pipeline
    app.state.model = torch.load("models/mlp_best.pt", weights_only=False)
    app.state.model.eval()
    app.state.pipeline = joblib.load("models/pipeline.pkl")
    app.state.start_time = time.time()
    log.info("app.startup", model="mlp_best.pt", pipeline="pipeline.pkl")
    yield
    # Shutdown: limpeza (se necessário)
    log.info("app.shutdown")

app = FastAPI(title="Churn Prediction API", version="1.0.0", lifespan=lifespan)
```

---

## Estrutura de Diretórios

```
src/api/
├── __init__.py
├── app.py              # FastAPI app com lifespan e middleware
├── schemas.py          # Pydantic models (Request/Response)
├── handlers.py         # Lógica dos endpoints
└── utils.py            # Funções auxiliares (load_model, etc.)

tests/
├── integration/
│   ├── test_api_health.py
│   ├── test_api_predict.py
│   └── test_api_predict_batch.py
```

---

## Testes esperados

### Smoke Tests (Funcionalidade Básica)
- `test_root_returns_info` — GET / → 200 com app, version, endpoints
- `test_health_returns_ok` — GET /health → 200 com status "ok"
- `test_predict_single_works` — POST /api/v1/predict com payload válido → 200
- `test_predict_batch_works` — POST /api/v1/predict_batch com múltiplos registros → 200

### Schema Tests (Validação de Request/Response)

Usar **Pandera** para validar estrutura de DataFrames:

```python
import pandera as pa
from pandera import Column, DataFrameSchema

# Schema de entrada
input_schema = pa.DataFrameSchema({
    "gender": Column(str, isin=["Male", "Female"]),
    "SeniorCitizen": Column(int, isin=[0, 1]),
    "tenure": Column(int, checks=pa.checks.GreaterThanOrEqual(0)),
    "MonthlyCharges": Column(float, checks=pa.checks.GreaterThanOrEqual(0)),
    # ... outros campos
})

# Schema de output (após transformação)
output_schema = pa.DataFrameSchema({
    "churn_probability": Column(float, checks=[
        pa.checks.GreaterThanOrEqual(0.0),
        pa.checks.LessThanOrEqual(1.0),
    ]),
})

@input_schema.validate
def predict_single(request_data: pd.DataFrame):
    # Lógica de predição
    pass
```

**Testes de Schema:**
- `test_predict_request_schema_valid` — validar request conforme schema
- `test_predict_response_schema_valid` — validar response conforme schema
- `test_predict_invalid_schema_rejected` — dados inválidos são rejeitados
- `test_batch_schema_all_records` — schema aplicado a todos os records em batch

### API Tests (Root)
- `test_root_returns_ok` — GET / → 200 com informações da API
- `test_root_has_version` — campo version está presente
- `test_root_has_endpoints_info` — endpoints info está presente

### API Tests (Health)
- `test_health_returns_ok` — GET /health → 200 com status "ok"
- `test_health_uptime_positive` — campo uptime_seconds > 0
- `test_health_model_version_present` — model_version está presente

### API Tests (Single Predict)
- `test_predict_valid_payload` — POST /api/v1/predict → 200 com churn_probability em [0, 1]
- `test_predict_invalid_payload` — missing field → 422
- `test_predict_invalid_type` — tenure como string → 422
- `test_predict_latency` — resposta em < 200ms
- `test_predict_returns_all_fields` — response contém all required fields

### API Tests (Batch Predict)
- `test_predict_batch_valid_payload` — POST /api/v1/predict_batch com 2-5 registros → 200
- `test_predict_batch_single_record` — com 1 registro → 200
- `test_predict_batch_empty` — array vazio → 400
- `test_predict_batch_exceeds_limit` — mais de 10k registros → 400
- `test_predict_batch_invalid_record` — 1 record inválido → 422
- `test_predict_batch_returns_all_predictions` — total_records == len(predictions)
- `test_predict_batch_record_index_matches` — record_index corresponde ao índice original
- `test_predict_batch_processing_time` — latência escalável com volume

### Error Handling Tests
- `test_500_on_model_inference_failure` — exceção no modelo → 500
- `test_503_on_model_not_ready` — modelo não carregado → 503
- `test_503_on_pipeline_not_ready` — pipeline não carregado → 503
- `test_422_on_validation_error` — Pydantic rejeita dados inválidos → 422
- `test_429_on_rate_limit_exceeded` — mais de 10 requests em 30s → 429

**Total de Testes Esperados:** ≥ 35 testes (smoke + schema + API + error handling)

---

## Error Handling e HTTP Codes

### 400 — Bad Request (Batch Size)

```json
{
  "error": "Validation Error",
  "detail": "Batch size exceeds maximum of 10000 records",
  "status_code": 400
}
```

### 429 — Too Many Requests (Rate Limit)

```json
{
  "error": "Too Many Requests",
  "detail": "Rate limit exceeded: 10 requests per 30 seconds",
  "retry_after": 30,
  "status_code": 429
}
```

### 422 — Unprocessable Entity (Validação Pydantic)

```json
{
  "error": "Validation Error",
  "detail": "Field required: tenure",
  "status_code": 422
}
```

### 500 — Internal Server Error (Falha do Modelo)

```json
{
  "error": "Prediction Error",
  "detail": "Internal server error during prediction",
  "status_code": 500
}
```

### 503 — Service Unavailable (Modelo Não Carregado)

```json
{
  "error": "Prediction Error",
  "detail": "Model or pipeline not loaded",
  "status_code": 503
}
```

### 504 — Gateway Timeout (Timeout no Batch)

```json
{
  "error": "Prediction Error",
  "detail": "Request timeout (> 60 seconds)",
  "status_code": 504
}
```

---

## Dependências do pyproject.toml

Para API e testes:

```toml
[project]
dependencies = [
    "fastapi>=0.135.3",
    "uvicorn>=0.29.0",
    "pydantic>=2.0",
    "structlog>=25.5.0",
    "torch>=2.11.0",
    "scikit-learn>=1.8.0",
    "joblib>=1.3.0",
]

[dependency-groups]
dev = [
    "pytest>=9.0.3",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=7.0",
    "pandera>=0.18.0",  # Para schema tests
]
```

---

## Deployment

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml requirements.txt ./
RUN pip install --no-cache-dir -e .

COPY src/ src/
COPY models/ models/

CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Run

```bash
# Local (com reload)
task api
# ou
uvicorn src.api.app:app --reload --port 8000

# Production
task api-prod
# ou
gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.api.app:app --bind 0.0.0.0:8000
```

### Testes

```bash
# Todos os testes
pytest tests/ -v

# Apenas testes da API
task test-api
# ou
pytest tests/integration/ -v

# Com coverage
pytest tests/integration/ --cov=src.api --cov-report=term
```

---

## Arquivos Implementados

| Arquivo | Descrição |
|---------|-----------|
| `src/api/__init__.py` | Pacote da API |
| `src/api/app.py` | Aplicação FastAPI com lifespan e middleware |
| `src/api/schemas.py` | Pydantic models (Request/Response) |
| `src/api/handlers.py` | Lógica dos endpoints |
| `src/api/utils.py` | Funções auxiliares (load_model, predict, etc.) |
| `tests/integration/conftest.py` | Fixtures para testes |
| `tests/integration/test_api_health.py` | Testes de health check |
| `tests/integration/test_api_predict.py` | Testes de predição única |
| `tests/integration/test_api_predict_batch.py` | Testes de predição batch |

---


