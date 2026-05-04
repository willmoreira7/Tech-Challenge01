# API de Inferência - Guia de Implementação

## 📁 Estrutura Criada

### Arquivos Principais (src/api/)

1. **schemas.py** - Modelos Pydantic para validação
   - `PredictRequest` - Schema para predição individual
   - `PredictResponse` - Response para predição individual
   - `PredictBatchRequest` - Schema para batch
   - `PredictBatchResponse` - Response para batch
   - `HealthResponse` - Response do health check
   - `RootResponse` - Response da rota raiz
   - `ErrorResponse` - Schema de erros

2. **utils.py** - Utilitários e middleware
   - `RateLimitMiddleware` - Rate limit (10 req/30s por IP)
   - `LoggingMiddleware` - Logging estruturado com structlog
   - `load_model()` - Carrega modelo PyTorch
   - `load_pipeline()` - Carrega pipeline scikit-learn
   - `get_lifespan()` - Context manager para startup/shutdown

3. **handlers.py** - Lógica dos endpoints
   - `handle_root()` - GET /
   - `handle_health()` - GET /health
   - `handle_predict()` - POST /api/v1/predict
   - `handle_predict_batch()` - POST /api/v1/predict_batch
   - Inclui tratamento de erros e logging

4. **app.py** - Aplicação FastAPI
   - Configuração de middleware
   - Registro de rotas
   - Lifespan management
   - Logging estruturado

5. **__init__.py** - Exports públicos do pacote

### Testes (tests/integration/)

- **conftest.py** - Fixtures pytest
  - `client` - Cliente HTTP para testes
  - `valid_predict_payload` - Payload válido
  - `valid_batch_payload` - Batch válido

- **test_api_root_health.py** - Testes para GET / e GET /health
  - 7 testes de validação

- **test_api_predict.py** - Testes para POST /api/v1/predict
  - 10 testes de validação e edge cases

- **test_api_predict_batch.py** - Testes para POST /api/v1/predict_batch
  - 11 testes de validação e constraintsválida

- **test_api_errors.py** - Testes para error handling e rate limit
  - Rate limit tests
  - Error handling tests

### Configuração (src/config.py)

- `configure_logging()` - Configuração de structlog

## 🚀 Como Executar

### Instalação de Dependências

```bash
pip install fastapi uvicorn pydantic structlog torch scikit-learn joblib pandas numpy
```

### Rodar a API Localmente

```bash
# Com reload (desenvolvimento)
uvicorn src.api.app:app --reload --port 8000

# Ou usando task
task api
```

### Acessar a Documentação

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Rodar os Testes

```bash
# Instalar pytest
pip install pytest pytest-asyncio

# Rodar testes
pytest tests/integration/ -v

# Com coverage
pytest tests/integration/ -v --cov=src/api
```

## 📋 Endpoints Implementados

### GET /
**Informações da API**
```bash
curl http://localhost:8000/
```

Response:
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

### GET /health
**Health check do serviço**
```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "ok",
  "model_version": "1.0.0",
  "uptime_seconds": 123.45,
  "timestamp": "2026-05-03T15:45:30Z"
}
```

### POST /api/v1/predict
**Predição individual**
```bash
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{
    "gender": "Male",
    "SeniorCitizen": 0,
    "Partner": "Yes",
    ...
  }'
```

Response:
```json
{
  "churn_probability": 0.823,
  "churn_predicted": true,
  "model_version": "1.0.0",
  "processing_time_ms": 45.2
}
```

### POST /api/v1/predict_batch
**Predição em batch**
```bash
curl -X POST http://localhost:8000/api/v1/predict_batch \
  -H "Content-Type: application/json" \
  -d '{
    "records": [
      {...},
      {...}
    ]
  }'
```

Response:
```json
{
  "batch_id": "batch_20260503_154530",
  "predictions": [
    {
      "record_index": 0,
      "churn_probability": 0.823,
      "churn_predicted": true
    }
  ],
  "model_version": "1.0.0",
  "total_records": 1,
  "processing_time_ms": 78.5
}
```

## 🛡️ Características Implementadas

### ✅ Validação Pydantic
- 19 campos com constraints (Literal, ge, le)
- Type checking automático
- Response codes 422 para validação inválida

### ✅ Rate Limiting
- 10 requisições por 30 segundos por IP
- Response 429 com retry_after
- Cleanup automático de timestamps expirados

### ✅ Logging Estruturado (structlog)
- Logging de requests com path, method, timestamp
- Logging de responses com status, latency_ms
- Logging de erros com contexto
- Nenhum uso de print()

### ✅ Middleware
- RateLimitMiddleware: Rate limiting
- LoggingMiddleware: Request/response logging
- Configurável no startup

### ✅ Lifespan Management
- Carregamento de modelo e pipeline no startup
- Limpeza no shutdown
- Error handling se modelo não carregar

### ✅ Error Handling
- 400: Batch size inválido
- 422: Validação Pydantic
- 429: Rate limit
- 500: Erro no modelo
- 503: Modelo não carregado
- 504: Timeout (configurável)

### ✅ SLOs Definidos
- p50 (single) < 100ms
- p99 (single) < 500ms
- p50 (batch ≤ 1k) < 5s
- Uptime > 99.5%

## 🧪 Testes Inclusos

**Total: 39 testes**

- ✅ 7 testes para root e health
- ✅ 10 testes para predict single
- ✅ 11 testes para predict batch
- ✅ 11 testes para error handling e rate limit

### Cobertura de Testes

- ✅ Schemas válidos
- ✅ Campos obrigatórios
- ✅ Validação de tipos
- ✅ Constraints numéricos
- ✅ Literals e enums
- ✅ Rate limiting
- ✅ Edge cases (batch vazio, excesso)
- ✅ Error handling

## 📝 Convenções Seguidas

- ✅ RANDOM_SEED = 42 (em handlers.py)
- ✅ Estrutlog (sem print())
- ✅ Sintaxe Python válida (validada com ast.parse)
- ✅ Tipo hints completos
- ✅ Docstrings em todos os handlers
- ✅ Comentários em linhas críticas

## 🔌 Integrações

- **PyTorch**: Carregamento de modelo com `torch.load()`
- **scikit-learn**: Pipeline de preprocessamento com `joblib.load()`
- **Pydantic v2**: Validação de schemas
- **FastAPI**: Framework assíncrono
- **structlog**: Logging estruturado
- **pytest**: Framework de testes

## 📦 Dependências

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
    "pandas>=2.0",
    "numpy>=1.24.0",
]

[dependency-groups]
dev = [
    "pytest>=9.0.3",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=7.0",
]
```

## 🎯 Próximos Passos

1. **Deploy**: Usar Docker (Dockerfile fornecido na spec)
2. **Monitoria**: Implementar métricas SLO com prometheus
3. **Testes de Carga**: Validar performance com locust
4. **CI/CD**: Adicionar pipeline de testes automáticos
5. **Documentação API**: Gerar OpenAPI schema

## 📚 Referências

- Spec completa: [specs/inference-api.md](../specs/inference-api.md)
- Convenções: [docs/conventions.md](conventions.md)
- Modelo card: [docs/model_card.md](model_card.md)
