# CLAUDE.md

Leia este arquivo antes de qualquer ação.
Para detalhes, leia os arquivos referenciados em docs/.

<important>
- RANDOM_SEED = 42 em todo código. Nunca use random/numpy/torch sem fixar seed.
- Proibido usar print(). Use structlog em todos os módulos src/.
- Métrica de negócio prioritária: Recall ≥ 0.75 (FN custa 20× mais que FP).
- Linting (ruff) deve passar sem erros antes de qualquer commit.
- Validação cruzada sempre estratificada (StratifiedKFold).
- Todo experimento MLflow deve registrar: params, métricas, dataset hash e artefatos.
</important>

Regras de qualidade de código: ver `.claude/rules/code-quality.md`.

---

## Visão geral

Previsão de churn para operadora de telecomunicações.
Classificação binária de clientes com risco de cancelamento.

- **Dataset**: Telco Customer Churn (IBM) — ~7.000 registros, 20 features, target `Churn`
- **Modelo principal**: MLP (PyTorch)
- **Baselines**: DummyClassifier, LogisticRegression
- **Stack**: PyTorch · Scikit-Learn · MLflow · FastAPI · Pydantic · structlog · ruff · pytest

---

## Estrutura de pastas

```
churn-mlp/
├── src/
│   ├── data/        # loaders, validators
│   ├── features/    # pipeline, transformadores custom
│   ├── models/      # MLP class, train loop
│   └── api/         # FastAPI app, schemas, middleware
├── tests/
├── notebooks/
├── data/
│   ├── raw/
│   └── processed/
├── models/
├── iac/
│   ├── modules/
│   │   ├── compute/     # EC2 + user_data (Docker + MLflow + FastAPI)
│   │   ├── networking/  # Security Group
│   │   ├── iam/         # IAM Role + Instance Profile + S3 policy
│   │   ├── storage/     # S3 bucket para artefatos MLflow
│   │   ├── keypair/     # Par de chaves RSA gerado via Terraform
│   │   └── alb/         # ALB + listener HTTPS + host-based rules
│   ├── flask-app/       # Flask placeholder (testes locais sem AWS)
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── locals.tf
│   └── versions.tf
├── specs/
│   ├── data-loader.md
│   ├── feature-pipeline.md
│   ├── mlp-model.md
│   ├── baseline-comparison.md
│   ├── api-predict.md
│   └── iac.md
├── docs/
│   ├── conventions.md
│   ├── decisions.md
│   ├── model_card.md
│   └── monitoring_plan.md
├── CLAUDE.md
├── pyproject.toml
├── Makefile
└── .gitignore
```

---

## Comandos

```bash
make install   # pip install -e ".[dev]"
make lint      # ruff check src/ tests/
make test      # pytest tests/ -v
make train     # python src/models/train.py
make run       # uvicorn src.api.app:app --reload
make mlflow    # mlflow ui --port 5000
```

### IAC (Terraform)

```bash
cd iac
terraform init      # inicializa providers e backend S3
terraform validate  # valida sintaxe HCL
terraform plan      # preview das mudanças
terraform apply     # provisiona infra na AWS
terraform destroy   # destrói todos os recursos

# Teste local (sem AWS)
cd iac/flask-app
docker compose -f docker-compose.local.yml up -d --build
```

---

## Contexto detalhado

| Arquivo | Conteúdo |
|---------|----------|
| `docs/CONVENTIONS.md` | Convenções de código, seeds, logging, commits |
| `docs/DECISIONS.md` | Decisões arquiteturais, experimentos MLflow, lições |
| `docs/MODEL_CARD.md` | Performance, limitações, vieses, cenários de falha |
| `docs/MONITORING_PLAN.md` | Métricas, alertas, playbook de resposta |
| `specs/mlp-model.md` | Arquitetura MLP, hiperparâmetros, early stopping, validação de performance |
| `specs/model-training.md` | Pipeline de treinamento, fluxo de configuração, CI/CD integration |
| `specs/inference-api.md` | Endpoints FastAPI, schemas Pydantic, rate limiting, health check |
| `specs/iac.md` | Arquitetura Terraform, módulos AWS, variáveis, critérios de aceitação |

---

## Decisões ativas

> Atualizado após EDA (2026-04-17).

- Métrica principal: `Recall ≥ 0.75` (restrição de negócio — FN custa 20×) + `PR-AUC` como métrica técnica (mais informativa que AUC-ROC em dados desbalanceados 73.5%/26.5%)
- pos_weight: `2.7683` (5174 neg / 1869 pos) — usar em `BCEWithLogitsLoss(pos_weight=torch.tensor(2.7683))`
- Threshold de decisão: `otimizar via Expected Profit = TP×1140 - FP×60 - FN×1200` (não fixar em 0.5)
- Arquitetura MLP: `[ ] a definir após experimentos` (spec inicial: 256→128→64→32→1)
- Versão do dataset: `[ ] registrar hash após download`
- Features candidatas a drop: `gender` (churn 26.9% vs 26.2%, sem poder discriminativo), `TotalCharges` (correlação 0.826 com tenure — avaliar no pipeline), `PhoneService` (sinal fraco: 26.7% vs 24.9%)
- Features mais preditivas: `Contract`, `InternetService`, `PaymentMethod`, `OnlineSecurity`, `TechSupport`, `tenure`
- TotalCharges: 11 linhas com espaço → imputadas com mediana (1397.48)

---

## Status de Implementação

### ✅ API FastAPI (Baseado em `specs/inference-api.md`)
- **Status**: Implementado e testado
- **Endpoints**: 
  - `GET /` — Health check com uptime
  - `GET /health` — Status da API
  - `POST /api/v1/predict` — Predição individual (com validação Pydantic Literal)
  - `POST /api/v1/predict_batch` — Predição em lote (até 10k registros)
- **Features**: Rate limiting (10 req/30sec), middleware customizado, carregamento automático de modelo
- **Testes**: 51 testes de integração (todos passando)
- **Ref**: [src/api/app.py](src/api/app.py), [src/api/handlers.py](src/api/handlers.py), [src/api/schemas.py](src/api/schemas.py)

### ✅ Pipeline de Treinamento (Baseado em `specs/mlp-model.md` + `specs/model-training.md`)
- **Status**: Implementado com MLflow integration
- **Script**: [src/models/train.py](src/models/train.py)
- **Funcionalidades**:
  - Carregamento de hyperparâmetros via `mlp_config.json`
  - Early stopping com patience configurável
  - Validação de performance: Recall ≥ 0.75 (exit code 2 se falhar)
  - Salvamento de artefatos: modelo, pipeline, config, test_results
  - Logging estruturado via structlog
  - Registrom em MLflow com experiment tracking
- **Performance**: Recall=0.8467, AUC-ROC=0.8506, PR-AUC=0.6648 (Fonte: `models/test_results.json`)
- **Testes**: 13 testes unitários (todos passando)
- **CI/CD**: Integrado em `.github/workflows/tests.yml` — treina antes de rodar testes

### ✅ Infraestrutura AWS (Baseado em `specs/iac.md`)
- **Status**: Deployada e operacional
- **Plataforma**: EC2 (t3.medium, Ubuntu 22.04) + ALB + Route53 + ACM
- **URLs**:
  - API: https://api.pocsarcotech.com
  - MLflow: https://mlflow.pocsarcotech.com/mlflow/
- **Módulos Terraform**: keypair, networking, iam, storage, compute, alb
- **Backend remoto**: S3 (`tech-terraform-poc` / `environment-pos/terraform.tfstate`)
- **Ref**: [iac/](iac/), [specs/iac.md](specs/iac.md), [docs/DECISIONS.md](docs/DECISIONS.md#deploy-etapa-4)

### ✅ Validação Completa
- **Linting**: ruff 0 errors
- **Testes**: 64/64 passando (51 API + 13 training)
- **Treinamento**: Exit code 0, métrica de negócio atendida (Recall=0.8467 ≥ 0.75)
- **Deploy**: API e MLflow acessíveis via HTTPS em produção