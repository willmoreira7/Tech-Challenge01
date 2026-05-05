# Conventions

## Seeds e Reprodutibilidade

`RANDOM_SEED = 42` fixado globalmente. Aplicar em:

```python
import random, numpy as np, torch
random.seed(42)
np.random.seed(42)
torch.manual_seed(42)
torch.backends.cudnn.deterministic = True
```

Splits sempre com `random_state=42`. StratifiedKFold obrigatório para classificação.

---

## Logging

Use `structlog` em todo código `src/`. Proibido `print()`.

```python
import structlog
log = structlog.get_logger()

log.info("training.started", epoch=1, lr=0.001)
log.warning("data.missing_values", column="TotalCharges", count=11)
log.error("api.predict_failed", error=str(e))
```

Formato de eventos: `<módulo>.<ação>` em snake_case.

---

## Estrutura de Módulos

```
src/
├── data/
│   ├── loader.py       # load_raw(), validate_schema()
│   └── validator.py    # pandera schema
├── features/
│   ├── pipeline.py     # build_pipeline()
│   └── transformers.py # transformadores custom (BaseEstimator)
├── models/
│   ├── mlp.py          # ChurnMLP(nn.Module)
│   └── train.py        # train_model(), evaluate_model()
└── api/
    ├── app.py          # FastAPI app
    ├── schemas.py      # Pydantic models
    └── middleware.py   # latency logging
```

---

## Nomenclatura

| Contexto | Padrão | Exemplo |
|----------|--------|---------|
| Arquivos | snake_case | `data_loader.py` |
| Classes | PascalCase | `ChurnMLP`, `TenureEncoder` |
| Funções | snake_case | `load_raw_data()` |
| Constantes | UPPER_SNAKE | `RANDOM_SEED`, `TARGET_COL` |
| Features | snake_case | `monthly_charges`, `tenure` |
| MLflow runs | `<modelo>_v<n>` | `mlp_v1`, `logreg_baseline` |

---

## Testes

Mínimo 3 tipos obrigatórios:

```
tests/
├── smoke/      # importa, instancia, não levanta exceção
├── schema/     # pandera + pydantic (shapes, tipos, nulos)
└── api/        # /health, /predict, erros 422/500
```

Fixtures compartilhadas em `conftest.py`. Sem mocks do banco ou do modelo em testes de integração.

---

## Experimentos MLflow

Cada run deve logar:

```python
mlflow.log_params({"lr": 0.001, "epochs": 50, "hidden": [256,128,64,32]})
mlflow.log_metrics({"auc_roc": 0.84, "recall": 0.77, "pr_auc": 0.68})
mlflow.set_tag("dataset_hash", hash_sha256)
mlflow.log_artifact("models/scaler.pkl")
mlflow.log_artifact("models/mlp.pt")
```

Nome do experimento: `churn-prediction`. Run name: `<modelo>_<data>` (ex: `mlp_2026-04-17`).

---

## Commits

Seguir Conventional Commits (enforçado via Commitlint):

```
feat(data): adicionar loader com validação pandera
fix(api): corrigir status 500 em payload inválido
test(mlp): adicionar smoke test do forward pass
docs(model_card): preencher métricas finais
```

Scopes válidos: `data`, `features`, `model`, `api`, `tests`, `docs`, `ci`, `config`, `iac`.
