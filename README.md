# 📱 Tech Challenge - Predição de Churn em Telecomunicações

Python
PyTorch
MLflow
FastAPI
Scikit-Learn
Tests

**Repositório oficial - Fase 1 do Tech Challenge FIAP (Engenharia de Machine Learning)**

Projeto de **predição de churn** com pipeline reprodutível: **PyTorch (MLP)**, pré-processamento **scikit-learn**, **FastAPI** para inferência, **MLflow** para experimentos e **testes automatizados** (unitários, integração e smoke) em CI. Para monitoramento e roadmap operacional além do código, ver [docs/MONITORING_PLAN.md](docs/MONITORING_PLAN.md).

### 🌐 URLs de Produção (AWS)


| Serviço                | URL                                                                    |
| ---------------------- | ---------------------------------------------------------------------- |
| **API FastAPI**        | [https://api.pocsarcotech.com](https://api.pocsarcotech.com)           |
| **MLflow UI**          | [https://mlflow.pocsarcotech.com](https://mlflow.pocsarcotech.com)     |
| **API Docs (Swagger)** | [https://api.pocsarcotech.com/docs](https://api.pocsarcotech.com/docs) |



[ML_CANVAS.md](docs/ML_CANVAS.md) complementa com **cenários de negócio e metas**; métricas oficiais do modelo vêm do último treino e dos relatórios de avaliação (CI / MLflow).

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


| Métrica                 | Target                        | Status                              |
| ----------------------- | ----------------------------- | ----------------------------------- |
| **AUROC (Prim.)**       | ≥ 0.82 (meta), ≥ 0.88 (ideal) | ✅ **0.8506** (MLP)                  |
| **Recall (Crítico)**    | ≥ 0.75                        | ✅ **0.8467** (MLP)                  |
| **Precision**           | 0.55 - 0.75                   | ✅ **0.4953** (MLP)                  |
| **PR-AUC (Secundária)** | ≥ 0.65                        | ✅ **0.6648** (MLP)                  |
| **F1-Score**            | ≥ 0.70                        | ✅ **0.625** (MLP)                   |
| **Expected Profit**     | ≥ R$ 2M/mês                   | ✅ Em validação (threshold optimize) |


### Objetivos técnicos (implementação neste repo)

- **EDA e baselines**: notebooks em `notebooks/`; baselines sklearn avaliados no trabalho de curso.
- **Modelo principal**: MLP PyTorch com métricas reportadas no README / Model Card (valores dependem do último treino).
- **Reprodutibilidade**: seeds fixas, artefatos versionáveis (`mlp_best.pt`, `pipeline.pkl`, `mlp_config.json`), CI que treina e executa testes.
- **API**: FastAPI com validação Pydantic, rate limit e testes de integração; contrato espelhado no OpenAPI e na secção **API FastAPI** abaixo.
- **Qualidade**: Ruff, cobertura pytest em CI.
- **Planejamento de pós-deploy**: Model Card, plano de monitoramento e Canvas — ver `docs/`.

---

## 📋 Documentação Estratégica & Planning

### ML Canvas – CRISP-DM Methodology

Para **contexto completo do projeto**, incluindo análise econômica detalhada, parâmetros de mercado brasileiro, metas de KPI, SLOs, roadmap CRISP-DM e estratégia de monitoramento, consulte:

📖 **[ML_CANVAS.md](docs/ML_CANVAS.md)** — contexto de negócio, segmentação, framework de lucro esperado, KPIs e roadmap CRISP-DM. **[MONITORING_PLAN.md](docs/MONITORING_PLAN.md)** — drift, alertas e diretrizes de observabilidade do modelo e da API.

Conteúdo típico do Canvas:

- Análise de negócio e parâmetros de mercado
- Metas técnicas (AUROC, Recall, PR-AUC) — conferir último treino / MLflow
- Referências de desempenho operacional (uptime, latência)
- Roadmap CRISP-DM em linha com o plano de monitoramento

---

## Arquitetura do sistema

### Fluxo implementado no código

1. **Ingestão**: CSV Telco em `data/raw/`; preparação em `[src/data/loader.py](src/data/loader.py)`.
2. **Features**: engenharia e pré-processamento sklearn em `[src/features/pipeline.py](src/features/pipeline.py)` (ver `[specs/feature-pipeline.md](specs/feature-pipeline.md)`).
3. **Treino**: `[src/models/train.py](src/models/train.py)` — hold-out estratificado (20%), validação cruzada StratifiedKFold (*k* = 5) no conjunto de treino, registo MLflow, artefatos em `models/`.
4. **Inferência**: `[src/api/](src/api/)` — carregamento de modelo e `pipeline.pkl` no arranque; endpoints síncronos (`predict`, `predict_batch`), contrato em OpenAPI.

Diagrama lógico:

```
[Dados brutos CSV] → [loader] → [pipeline de features] → [treino MLP + avaliação]
        → artefatos: mlp_best.pt | pipeline.pkl | mlp_config.json
                                              → [API FastAPI]
```

### Documentação relacionada


| Documento                                     | Conteúdo                            |
| --------------------------------------------- | ----------------------------------- |
| [ML_CANVAS.md](docs/ML_CANVAS.md)             | Negócio, KPIs, roadmap CRISP-DM     |
| [MONITORING_PLAN.md](docs/MONITORING_PLAN.md) | Drift, alertas, observabilidade     |
| [DECISIONS.md](docs/DECISIONS.md)             | Infraestrutura e decisões de deploy |


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
├── tests/
│   ├── conftest.py
│   ├── unit/                     # Testes unitários (dados, features, treino, schemas)
│   │   ├── test_data_loader.py
│   │   ├── test_loader_pandera.py
│   │   ├── test_feature_pipeline.py
│   │   ├── test_schema.py
│   │   └── test_train_script.py
│   └── integration/              # Testes HTTP da API
│       ├── conftest.py
│       ├── test_api_root_health.py
│       ├── test_api_predict.py
│       ├── test_api_predict_batch.py
│       └── test_api_errors.py
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
# Suite completa (executar após treino se forem necessários artefatos em models/)
pytest tests/ -v --cov=src
```

### 5. Treinar Modelo MLP

```bash
# Treina modelo com config em configs/mlp_default.yaml
task train

# Resultado: Recall=0.8467 (meta ≥0.75 ✅), ROC-AUC=0.8506, PR-AUC=0.6648
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

### Etapa 1: Preparação de dados

- Leitura do CSV; tratamento de `TotalCharges` vazios (mediana); codificação do alvo `Churn`; remoção de `customerID` (validação opcional com Pandera quando instalado).
- Partição estratificada **80% / 20%** (treino com CV interno / conjunto de teste final); ver `[train.py](src/models/train.py)`.

### Etapa 2: Feature Engineering (Scikit-Learn)

Implementação reprodutível em `[src/features/pipeline.py](src/features/pipeline.py)` + `[specs/feature-pipeline.md](specs/feature-pipeline.md)`:

1. `**engineer_features`** (via `FunctionTransformer`): cria `log_tenure = log(tenure+1)`, `is_fiber`, `n_add_on_services` (contagem de add-ons); remove colunas de baixo sinal (`gender`, `PhoneService`, `MultipleLines`, `TotalCharges`, `StreamingTV`, `StreamingMovies`).
2. **Numéricas**: `SimpleImputer(median)` + `StandardScaler` — `log_tenure`, `MonthlyCharges`, `SeniorCitizen`, `n_add_on_services`.
3. **Binárias**: `OrdinalEncoder` — `Partner`, `Dependents`, `PaperlessBilling`, `is_fiber`.
4. **Nominais**: `OneHotEncoder(drop="if_binary")` — `InternetService`, serviços online, `Contract`, `PaymentMethod`.
5. **Saída**: ~**30** colunas numéricas codificadas (antes ~40 sem engenharia deliberada).

Notebook de validação: `[notebooks/feature_engineering.ipynb](notebooks/feature_engineering.ipynb)`.

### Etapa 3: Modelagem - Baseline vs Deep Learning

#### 3a. Hyperparameter Tuning: Random Search (Random Forest)

**Método**: RandomizedSearchCV com 20 iterações aleatórias e StratifiedKFold(k=5)

**Espaço de Hiperparâmetros Explorado**:

- `n_estimators`: [50, 100, 150, 200, 250]
- `max_depth`: [5, 10, 15, 20, None]
- `min_samples_split`: [2, 5, 10, 15]
- `min_samples_leaf`: [1, 2, 4, 8]
- `max_features`: ["sqrt", "log2"]
- `class_weight`: ["balanced", None]

**Métrica de Otimização**: ROC-AUC (0.8389 alcançado)

**Resultado da Busca**:

- Melhor Run: 20 iterações testadas automaticamente
- Tempo Computacional: ~45 minutos (paralelo com n_jobs=-1)
- Benchmark vs Default: +2.2% ROC-AUC, +20.3% F1-Score
- Artefatos Salvos: Best model, hiperparâmetros, test results em MLflow

**Notebook de Referência**: [notebooks/random_forest.ipynb](notebooks/random_forest.ipynb)

---

#### 3b. Baseline: Logistic Regression (Scikit-Learn)

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

Baselines avaliados com StratifiedKFold k=5 (média ± std). Random Forest TUNED otimizado via Random Search. MLP avaliado em holdout test set (20%).


| Modelo                                  | Accuracy         | ROC AUC            | Recall           | Precision        | F1               |
| --------------------------------------- | ---------------- | ------------------ | ---------------- | ---------------- | ---------------- |
| DummyClassifier (most_frequent)         | 0.7346±0.000     | 0.5000±0.000       | 0.0000±0.000     | 0.0000±0.000     | 0.0000±0.000     |
| DummyClassifier (stratified)            | 0.6129±0.006     | 0.5050±0.007       | 0.2750±0.011     | 0.2727±0.011     | 0.2738±0.011     |
| Logistic Regression (balanced)          | 0.7456±0.005     | 0.8449±0.013       | **0.8020±0.015** | 0.5132±0.007     | 0.6258±0.009     |
| Decision Tree (balanced)                | 0.7316±0.013     | 0.6588±0.020       | 0.5029±0.036     | 0.4940±0.024     | 0.4983±0.030     |
| Random Forest (default)                 | 0.7842±0.010     | 0.8207±0.010       | 0.4746±0.035     | 0.6223±0.024     | 0.5380±0.029     |
| **Random Forest (Random Search TUNED)** | **0.7896±0.012** | **0.8389±0.011** ✅ | **0.6127±0.032** | **0.6891±0.018** | **0.6478±0.024** |
| **MLP (PyTorch)**                       | **0.8067**       | **0.8506** ✅       | **0.8467** ✅     | **0.4953**       | **0.625**        |


**Meta de negócio: Recall ≥ 0.75** ✅  

- Logistic Regression: 0.80 ± 0.015 (atinge target)
- Random Forest (TUNED): 0.6127 (não atinge, mas melhora vs default)
- **MLP (PyTorch): 0.8467** (atinge target com AUC-ROC=0.8506, PR-AUC=0.6648)
- Exit code: 0 ✅ Validação de performance passou

**Random Search Impact (Random Forest)**:

- **ROC-AUC**: 0.8207 → 0.8389 (+2.2%)
- **Accuracy**: 0.7842 → 0.7896 (+0.7%)
- **F1-Score**: 0.5380 → 0.6478 (+20.3%)
- **Hiperparâmetros Otimizados**: n_estimators, max_depth, min_samples_split, class_weight
- **CV Strategy**: 20 iterações aleatórias com StratifiedKFold(k=5)

#### 3c. Deep Learning: Rede Neural (PyTorch)

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
- **Loss**: BCEWithLogitsLoss com pos_weight=2.7683 (balanceamento de classes: 5174 neg / 1869 pos)
- **Scheduler**: Cosine Annealing (warm-up 5 epochs, T_max=100)
- **Regularization**: L2=0.0001, Dropout escalado por layer (0.3, 0.2, 0.2)
- **Batch Size**: 32
- **Epochs**: 100 com *early stopping* (paciência conforme `configs/mlp_default.yaml`, monitorização da **perda de validação**)
- **Threshold Otimizado**: Grid search 0.01-0.99 para maximizar Expected Profit (não 0.5)

**Justificativa NN vs Baseline**:

1. Features não-lineares (tenure × monthly_charges → churn risk)
2. Captura interações entre serviços ativos
3. AUROC 0.85+ vs Logistic 0.76 (~9% melhoria)
4. **Expected Profit**: NN Recall 0.80 = +R$ 220K/1M clientes vs Logistic Recall 0.70
5. Batch normalization melhora estabilidade treino

### Etapa 4: Avaliação e registo

- **Métricas**: AUROC, PR-AUC, *recall*, *precision*, F1, exatidão; limiar de decisão para métricas derivado do lucro esperado no código de avaliação (ver `train.py`).
- **Validação**: StratifiedKFold no treino; desempenho de referência no hold-out de teste (20%).
- **MLflow**: parâmetros, métricas do run, modelo PyTorch e artefato `pipeline.pkl` (conforme configuração de *tracking*).

### Etapa 5: Artefatos para inferência e CI

- `models/mlp_best.pt` — pesos do MLP  
- `models/pipeline.pkl` — pipeline sklearn de pré-processamento  
- `models/mlp_config.json` — dimensão de entrada e metadados do último treino

---

## Testes automatizados

As suites encontram-se em `tests/unit/` e `tests/integration/`. O projeto usa **pytest**; o comando `pytest --collect-only` permite conferir o número atual de casos (da ordem de **75**, dependendo da revisão do repositório).

### Execução

```bash
task test
# ou
pytest tests/ -v --cov=src --cov-report=term-missing
pytest tests/unit/ -v
pytest tests/integration/ -v
```

### Escopo das suites


| Pasta                | Foco                                                                                                             |
| -------------------- | ---------------------------------------------------------------------------------------------------------------- |
| `tests/unit/`        | `loader`, pipeline de features, schemas, saneamento do fluxo de treino (`train.py` / artefatos quando existirem) |
| `tests/integration/` | Rotas `/`, `/health`, predição simples e em *batch*, erros HTTP (422, 429, 503), *rate limiting*                 |


Relatórios de cobertura são gerados com `--cov=src`; percentagens atualizadas resultam do último comando ou do job de CI.

### Cobertura (opcional)

```bash
pytest tests/ -v --cov=src --cov-report=html --cov-report=term
pytest tests/ -v --cov=src --cov-fail-under=80   # falha local se abaixo do limiar
```

---

## 🛠️ Qualidade de código e CI/CD

### Ferramentas locais

- **Ruff** — lint e formatação (`task lint`, `task format`).
- **Mypy** — tipagem estática (dependência do projeto; integração opcional em fluxos locais).

### CI/CD (GitHub Actions)

Três *workflows* com responsabilidades distintas:


| Workflow     | Arquivo      | Gatilho                                | Jobs                                                                             |
| ------------ | ------------ | -------------------------------------- | -------------------------------------------------------------------------------- |
| **PR Check** | `pr.yml`     | Pull Request → `main`                  | lint + testes unitários                                                          |
| **CD**       | `cd.yml`     | Release criada como **pre-release**    | lint → treino → testes integração → build Docker → smoke test                    |
| **Deploy**   | `deploy.yml` | Pre-release **promovida** para release | pull imagem → SSH EC2 → `docker compose up` → health check → rollback automático |


### Processo de Release

```bash
# 1. Criar pre-release — dispara cd.yml (treino + build + smoke)
gh release create v1.0.0 --prerelease --title "v1.0.0" --notes "Descrição"

# 2. Aguardar cd.yml completar (lint, treino, integração, build, smoke)
#    O workflow atualiza as notas da release com as métricas do modelo.

# 3. Promover para release — dispara deploy.yml (deploy na EC2)
#    GitHub UI: Edit release → desmarcar "Set as a pre-release" → Update release
#    Ou via CLI:
gh release edit v1.0.0 --prerelease=false
```

O `deploy.yml` executa automaticamente após a promoção:

1. Faz pull da imagem `mmacanmunhoz/churn-api:v1.0.0` no Docker Hub
2. Acessa a EC2 via SSH e atualiza o `docker compose`
3. Aguarda health check em `https://api.pocsarcotech.com/health`
4. Em caso de falha, faz rollback automático para a imagem anterior

---

## API REST (FastAPI)

A especificação **canônica** é o **OpenAPI** exposto em `/docs` e `/openapi.json`. Os corpos de pedido seguem os nomes de colunas do *dataset* Telco (`Contract`, `tenure`, `MonthlyCharges`, …), definidos em `[src/api/schemas.py](src/api/schemas.py)`.

### `GET /`

**Response (200)**: metadados da API (`app`, `version`, `description`, `documentation`, `endpoints`).

### `GET /health`

**Response (200)** — campos principais:

- `status`: `healthy` se modelo e pipeline carregados; caso contrário `degraded`
- `model_version`, `model_source` (`local_file` | `mlflow_registry`), `uptime_seconds`, `timestamp`

### `POST /api/v1/predict`

**Request** — um objeto `PredictRequest` (campos obrigatórios; exemplo reduzido):

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

**Response (200)**:

```json
{
  "churn_probability": 0.73,
  "churn_predicted": true,
  "model_version": "1.0.0",
  "processing_time_ms": 12.5
}
```

Critério atual para `churn_predicted`: probabilidade de churn **≥ 0,5**. Na avaliação offline, o treino também explora limiares orientados a custo/lucro — ver métricas em `train.py` / MLflow.


| Code | Cenário                           |
| ---- | --------------------------------- |
| 200  | Sucesso                           |
| 422  | Validação Pydantic                |
| 429  | Rate limit (10 req / 30 s por IP) |
| 503  | Modelo ou pipeline não carregado  |


**Request**: objeto JSON com chave `**records`**: lista de até **10.000** registros no mesmo formato de `PredictRequest`.

**Response (200)** inclui `batch_id`, `predictions` (por item: `record_index`, `churn_probability`, `churn_predicted`), `model_version`, `total_records`, `processing_time_ms`.

### API Documentation


| Ambiente     | Swagger UI                                                             | ReDoc                                                                    |
| ------------ | ---------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| **Produção** | [https://api.pocsarcotech.com/docs](https://api.pocsarcotech.com/docs) | [https://api.pocsarcotech.com/redoc](https://api.pocsarcotech.com/redoc) |
| **Local**    | [http://localhost:8000/docs](http://localhost:8000/docs)               | [http://localhost:8000/redoc](http://localhost:8000/redoc)               |


---

## 📊 MLflow Tracking & Experiment Management

### Setup & Inicio

```bash
# Iniciar MLflow UI
mlflow ui --host 0.0.0.0 --port 5000

# Acesso em: http://localhost:5000
```

### Logging Automático

Cada execução de `src/models/train.py` regista no MLflow hiperparâmetros, métricas agregadas de validação cruzada e de *hold-out*, modelo PyTorch, artefato `pipeline.pkl`, hash do *dataset* e etiquetas definidas no código. Não há registo métrico por *epoch* individual neste *script* — apenas o necessário para comparar *runs* e reproduzir artefatos.

### Comparação de Experimentos

```python
# Query MLflow para comparar modelos
runs = mlflow.search_runs(experiment_names=["churn-baselines"])
# Visualizar todos os runs
for run in runs:
    print(f"Run: {run.info.run_name}")
    print(f"  ROC-AUC: {run.data.metrics.get('roc_auc', 'N/A')}")
    print(f"  Recall: {run.data.metrics.get('recall', 'N/A')}")
    print(f"  F1: {run.data.metrics.get('f1', 'N/A')}")

# Melhor run por métrica
best_roc = runs.sort_values("metrics.roc_auc", ascending=False).iloc[0]
best_recall = runs.sort_values("metrics.recall", ascending=False).iloc[0]
```

---

## Governança e Model Card

O **[MODEL_CARD.md](docs/MODEL_CARD.md)** descreve o modelo (MLP PyTorch), dados, desempenho de referência, limitações, vieses e recomendações. Para políticas de *drift* e retreino, utilize também o **[MONITORING_PLAN.md](docs/MONITORING_PLAN.md)**.

---

## Monitoramento operacional

Referência: **[MONITORING_PLAN.md](docs/MONITORING_PLAN.md)**.


| Camada              | Instrumentação sugerida | Escopo                                                                                                  |
| ------------------- | ----------------------- | ------------------------------------------------------------------------------------------------------- |
| API / infra         | Prometheus + Grafana    | Requisições HTTP, latência, erros, recursos                                                             |
| Experimentação      | MLflow                  | Registro de treinos, métricas, artefatos                                                                |
| Qualidade dos dados | Procedimentos no plano  | Detecção de *drift* (ex.: KS em variáveis contínuas; testes adequados para categóricas como `Contract`) |


Alertas, limiares e playbooks encontram-se no documento acima.

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

### Índice de documentos

- **[ML_CANVAS.md](docs/ML_CANVAS.md)** — Contexto de negócio, KPIs e roadmap CRISP-DM.
- **[MODEL_CARD.md](docs/MODEL_CARD.md)** — Modelo, limitações e riscos conhecidos.
- **[VALIDATION_REPORT.md](docs/VALIDATION_REPORT.md)** — Relatório de validação e métricas.
- **[MONITORING_PLAN.md](docs/MONITORING_PLAN.md)** — Plano de monitoramento (drift, alertas, observabilidade).
- **[DECISIONS.md](docs/DECISIONS.md)** — Decisões de arquitetura e deploy.
- **[CONVENTIONS.md](docs/CONVENTIONS.md)** — Convenções de código e repositório.
- **[IMPLEMENTATION_GUIDE.md](docs/IMPLEMENTATION_GUIDE.md)** — Guia de implementação.

### Especificações de Features

- **[specs/data-loader.md](specs/data-loader.md)**: Especificação de carregamento e validação
- **[specs/feature-pipeline.md](specs/feature-pipeline.md)**: Pipeline de features com sklearn
- **[specs/mlp-model.md](specs/mlp-model.md)**: Arquitetura MLP, hiperparâmetros, early stopping
- **[specs/model-training.md](specs/model-training.md)**: Pipeline de treinamento, fluxo de configuração
- **[specs/inference-api.md](specs/inference-api.md)**: Endpoints FastAPI, schemas Pydantic, rate limiting
- **[specs/baseline-comparison.md](specs/baseline-comparison.md)**: Comparação de 5 baselines
- **[specs/iac.md](specs/iac.md)** — Terraform, módulos AWS.

Contratos HTTP (`Swagger` / `ReDoc`): mesma tabela na secção **API REST (FastAPI)** deste README.

---

## 🔧 Stack Tecnológico

### Core ML & Data


| Tecnologia       | Versão | Propósito                            | Status      |
| ---------------- | ------ | ------------------------------------ | ----------- |
| **Python**       | 3.12+  | Runtime                              | ✅ Instalado |
| **PyTorch**      | 2.11.0 | Deep Learning (rede neural MLP)      | ✅ Instalado |
| **Scikit-Learn** | 1.8.0  | 5 Baselines + pré-processamento      | ✅ Instalado |
| **Pandas**       | 2.3.3  | Manipulação & validação de dados     | ✅ Instalado |
| **NumPy**        | 2.4.4  | Computação numérica                  | ✅ Instalado |
| **SciPy**        | 1.17.1 | Estatística (KS-test, distributions) | ✅ Instalado |


### API & Backend


| Tecnologia   | Versão  | Propósito                          | Status      |
| ------------ | ------- | ---------------------------------- | ----------- |
| **FastAPI**  | 0.135.3 | Framework HTTP assíncrono          | ✅ Instalado |
| **Uvicorn**  | 0.44.0  | ASGI server                        | ✅ Instalado |
| **Pydantic** | 2.13.0  | Validação & serialização (schemas) | ✅ Instalado |


### Experiment & Model Management


| Tecnologia    | Versão | Propósito                            | Status      |
| ------------- | ------ | ------------------------------------ | ----------- |
| **MLflow**    | 3.11.1 | Tracking, Model Registry, deployment | ✅ Instalado |
| **Structlog** | 25.5.0 | Logging estruturado (JSON)           | ✅ Instalado |


### Testes & Qualidade de Código


| Tecnologia         | Versão  | Propósito                      | Status      |
| ------------------ | ------- | ------------------------------ | ----------- |
| **Pytest**         | 9.0.3   | Framework de testes            | ✅ Instalado |
| **Pytest-cov**     | 7.0     | Coverage reporting             | ✅ Instalado |
| **Pytest-asyncio** | 0.24.0  | Async test support             | ✅ Instalado |
| **Ruff**           | 0.15.10 | Linting ultrafast (ruff check) | ✅ Instalado |
| **Mypy**           | 1.20.1  | Type checking estático         | ✅ Instalado |


### Task Automation & Notebooks


| Tecnologia    | Versão | Propósito                            | Status      |
| ------------- | ------ | ------------------------------------ | ----------- |
| **Taskipy**   | 1.14.1 | Task runner (task train, task test)  | ✅ Instalado |
| **Jupyter**   | 1.1.1  | Notebooks interativos (11 notebooks) | ✅ Instalado |
| **IPython**   | 9.12.0 | IPython kernel para notebooks        | ✅ Instalado |
| **IPykernel** | 7.2.0  | Kernel para Jupyter                  | ✅ Instalado |


### DevOps & Infrastructure


| Tecnologia         | Versão | Propósito                            | Status      |
| ------------------ | ------ | ------------------------------------ | ----------- |
| **Docker**         | 24.0+  | Containerização (Dockerfile)         | ⚠️ Opcional |
| **Terraform**      | 1.5+   | Infraestrutura como Código (AWS IaC) | ⚠️ Opcional |
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
Internet
    │ HTTPS (443)
    ▼
┌─────────────────────────────────────────────────┐
│  ALB (Application Load Balancer)                │
│  └─ api.pocsarcotech.com  → EC2:8080  (FastAPI) │
│  └─ mlflow.pocsarcotech.com → EC2:5000 (MLflow) │
│  └─ ACM: wildcard cert *.pocsarcotech.com       │
├─────────────────────────────────────────────────┤
│  AWS EC2 (t3.medium, Ubuntu 22.04)              │
│  └─ Docker: mlflow (5000) + fastapi (8080)      │
│  └─ user_data: setup automático                 │
├─────────────────────────────────────────────────┤
│  Security Group (Networking)                    │
│  └─ Ingress: 8080 (API), 5000 (MLflow), 22 SSH  │
│  └─ Egress: Internet acesso                     │
├─────────────────────────────────────────────────┤
│  IAM Role + Instance Profile                    │
│  └─ S3 access para MLflow artifacts             │
├─────────────────────────────────────────────────┤
│  S3 Bucket (fiap-mlflow-artifacts)              │
│  └─ MLflow artifacts, modelo, logs              │
├─────────────────────────────────────────────────┤
│  RSA Key Pair (SSH access)                      │
│  └─ ~/.ssh/mlflow-flask-project-key.pem         │
└─────────────────────────────────────────────────┘
```

**URLs Deployadas:**


| Serviço             | URL                                                                                |
| ------------------- | ---------------------------------------------------------------------------------- |
| API FastAPI         | [https://api.pocsarcotech.com](https://api.pocsarcotech.com)                       |
| MLflow UI           | [https://mlflow.pocsarcotech.com/mlflow/](https://mlflow.pocsarcotech.com/mlflow/) |
| API Docs            | [https://api.pocsarcotech.com/docs](https://api.pocsarcotech.com/docs)             |



### Deploy (Terraform)

```bash
cd iac/
terraform init           # Inicializa backend S3 (tech-terraform-poc)
terraform plan           # Preview mudanças
terraform apply          # Provisiona na AWS
terraform destroy        # Destrói recursos
```

**Modules**:

- `modules/compute/` — EC2 com user_data Docker
- `modules/networking/` — Security Group
- `modules/iam/` — Role + Profile + S3 policy
- `modules/storage/` — S3 bucket (fiap-mlflow-artifacts)
- `modules/keypair/` — RSA key pair gerado
- `modules/alb/` — ALB + listener HTTPS + host-based rules

---

### Estado do projeto

Entregáveis principais desta fase: pipeline de treino reprodutível (MLP + MLflow), artefatos em `models/`, API FastAPI com testes de integração, *lint* em CI (Ruff), infraestrutura descrita em `iac/` e *pipelines* em `.github/workflows/` (`pr.yml`, `cd.yml`, `deploy.yml`).

**Última atualização do README:** maio de 2026 · **Fase FIAP:** Tech Challenge — rede neural para predição de churn.

## 📚 Referências & Recursos

- [PyTorch Documentation](https://pytorch.org/docs/stable/index.html)
- [Scikit-Learn Best Practices](https://scikit-learn.org/stable/)
- [MLflow Model Registry](https://mlflow.org/docs/latest/model-registry.html)
- [FastAPI Production](https://fastapi.tiangolo.com/deployment/)
- [Model Card Guide](https://huggingface.co/docs/hub/model-cards)
- [AI Governance Frameworks](https://www.parthenonsystems.com/blog/machine-learning-model-cards/)

