---
name: test-api
description: Executa smoke tests e validações da API FastAPI. Usar quando quiser verificar se a API está funcionando, após mudanças em src/api/ ou após novo deploy.
---

Consulte `specs/inference-api.md` para o contrato completo.

## Estado atual

API implementada em `src/api/`. 51 testes de integração em `tests/integration/`.

## Rodar a suíte completa

```bash
make test
# ou só integração:
uv run pytest tests/integration/ -v
```

## Endpoints implementados

| Método | Path | Response |
|--------|------|----------|
| GET | `/` | `RootResponse` — info da API |
| GET | `/health` | `HealthResponse` — status + uptime |
| POST | `/api/v1/predict` | `PredictResponse` — predição individual |
| POST | `/api/v1/predict_batch` | `PredictBatchResponse` — batch (máx 10k) |

## Payload de referência

```json
{
  "gender": "Male", "SeniorCitizen": 0, "Partner": "Yes", "Dependents": "No",
  "tenure": 12, "PhoneService": "Yes", "MultipleLines": "No phone service",
  "InternetService": "Fiber optic", "OnlineSecurity": "No",
  "OnlineBackup": "No", "DeviceProtection": "No", "TechSupport": "No",
  "StreamingTV": "No", "StreamingMovies": "No", "Contract": "Month-to-month",
  "PaperlessBilling": "Yes", "PaymentMethod": "Electronic check",
  "MonthlyCharges": 70.35, "TotalCharges": 844.20
}
```

## Checklist de smoke test manual

```bash
# 1. Sobe a API localmente
make run

# 2. Health check
curl http://localhost:8000/health

# 3. Predição individual
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{"gender":"Male","SeniorCitizen":0,"Partner":"Yes","Dependents":"No","tenure":12,"PhoneService":"Yes","MultipleLines":"No phone service","InternetService":"Fiber optic","OnlineSecurity":"No","OnlineBackup":"No","DeviceProtection":"No","TechSupport":"No","StreamingTV":"No","StreamingMovies":"No","Contract":"Month-to-month","PaperlessBilling":"Yes","PaymentMethod":"Electronic check","MonthlyCharges":70.35,"TotalCharges":844.20}'

# 4. Payload inválido → deve retornar 422
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{"gender": "Male"}'
```

## SLOs

- `p50 < 100ms` · `p99 < 500ms` · uptime `> 99.5%`
- Rate limit: 10 req/30sec por IP → 429

Se falhar na inicialização, verifique se `models/mlp_best.pt` e `models/pipeline.pkl` existem (rode `make train` antes).
