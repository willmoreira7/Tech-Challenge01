---
name: test-api
description: Executa smoke tests e validações da API FastAPI
---

Execute a bateria de testes da API:

1. Verifique que a API está rodando: `GET /health` deve retornar `{"status": "ok"}`
2. Smoke test do endpoint principal:

```json
POST /predict
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

3. Teste de validação Pydantic — envie payload inválido e espere `422`
4. Teste de campo ausente — remova `tenure` e espere `422`
5. Verifique que a resposta contém: `churn_probability` (float 0-1) e `churn_predicted` (bool)
6. Meça latência: p50 deve ser < 100ms

Reporte qualquer falha com o erro exato e o campo problemático.
