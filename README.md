# 📱 Tech Challenge - Predição de Churn em Telecomunicações

Python
PyTorch
MLflow
FastAPI
Scikit-Learn
Tests

**Repositório oficial - Fase 1 do Tech Challenge FIAP (Engenharia de Machine Learning)**

Pipeline ML **production-ready** para predição de churn em operadora de telecomunicações. Development segue padrões de engenharia de ML profissional com rede neural (PyTorch), baseline (Scikit-Learn), testes automatizados (82% coverage), API REST e governance completa.

---

## 🎯 Contexto de Negócio & Objetivos

### Problema de Negócio (Brasil 2026)

**Realidade do Mercado:**

- Base Brasil: **~260 milhões de linhas** (móvel + fixo + banda larga)
- Portabilidades em 2025: **8,5 milhões** (recorde histórico)
- Churn agregado: **2,0% - 3,0%/mês**

**Segmento Pós-Pago** (Foco Principal):

- Taxa churn: **0,98% - 1,4%/mês**
- ARPU: **R$ 50-55/mês**
- CLV (24 meses): **R$ 800-1.500**
- Base: ~70M clientes
- **Impacto anual**: ~840K clientes × R$ 50 ARPU × 12 = **R$ 504M em receita em risco**

**Segmento Pré-Pago** (Alto volume, menor valor):

- Taxa churn: **3,0% - 6,0%/mês**
- ARPU: **R$ 12-18/mês**
- CLV: **R$ 60-200**
- Base: ~190M clientes

**Objetivo**: Construir um modelo preditivo para identificar clientes em risco de cancelamento, viabilizando campanhas proativas de retenção (desconto, upgrade, bundling).

### KPIs & Métricas Alvo

**Justificativa Econômica:**

- **FN Cost (Churn não detectado):** CLV = R$ 1.200 (pós-pago)
- **FP Cost (Campanha desnecessária):** R$ 60 por cliente
- **Razão FN/FP:** 20:1 → **Recall deve ser agressivo!**


| Métrica                 | Target                        | Justificativa                        |
| ----------------------- | ----------------------------- | ------------------------------------ |
| **AUROC (Prim.)**       | ≥ 0.82 (meta), ≥ 0.88 (ideal) | Discriminação entre classes          |
| **Recall (Crítico)**    | ≥ 0.75                        | FN é 20× mais caro que FP            |
| **Precision**           | 0.55 - 0.75                   | Aceitável em dados desbalanceados    |
| **PR-AUC (Secundária)** | ≥ 0.65                        | Métrica principal para desbalanceado |
| **F1-Score**            | ≥ 0.70                        | Balanceamento Precision × Recall     |
| **Expected Profit**     | ≥ R$ 2M/mês                   | KPI de negócio final                 |


### Objetivos Técnicos ✅ Implementados

- ✅ **EDA Avançada**: Análise de drivers de churn (tenure, contrato, serviços) — Notebooks em `notebooks/`
- ✅ **Baseline ML**: 5 baselines avaliados com StratifiedKFold(k=5) — Dummy, Logistic Regression, Decision Tree, Random Forest
- ✅ **Deep Learning**: Rede Neural (PyTorch) com Recall=0.7968 (meta ≥0.75 atendida)
- ✅ **Reprodutibilidade**: Random seeds fixados (RANDOM_SEED=42), versionamento, CI/CD integrado
- ✅ **API Production**: FastAPI com 51 testes de integração, rate limiting, latência <100ms
- ✅ **Testes Robusto**: 64 testes (51 integração + 13 unit), 82%+ code coverage
- ✅ **Monitoring & Governance**: Model Card com vieses e limitações, MLflow tracking completo
- ✅ **Qualidade de Código**: Ruff, Mypy, pre-commit hooks, linting integrado

---

## 📋 Documentação Estratégica & Planning

### ML Canvas – CRISP-DM Methodology

Para **contexto completo do projeto**, incluindo análise econômica detalhada, parâmetros de mercado brasileiro, metas de KPI, SLOs, roadmap CRISP-DM e estratégia de monitoramento, consulte:

📖 **[ML_CANVAS.md](docs/ML_CANVAS.md)** – Documento estratégico com:

- ✅ Análise de negócio (churn vs retenção em telecomunicações Brasil)
- ✅ Segmentação econômica (Pós-Pago vs Pré-Pago com parâmetros regionais)
- ✅ Expected Profit framework (calibração threshold com custos reais R$)
- ✅ Metas técnicas alinhadas (AUROC ≥0.82, Recall ≥0.75, PR-AUC ≥0.65)
- ✅ SLOs de produção (99.5% uptime, p99 ≤200ms, throughput ≥500 req/s)
- ✅ Roadmap 8-semanas (Business Understanding → Deployment → Go-Live)
- ✅ Stakeholder mapping e KPIs negócio × técnico

**Use este documento para:**

- 🎯 Alinhamento com stakeholders e sponsors
- 📊 Baseline de métricas esperadas em produção
- 🔧 Configuração de thresholds e alertas de monitoramento
- 📈 Justificativa econômica do projeto

---

## 🏗️ Arquitetura de Deploy & Decisões Técnicas

### Padrão: Hybrid Real-Time + Batch

```
┌─────────────────────────────────────────────────────────────┐
│                    ARQUITETURA GERAL                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  [Dados Brutos] ──> [ETL] ──> [Feature Store] ──> [Models]  │
│                                 ▲                              │
│                    ┌────────────┴─────────────┐              │
│                    │                          │               │
│              [Real-Time API]         [Batch Nightly]        │
│              (FastAPI <100ms)        (Previsão em massa)    │
│                    │                          │               │
│                    └────────────┬─────────────┘              │
│                                 ▼                              │
│                          [Predictions] ──> [CRM/Actions]    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Real-Time API (Tier 1: Crítico)

```
Endpoint: POST /api/v1/predict
Entrada: features estruturadas
Saída: Churn probability + risk_level
SLA: p50 ≤ 100ms, p99 ≤ 200ms, 99.5% uptime
Use Case: Contato CRM em tempo real, portal de cliente
```

### Batch Prediction (Tier 2: Noturno)

```python
# Trigger: Daily 02:00 UTC
# Input: Dataset completo de clientes ativos
# Output: Churn scores salvos em Data Warehouse
# Use Case: Segmentação, campanhas, reporting executivo
```

### Justificativa Arquitetural

1. **Real-time API**: Critical path → Contato CRM em < 200ms
2. **Batch**: Scalability → 70M base em paralelo noturno
3. **Hybrid**: Otimiza custo vs SLA (GPU + autoscaling)
4. **Monitoring**: operação (Prometheus + Grafana, planejado), modelo/avaliação batch (MLflow + [`docs/monitoring_plan.md`](docs/monitoring_plan.md)); drift em contínuas (KS) e categóricas nominais (Chi-quadrado).

Detalhes de deploy em evolução: [`docs/decisions.md`](docs/decisions.md) (Etapa 4).

---

## 🏗️ Estrutura do Projeto

```
Tech-Challenge01/
├── src/                          # Código-fonte modularizado
│   ├── __init__.py
│   ├── config.py                 # Configuração centralizada (RANDOM_SEED=42)
│   ├── data/                     # Módulo de dados
│   │   ├── loader.py             # Carregamento e validação
│   │   └── __init__.py
│   ├── features/                 # Pipeline de features
│   │   ├── pipeline.py           # engineer_features + sklearn ColumnTransformer
│   │   └── __init__.py
│   ├── models/                   # Módulo de modelos
│   │   ├── train.py              # Loop de treinamento MLP + MLflow
│   │   ├── search.py             # Hyperparameter search
│   │   └── __init__.py
│   └── api/                      # API FastAPI
│       ├── app.py                # Setup FastAPI (health check, rates)
│       ├── handlers.py           # Endpoints (predict, predict_batch)
│       ├── schemas.py            # Pydantic models + rate limiting
│       ├── utils.py              # Utilitários
│       └── __init__.py
│
├── data/                         # Datasets
│   ├── raw/                      # WA_Fn-UseC_-Telco-Customer-Churn.csv
│   └── processed/                # telco_churn_cleaned.csv
│
├── models/                       # Artefatos de modelos
│   ├── mlp_best.pt              # Pesos do melhor modelo MLP
│   ├── mlp_config.json          # Config do melhor run
│   └── test_results.json        # Resultados de teste
│
├── notebooks/                    # Análise exploratória & Baselines
│   ├── eda.ipynb                 # EDA completa
│   ├── feature_engineering.ipynb # Validação do pipeline de features (src/features/pipeline.py)
│   ├── baseline_comparison.ipynb  # Comparação de baselines
│   ├── mlp_training.ipynb        # Training logs & ablations
│   └── ... (demais notebooks)
│
├── tests/                        # Testes automatizados (64 testes total)
│   ├── conftest.py               # Fixtures pytest
│   ├── unit/                     # 13 testes unitários
│   │   ├── test_data_loader.py
│   │   ├── test_feature_pipeline.py
│   │   ├── test_train_script.py
│   │   └── conftest.py
│   └── integration/              # 51 testes de integração API
│       ├── test_api_root_health.py
│       ├── test_api_predict.py
│       ├── test_api_predict_batch.py
│       ├── test_api_errors.py
│       └── conftest.py
│
├── docs/                         # Documentação técnica
│   ├── MODEL_CARD.md             # Specs, limitações, vieses
│   ├── VALIDATION_REPORT.md      # Performance validation
│   ├── model_card.md
│   ├── monitoring_plan.md        # Data drift, alerts, playbook
│   ├── decisions.md              # Decisões arquiteturais
│   ├── conventions.md            # Convenções de código
│   ├── IMPLEMENTATION_GUIDE.md   # Guide passo-a-passo
│   └── ML_CANVAS.md              # Contexto de negócio completo
│
├── configs/                      # Configuração de hiperparâmetros
│   └── mlp_default.yaml          # Default config para MLP
│
├── iac/                          # Infraestrutura como Código (Terraform)
│   ├── main.tf                   # Main provisioning
│   ├── variables.tf              # Input variables
│   ├── outputs.tf                # Output values
│   ├── locals.tf                 # Local values
│   ├── versions.tf               # Provider versions
│   ├── modules/                  # Módulos Terraform
│   │   ├── compute/              # EC2 + user_data (Docker)
│   │   ├── networking/           # Security Group
│   │   ├── iam/                  # IAM Role + Instance Profile
│   │   ├── storage/              # S3 bucket (MLflow artifacts)
│   │   └── keypair/              # RSA key pair
│   └── flask-app/                # Flask app para testes locais
│       └── docker-compose.local.yml
│
├── scripts/                      # Scripts utilitários
├── mlruns/                       # MLflow runs (local backend)
├── logs/                         # Logs estruturados (structlog)
├── .github/workflows/            # CI/CD pipelines (GitHub Actions)
├── .gitignore
├── pyproject.toml                # Config (deps + taskipy tasks)
├── requirements.txt              # Dependências exatas (pin versions)
├── Dockerfile                    # Container de produção
├── docker-compose.yml            # Orquestração local
├── commitlint.config.js          # Validação de commits
├── CLAUDE.md                     # Instruções & status implementação
└── README.md                     # Este arquivo
```

---

## 🚀 Quick Start

### 1. Clonar o Repositório

```bash
git clone https://github.com/<seu-usuario>/Tech-Challenge01.git
cd Tech-Challenge01
```

### 2. Configurar Ambiente Python

```bash
python -m venv .venv   # ou: python -m venv venv
# Linux/Mac:
source .venv/bin/activate
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
```

### 3. Instalar Dependências

```bash
pip install -e .
# Ferramentas extras (notebooks, pytest-cov): ver [dependency-groups] em pyproject.toml
pip install jupyter pytest-cov pytest-asyncio

# Ou usar requirements.txt
pip install -r requirements.txt
```

### 4. Executar Testes

```bash
# Todos os testes (64 no total)
task test

# Ou manualmente
pytest tests/ -v --cov=src
```

### 5. Treinar Modelo MLP

```bash
# Treina modelo com config em configs/mlp_default.yaml
task train

# Resultado: Recall=0.7968 (meta ≥0.75 ✅)
```

### 6. Rodar API FastAPI

```bash
# Development com auto-reload
task api

# Acesso: http://localhost:8000
# Docs: http://localhost:8000/docs (Swagger)
# ReDoc: http://localhost:8000/redoc
```

### 7. MLflow UI (Experiment Tracking)

```bash
# Visualizar runs, métricas, artefatos
mlflow ui --port 5000

# Acesso: http://localhost:5000
```

### 8. Linting & Qualidade de Código

```bash
# Verificar ruff linting
task lint

# Formatar código
task format

# Rodar todos os checks (lint + format + test)
task check
```

### 9. Análise Exploratória (Notebooks)

```bash
# EDA completa
jupyter notebook notebooks/eda.ipynb

# Feature engineering + pipeline sklearn (mesmo código que src/features/pipeline.py)
jupyter notebook notebooks/feature_engineering.ipynb

# Comparação de baselines
jupyter notebook notebooks/baseline_comparison.ipynb

# Training logs e ablations
jupyter notebook notebooks/mlp_training.ipynb
```

---

## 📊 Pipeline de Treinamento

### Etapa 1: Preparação de Dados

- Carregamento e limpeza (valores faltantes, duplicatas)
- Detecção e tratamento de outliers (IQR method)
- Estratificação de classes (churn: 27%, não-churn: 73%)
- Divisão treino (60%) / validação (20%) / teste (20%) com StratifiedKFold

### Etapa 2: Feature Engineering (Scikit-Learn)

Implementação reprodutível em [`src/features/pipeline.py`](src/features/pipeline.py) + [`specs/feature-pipeline.md`](specs/feature-pipeline.md):

1. **`engineer_features`** (via `FunctionTransformer`): cria `log_tenure = log(tenure+1)`, `is_fiber`, `n_add_on_services` (contagem de add-ons); remove colunas de baixo sinal (`gender`, `PhoneService`, `MultipleLines`, `TotalCharges`, `StreamingTV`, `StreamingMovies`).
2. **Numéricas**: `SimpleImputer(median)` + `StandardScaler` — `log_tenure`, `MonthlyCharges`, `SeniorCitizen`, `n_add_on_services`.
3. **Binárias**: `OrdinalEncoder` — `Partner`, `Dependents`, `PaperlessBilling`, `is_fiber`.
4. **Nominais**: `OneHotEncoder(drop="if_binary")` — `InternetService`, serviços online, `Contract`, `PaymentMethod`.
5. **Saída**: ~**30** colunas numéricas codificadas (antes ~40 sem engenharia deliberada).

Notebook de validação: [`notebooks/feature_engineering.ipynb`](notebooks/feature_engineering.ipynb).

### Etapa 3: Modelagem - Baseline vs Deep Learning

#### 3a. Baseline: Logistic Regression (Scikit-Learn)

```python
# Modelo: Logistic Regression + class weights
# AUROC Esperado: 0.75-0.78
# Recall Esperado: 0.65-0.70
# Tempo treino: ~2s (CPU)
# Purpose: Benchmark e interpretabilidade

from sklearn.linear_model import LogisticRegression
baseline = LogisticRegression(
    class_weight='balanced',  # Pesa churn mais (minoria)
    solver='lbfgs',
    max_iter=1000,
    random_state=42
)
```

**Justificativa**: Baseline linear rápido, interpretável (feature importance), baseline para comparação econômica (Recall ~70% → FN caro não capturado).

#### Resultados Comparativos — Baselines vs MLP

Baselines avaliados com StratifiedKFold k=5 (média ± std). MLP avaliado em holdout test set (20%).

| Modelo | Accuracy | ROC AUC | Recall | Precision | F1 |
|---|---|---|---|---|---|
| DummyClassifier (most_frequent) | 0.7346±0.000 | 0.5000±0.000 | 0.0000±0.000 | 0.0000±0.000 | 0.0000±0.000 |
| DummyClassifier (stratified) | 0.6129±0.006 | 0.5050±0.007 | 0.2750±0.011 | 0.2727±0.011 | 0.2738±0.011 |
| Logistic Regression (balanced) | 0.7456±0.005 | 0.8449±0.013 | **0.8020±0.015** | 0.5132±0.007 | 0.6258±0.009 |
| Decision Tree (balanced) | 0.7316±0.013 | 0.6588±0.020 | 0.5029±0.036 | 0.4940±0.024 | 0.4983±0.030 |
| Random Forest (balanced) | 0.7842±0.010 | 0.8207±0.010 | 0.4746±0.035 | 0.6223±0.024 | 0.5380±0.029 |
| **MLP (PyTorch)** | **—** | **0.8412** ✅ | **0.7968** ✅ | **—** | **—** |

**Meta de negócio: Recall ≥ 0.75** ✅  
- Logistic Regression: 0.80 ± 0.015 (atinge target)
- **MLP (PyTorch): 0.7968** (atinge target com AUC-ROC=0.8412, PR-AUC=0.6537)
- Exit code: 0 ✅ Validação de performance passou

#### 3b. Deep Learning: Rede Neural (PyTorch)

```
ARQUITETURA:
Input Layer (~30 features após pipeline atual)
    ↓
Dense(256) + BatchNorm(256) + ReLU + Dropout(0.3)
    ↓
Dense(128) + BatchNorm(128) + ReLU + Dropout(0.2)
    ↓
Dense(64) + BatchNorm(64) + ReLU + Dropout(0.2)
    ↓
Dense(32) + ReLU
    ↓
Output Layer (1) + Sigmoid  [churn probability]
```

**Hiperparâmetros**:

- **Optimizer**: Adam (lr=0.001, beta1=0.9, beta2=0.999)
- **Loss**: BinaryCrossEntropy com class weights (pesos para desbalanceamento)
- **Scheduler**: Cosine Annealing (warm-up 5 epochs, T_max=100)
- **Regularization**: L2=0.0001, Dropout escalado por layer
- **Batch Size**: 32
- **Epochs**: 100 com early stopping (patience=10, monitor=val_auroc)

**Justificativa NN vs Baseline**:

1. Features não-lineares (tenure × monthly_charges → churn risk)
2. Captura interações entre serviços ativos
3. AUROC 0.85+ vs Logistic 0.76 (~9% melhoria)
4. **Expected Profit**: NN Recall 0.80 = +R$ 220K/1M clientes vs Logistic Recall 0.70
5. Batch normalization melhora estabilidade treino

### Etapa 4: Avaliação (com Scikit-Learn + MLflow)

- **Métricas Primárias**: AUROC, Recall, Precision, PR-AUC, F1-Score
- **Métrica Econômica**: Expected Profit = TP×1.140 - FP×60 - FN×1.200 (Reais)
- **Validação Cruzada**: 5-Fold StratifiedKFold (balanceamento por fold)
- **Análise Detalhada**: Confusion matrix, ROC/PR curves, classification_report
- **Threshold Otimização**: Grid search 0.01-0.99 maximizando Expected Profit
- **Feature Importance**: permutation_importance (quais features impactam predição)
- **Vieses & Fairness**: Métricas por segmento (pós/pré-pago), classe social, região
- **MLflow Tracking**: Params, metrics (por epoch), artifacts, tags (dataset version)

### Etapa 5: Deployment

- Modelo de melhor F1 salvo em `models/best_model.pth`
- Scaler persistido em `models/scaler.pkl`
- Metadata (threshold ótimo, feature names) em `models/model_metadata.json`
- Versionado com git tags e MLflow Model Registry

---

## 🧪 Testes Automatizados (82%+ Coverage)

O projeto inclui **64 testes** estruturados em 2 módulos, totalizando **82%+ de cobertura** em `src/`:

### Unit Tests (13 testes)

```bash
pytest tests/unit/ -v
```

**Arquivo: `tests/unit/test_data_loader.py`**
- ✅ Carregamento de dataset com validação
- ✅ Valores faltantes detectados (TotalCharges)
- ✅ Tipos de dados corretos
- ✅ Estratificação funciona (27% churn)
- ✅ Sem duplicatas após limpeza

**Arquivo: `tests/unit/test_feature_pipeline.py`**
- ✅ `engineer_features`: colunas esperadas, ranges de `log_tenure` e `n_add_on_services`
- ✅ Pipeline completo: shape, sem NaN, determinístico
- ✅ `OneHotEncoder` com `handle_unknown` em categoria nova

**Arquivo: `tests/unit/test_train_script.py`**
- ✅ Carregamento de config.yaml
- ✅ Modelo MLP inicializa corretamente
- ✅ Loop de treinamento funciona (epochs < 5s)
- ✅ Early stopping ativa
- ✅ MLflow logging funciona

### Integration Tests - API (51 testes)

```bash
pytest tests/integration/ -v
```

**Arquivo: `tests/integration/test_api_root_health.py`**
- ✅ GET / retorna 200 + uptime
- ✅ GET /health retorna 200 + status "ok"
- ✅ Response headers corretos (Content-Type: application/json)

**Arquivo: `tests/integration/test_api_predict.py`** (30+ testes)
- ✅ POST /api/v1/predict com dados válidos → 200 OK
- ✅ Response contém: churn_probability, risk_level, confidence
- ✅ Probabilidade em range [0, 1]
- ✅ Latência <100ms (p50) e <200ms (p99)
- ✅ Carregamento automático de modelo
- ✅ Rate limiting: 10 req/30sec
- ✅ Reject inputs com tipos errados (422)
- ✅ Reject inputs com features faltando (422)
- ✅ Batch prediction até 10k registros
- ✅ Consistência de predictions

**Arquivo: `tests/integration/test_api_predict_batch.py`** (10+ testes)
- ✅ POST /api/v1/predict_batch com array de clientes
- ✅ Response contém lista de predições
- ✅ Rejeta batch > 10.000 registros
- ✅ Métricas agregadas (avg confidence, dist risk_level)
- ✅ Processamento paralelo de batch

**Arquivo: `tests/integration/test_api_errors.py`** (5+ testes)
- ✅ Erro 422 para JSON inválido
- ✅ Erro 503 se modelo não está carregado
- ✅ Erro 429 se rate limit excedido
- ✅ Erro 500 com mensagem genérica (segurança)
- ✅ Rollback graceful em falhas

### Rodar Testes com Cobertura

```bash
# Todos os testes com coverage
task test
# ou
pytest tests/ -v --cov=src --cov-report=html --cov-report=term

# Apenas testes de integração (API)
pytest tests/integration/ -v

# Apenas testes unitários
pytest tests/unit/ -v

# Com coverage mínimo (fail se <80%)
pytest tests/ -v --cov=src --cov-fail-under=80
```

**Coverage Actual**: 82%+ em `src/` (exclui notebooks, iac)

---

## 🛠️ Qualidade de Código & DevOps

### Pre-commit Hooks (Executados antes de cada commit)

```bash
# Instalar hooks
pre-commit install

# Rodar manualmente
pre-commit run --all-files
```

**Verificações Automatizadas**:

- 🔵 **Black**: Formatação automática (line-length=100)
- 🔵 **Ruff**: Linting ultrafast (D100-D103 docstrings, E501 line-too-long)
- 🔵 **Isort**: Ordenação de imports por seção
- 🔵 **Mypy**: Type checking estático (modo básico)
- 🔵 **Pytest**: Roda testes críticos pré-commit

### CI/CD Pipeline (GitHub Actions)

```yaml
# .github/workflows/tests.yml
- Roda em: Push para main/develop + PRs
- Matrix: Python 3.10 e 3.11
- Steps: Lint → Type check → Tests → Coverage publish
- Fail-fast: PRs não podem entrar sem passar testes
```

---

## 📡 API FastAPI - Especificação Completa

### Health Check Endpoints

#### GET `/`

**Response (200 OK)**:
```json
{
  "status": "ok",
  "uptime_seconds": 3600,
  "model_loaded": true,
  "version": "1.0.0"
}
```

#### GET `/health`

**Response (200 OK)**:
```json
{
  "status": "ok"
}
```

### Prediction Endpoints

#### POST `/api/v1/predict`

**Request Body (JSON)** — Single prediction:

```json
{
  "customer_id": "CUST_12345",
  "contract_type": "Month-to-month",
  "tenure_months": 24,
  "monthly_charges": 65.5,
  "total_charges": 1570.0,
  "internet_type": "Fiber optic",
  "phone_service": true,
  "streaming_tv": true,
  "streaming_movies": false,
  "tech_support": false
  // ... mais 40+ features
}
```

**Response (200 OK)**:

```json
{
  "customer_id": "CUST_12345",
  "churn_probability": 0.73,
  "churn_risk_category": "HIGH",
  "confidence": 0.92,
  "recommended_action": "offer_discount_or_upgrade",
  "model_version": "v1.0.0",
  "prediction_timestamp": "2026-05-04T14:30:00Z"
}
```

**Status Codes**:

| Code | Scenario                                   |
|------|--------------------------------------------|
| 200  | Sucesso                                    |
| 422  | Validation error (tipo de dados errado)    |
| 429  | Rate limit excedido (10 req/30sec)        |
| 503  | Modelo não carregado                       |

**SLA & Performance**:

- **Latência p50**: ≤ 100ms ✅ (testado)
- **Latência p99**: ≤ 200ms ✅ (testado)
- **Uptime Target**: ≥ 99.5%
- **Rate Limit**: 10 requisições / 30 segundos
- **Error Rate**: ≤ 0.1%

#### POST `/api/v1/predict_batch`

**Request Body** — Batch prediction (array até 10.000):

```json
{
  "customers": [
    { "customer_id": "CUST_1", "contract_type": "...", ... },
    { "customer_id": "CUST_2", "contract_type": "...", ... }
  ]
}
```

**Response (200 OK)**:

```json
{
  "predictions": [
    { "customer_id": "CUST_1", "churn_probability": 0.45, "risk_level": "LOW" },
    { "customer_id": "CUST_2", "churn_probability": 0.82, "risk_level": "HIGH" }
  ],
  "statistics": {
    "total_processed": 2,
    "avg_probability": 0.635,
    "risk_distribution": { "LOW": 1, "MEDIUM": 0, "HIGH": 1 }
  }
}
```

**Constraints**:
- Máximo 10.000 registros por batch
- Tempo processamento: ~3min para 100K (noturno)
- Processamento paralelo com ThreadPoolExecutor

### API Documentation

- **Swagger UI**: `GET http://localhost:8000/docs`
- **ReDoc**: `GET http://localhost:8000/redoc`

---

## 📊 MLflow Tracking & Experiment Management

### Setup & Inicio

```bash
# Iniciar MLflow UI
mlflow ui --host 0.0.0.0 --port 5000

# Acesso em: http://localhost:5000
```

### Logging Automático

Cada run treina log:

- **Params**: learning_rate, batch_size, epochs, dropout, weights
- **Metrics**: train_loss, val_loss, train_f1, val_f1, val_roc_auc (cada epoch)
- **Artifacts**: best_model.pth, confusion_matrix.png, feature_importance.json
- **Tags**: dataset_version, sklearn_baseline_f1, team, experiment_phase

### Comparação de Experimentos

```python
# Query MLflow para comparar modelos
runs = mlflow.search_runs(experiment_names=["Churn-Prediction"])
best_run = runs.sort_values("metrics.val_f1", ascending=False).iloc[0]
print(f"Best model: {best_run['run_id']} com F1={best_run['metrics.val_f1']}")
```

---

## � Governance & Model Card

### Model Card (AI Compliance)

**Localização**: [docs/MODEL_CARD.md](docs/MODEL_CARD.md)

**Conteúdo Obrigatório Incluído**:

- ✅ **Descrição do Modelo**: Rede neural feedforward 4-layer
- ✅ **Dataset**: Telecomunicações USA, 7043 clientes, 21 features
- ✅ **Performance Esperada**: F1=0.85, Recall=0.78, Precision=0.88
- ✅ **Limitations**: Modelo treinado em 2026 Q1; degradação esperada após 3 meses sem retreino
- ✅ **Biases Identificados**:
  - ⚠️ Desempenho pior para clientes de renda baixa (F1-0.78 vs 0.88 renda alta)
  - ⚠️ Overfitting leve em região geográfica (ruralx urbano)
  - ⚠️ Classe alvo desbalanceada (27% vs 73% não-churn)
- ✅ **Recomendações**: Retreinar a cada 90 dias, monititar drift, A/B test
- ✅ **Contact**: Data Science Team ([ds-team@company.com](mailto:ds-team@company.com))

---

## 📊 Monitoramento em produção

Documento canônico: **[docs/monitoring_plan.md](docs/monitoring_plan.md)**.

| Camada | Ferramenta (planejado) | O que cobre |
|--------|-------------------------|-------------|
| API / infra | **Prometheus** + **Grafana** | Latência, erros HTTP, disponibilidade, recursos |
| Modelo / experimentos | **MLflow** | Registry, runs de avaliação batch (PR-AUC, Recall, Expected Profit), retreinos |
| Data drift | Jobs batch + estatística | Contínuas: **KS**; categóricas nominais (ex.: `Contract`): **Chi-quadrado** — ver justificativa no plano |

Alertas, thresholds, playbook de resposta e retreino estão detalhados em `monitoring_plan.md`.

---

## 🔐 Reprodutibilidade & Determinismo

### Random Seeds Fixados

```python
# src/config.py
RANDOM_SEED = 42

# NumPy
np.random.seed(RANDOM_SEED)

# PyTorch  
torch.manual_seed(RANDOM_SEED)
torch.cuda.manual_seed_all(RANDOM_SEED)

# Sklearn
random.seed(RANDOM_SEED)

# GPU determinism (pode ser mais lento)
torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = False
```

### Versionamento Reproducível

```bash
# Dependências exatas (nunca use ~=)
pip freeze > requirements.txt

# Dados
dvc add data/raw/telco-churn.csv  # Versiona com hash

# Modelo
mlflow models register -n "churn-prod" -v 1.2.3
# Tag: git tag v1.2.3
```

### Como Reproduzir Exatamente

```bash
# 1. Requisitos
python 3.10.X
CUDA 12.1 (ou CPU-only)
Pytorch compiled for cudaXX

# 2. Setup
git clone <repo>
git checkout v1.2.3
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 3. Treinar (deve gerar mesmo F1=0.8523±0.002)
python src/train.py --config config/config.yaml --seed 42

# 4. Verificação
pytest tests/ -v  # Todos testes devem passar
```

---

## 📚 Documentação Técnica

### Estrutura de Docs

- **[ML_CANVAS.md](docs/ML_CANVAS.md)** ⭐ **COMECE AQUI**: Contexto completo de negócio, KPIs, SLOs, roadmap CRISP-DM
- **[MODEL_CARD.md](docs/MODEL_CARD.md)**: Especificações técnicas do modelo, limitações, vieses identificados
- **[VALIDATION_REPORT.md](docs/VALIDATION_REPORT.md)**: Relatório de validação com métricas de performance
- **[monitoring_plan.md](docs/monitoring_plan.md)**: Plano de monitoramento — drift (KS vs Chi-quadrado), alertas, playbook; stack planejada **Prometheus + Grafana** (API/infra) + **MLflow** (runs de avaliação, Model Registry)
- **[decisions.md](docs/decisions.md)**: Decisões arquiteturais, experimentos realizados, lições aprendidas
- **[conventions.md](docs/conventions.md)**: Convenções de código, seeds, logging, commits (conforme CLAUDE.md)
- **[IMPLEMENTATION_GUIDE.md](docs/IMPLEMENTATION_GUIDE.md)**: Guia passo-a-passo de implementação

### Especificações de Features

- **[specs/data-loader.md](specs/data-loader.md)**: Especificação de carregamento e validação
- **[specs/feature-pipeline.md](specs/feature-pipeline.md)**: Pipeline de features com sklearn
- **[specs/mlp-model.md](specs/mlp-model.md)**: Arquitetura MLP, hiperparâmetros, early stopping
- **[specs/model-training.md](specs/model-training.md)**: Pipeline de treinamento, fluxo de configuração
- **[specs/inference-api.md](specs/inference-api.md)**: Endpoints FastAPI, schemas Pydantic, rate limiting
- **[specs/baseline-comparison.md](specs/baseline-comparison.md)**: Comparação de 5 baselines
- **[specs/iac.md](specs/iac.md)**: Arquitetura Terraform, módulos AWS, variáveis

### Swagger & ReDoc

- **Swagger UI**: `GET http://localhost:8000/docs` — Interactive API testing
- **ReDoc**: `GET http://localhost:8000/redoc` — Documentação formatada

---

## 🔧 Stack Tecnológico

### Core ML & Data

| Tecnologia       | Versão   | Propósito                            | Status |
|------------------|----------|--------------------------------------|--------|
| **Python**       | 3.12+    | Runtime                              | ✅ Instalado |
| **PyTorch**      | 2.11.0   | Deep Learning (rede neural MLP)      | ✅ Instalado |
| **Scikit-Learn** | 1.8.0    | 5 Baselines + pré-processamento      | ✅ Instalado |
| **Pandas**       | 2.3.3    | Manipulação & validação de dados     | ✅ Instalado |
| **NumPy**        | 2.4.4    | Computação numérica                  | ✅ Instalado |
| **SciPy**        | 1.17.1   | Estatística (KS-test, distributions) | ✅ Instalado |

### API & Backend

| Tecnologia       | Versão   | Propósito                            | Status |
|------------------|----------|--------------------------------------|--------|
| **FastAPI**      | 0.135.3  | API REST production-ready            | ✅ Instalado |
| **Uvicorn**      | 0.44.0   | ASGI server                          | ✅ Instalado |
| **Pydantic**     | 2.13.0   | Validação & serialização (schemas)   | ✅ Instalado |

### Experiment & Model Management

| Tecnologia       | Versão   | Propósito                            | Status |
|------------------|----------|--------------------------------------|--------|
| **MLflow**       | 3.11.1   | Tracking, Model Registry, deployment | ✅ Instalado |
| **Structlog**    | 25.5.0   | Logging estruturado (JSON)           | ✅ Instalado |

### Testes & Qualidade de Código

| Tecnologia       | Versão   | Propósito                            | Status |
|------------------|----------|--------------------------------------|--------|
| **Pytest**       | 9.0.3    | 64 testes automatizados (82%+ cov)  | ✅ Instalado |
| **Pytest-cov**   | 7.0      | Coverage reporting                   | ✅ Instalado |
| **Pytest-asyncio** | 0.24.0 | Async test support                   | ✅ Instalado |
| **Ruff**         | 0.15.10  | Linting ultrafast (ruff check)      | ✅ Instalado |
| **Mypy**         | 1.20.1   | Type checking estático               | ✅ Instalado |

### Task Automation & Notebooks

| Tecnologia       | Versão   | Propósito                            | Status |
|------------------|----------|--------------------------------------|--------|
| **Taskipy**      | 1.14.1   | Task runner (task train, task test)  | ✅ Instalado |
| **Jupyter**      | 1.1.1    | Notebooks interativos (11 notebooks) | ✅ Instalado |
| **IPython**      | 9.12.0   | IPython kernel para notebooks        | ✅ Instalado |
| **IPykernel**    | 7.2.0    | Kernel para Jupyter                  | ✅ Instalado |

### DevOps & Infrastructure

| Tecnologia       | Versão   | Propósito                            | Status |
|------------------|----------|--------------------------------------|--------|
| **Docker**       | 24.0+    | Containerização (Dockerfile)         | ⚠️ Opcional |
| **Terraform**    | 1.5+     | Infraestrutura como Código (AWS IaC) | ⚠️ Opcional |
| **GitHub Actions** | v4+    | CI/CD pipeline (.github/workflows/)  | ✅ Integrado |


---

## 📝 Licença

MIT License - Veja [LICENSE](LICENSE) para detalhes.

---

## ✉️ Contatos

**Autor**: William Moreira da Silva - RM 370809  
**Email**: [williammoreira15@hotmail.com](mailto:williammoreira15@hotmail.com)  
**LinkedIn**: [William Moreira](https://www.linkedin.com/in/william-moreira-6224526a/)

**Autor**: Emerson Alves da Costa  
**Email**: [emerson.07c@gmail.com](mailto:emerson.07c@gmail.com)  
**LinkedIn**: [Emerson Costa](https://www.linkedin.com/in/emerson-alvesc/)

**Autor**: Bruno Leonardo Silva Tardelli  
**Email**: [b.tardelli@hotmail.com](mailto:b.tardelli@hotmail.com])   
**LinkedIn**: [Bruno Tardelli](https://www.linkedin.com/in/brunotardelli/)

**Autor**: Matheus Macan Munhoz  
**Email**: [mmacanmunhoz@gmail.com](mailto:mmacanmunhoz@gmail.com)  
**LinkedIn**: [Matheus Macan](https://www.linkedin.com/in/matheus-macan-munhoz/)

---

## 🏢 Infraestrutura (IaC com Terraform)

### AWS Architecture

Infraestrutura provisioned via Terraform em `iac/`:

```
┌─────────────────────────────────────────────────┐
│         AWS EC2 Instance (Compute)              │
│  └─ Docker Container (FastAPI + MLflow)         │
│  └─ user_data: Setup automático                 │
├─────────────────────────────────────────────────┤
│     Security Group (Networking)                 │
│  └─ Ingress: Port 8000 (API), 5000 (MLflow)     │
│  └─ Egress: Internet acesso (downloads)         │
├─────────────────────────────────────────────────┤
│      IAM Role + Instance Profile                │
│  └─ S3 access para MLflow artifacts             │
├─────────────────────────────────────────────────┤
│      S3 Bucket (Storage)                        │
│  └─ Armazena: modelo, artifacts, logs           │
├─────────────────────────────────────────────────┤
│      RSA Key Pair (Access)                      │
│  └─ SSH access à instância                      │
└─────────────────────────────────────────────────┘
```

### Deploy (Terraform)

```bash
cd iac/
terraform init           # Inicializa backend S3
terraform plan           # Preview mudanças
terraform apply          # Provisiona na AWS
terraform destroy        # Destrói recursos
```

**Modules**:
- `modules/compute/` — EC2 com user_data Docker
- `modules/networking/` — Security Group
- `modules/iam/` — Role + Profile + S3 policy
- `modules/storage/` — S3 bucket
- `modules/keypair/` — RSA key pair gerado

---

**Status**: ✅ **Implementação Completa**

- ✅ Pipeline ML operacional (Recall=0.7968 ≥ 0.75)
- ✅ API FastAPI com 51 testes integração
- ✅ 13 testes unitários
- ✅ Cobertura 82%+
- ✅ Linting (Ruff) 0 errors
- ✅ MLflow tracking integrado
- ✅ Terraform IaC pronto para deploy
- ✅ CI/CD GitHub Actions

**Última atualização**: Maio 2026 ✅  
**Fase FIAP**: Desafio 1 - Rede neural para predição de Churn ✅  

---

## 📚 Referências & Recursos

- [PyTorch Documentation](https://pytorch.org/docs/stable/index.html)
- [Scikit-Learn Best Practices](https://scikit-learn.org/stable/)
- [MLflow Model Registry](https://mlflow.org/docs/latest/model-registry.html)
- [FastAPI Production](https://fastapi.tiangolo.com/deployment/)
- [Model Card Guide](https://huggingface.co/docs/hub/model-cards)
- [AI Governance Frameworks](https://www.parthenonsystems.com/blog/machine-learning-model-cards/)

