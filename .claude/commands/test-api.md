---
name: test-api
description: Executa smoke tests e validações da API FastAPI
---

Implemente e execute seguindo **exatamente** `specs/api-predict.md`.

Se `src/api/` ainda não existir, crie conforme `specs/api-predict.md`:
- `GET /health` → `{"status": "ok", "model_version": "1.0.0", "uptime_seconds": float}`
- `POST /predict` → `{"churn_probability": float, "churn_predicted": bool, "model_version": "1.0.0"}`
- Schema Pydantic `PredictRequest` com validações dos campos (conforme spec)
- Middleware de latência via structlog
- Modelo e pipeline carregados no `lifespan` (não por request)

Execute a bateria de testes (conforme `specs/api-predict.md`):

1. `test_health_returns_ok` — `GET /health` → 200
2. `test_predict_valid_payload` — `POST /predict` com payload completo → 200, `churn_probability` entre 0 e 1
3. `test_predict_invalid_payload` — payload sem `tenure` → 422
4. `test_predict_latency` — resposta em < 200ms

Payload de referência para testes:
```json
{
  "gender": "Male", "SeniorCitizen": 0, "Partner": "Yes", "Dependents": "No",
  "tenure": 12, "PhoneService": "Yes", "MultipleLines": "No",
  "InternetService": "Fiber optic", "OnlineSecurity": "No",
  "OnlineBackup": "No", "DeviceProtection": "No", "TechSupport": "No",
  "StreamingTV": "No", "StreamingMovies": "No", "Contract": "Month-to-month",
  "PaperlessBilling": "Yes", "PaymentMethod": "Electronic check",
  "MonthlyCharges": 70.35, "TotalCharges": 844.20
}
```

SLOs (conforme spec): p50 < 100ms · p99 < 500ms · uptime > 99.5%
Logging via structlog — sem print().
