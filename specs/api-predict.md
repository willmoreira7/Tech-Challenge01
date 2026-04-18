# Spec: API de Inferência (FastAPI)

## Endpoints

### `GET /health`

```json
// Response 200
{"status": "ok", "model_version": "1.0.0", "uptime_seconds": 123.4}
```

### `POST /predict`

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
  "model_version": "1.0.0"
}
```

**Erros:**

| Código | Causa |
|--------|-------|
| `422` | Campo ausente ou tipo inválido (Pydantic) |
| `500` | Falha interna no modelo |
| `503` | Modelo não carregado |

## Validações Pydantic

- `gender`: `Literal["Male", "Female"]`
- `SeniorCitizen`: `int` com `ge=0, le=1`
- `tenure`: `int` com `ge=0`
- `MonthlyCharges`: `float` com `gt=0`
- `TotalCharges`: `float` com `ge=0`
- `Contract`: `Literal["Month-to-month", "One year", "Two year"]`

## Middleware de latência

Logar via structlog a cada request:

```python
log.info("api.request", path="/predict", latency_ms=45.2, status=200)
```

## SLOs

- Latência p50 < 100ms
- Latência p99 < 500ms
- Uptime > 99.5%

## Startup

Carregar modelo e pipeline no `lifespan` (FastAPI), não por request:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.model = load_model("models/mlp_best.pt")
    app.state.pipeline = joblib.load("models/pipeline.pkl")
    yield
```

## Testes esperados

- `test_health_returns_ok` — GET /health → 200
- `test_predict_valid_payload` — POST /predict → 200 com probability 0-1
- `test_predict_invalid_payload` — payload sem `tenure` → 422
- `test_predict_latency` — resposta em < 200ms
