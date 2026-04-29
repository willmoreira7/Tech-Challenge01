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
│   │   ├── compute/     # EC2 + user_data (Docker + MLflow + Flask)
│   │   ├── networking/  # Security Group
│   │   ├── iam/         # IAM Role + Instance Profile + S3 policy
│   │   ├── storage/     # S3 bucket para artefatos MLflow (opcional)
│   │   └── keypair/     # Par de chaves RSA gerado via Terraform
│   ├── flask-app/       # Flask placeholder (pré-migração para FastAPI)
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
| `docs/conventions.md` | Convenções de código, seeds, logging, commits |
| `docs/decisions.md` | Decisões arquiteturais, experimentos MLflow, lições |
| `docs/model_card.md` | Performance, limitações, vieses, cenários de falha |
| `docs/monitoring_plan.md` | Métricas, alertas, playbook de resposta |
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