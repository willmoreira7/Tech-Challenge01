---
name: experiment
description: Compara runs do MLflow, seleciona o melhor modelo e atualiza docs/DECISIONS.md. Usar após retreinar o modelo ou quando quiser analisar resultados de experimentos.
---

## Ver runs existentes

```bash
make mlflow
# abre http://localhost:5000 — experiment: churn-mlp
```

## Via Python (sem UI)

```python
import mlflow

mlflow.set_experiment("churn-mlp")
runs = mlflow.search_runs(order_by=["metrics.recall DESC"])
print(runs[["run_id", "metrics.recall", "metrics.pr_auc", "metrics.roc_auc", "metrics.f1", "tags.recall_target_met"]].head(10))
```

## Critérios de seleção do melhor modelo

Prioridade:
1. `recall_target_met == True` (Recall ≥ 0.75 — restrição de negócio)
2. Maximizar `pr_auc` (mais informativa que AUC-ROC em dados desbalanceados 26.5%)
3. Desempate por `roc_auc`

**Resultado atual (referência):**

| Modelo | Recall | PR-AUC | AUC-ROC | F1 |
|--------|--------|--------|---------|-----|
| MLP v1 (atual) | 0.8467 | 0.6648 | 0.8506 | 0.625 |
| LogisticRegression (baseline) | 0.802 | 0.655 | 0.845 | 0.626 |

## Após selecionar novo melhor modelo

1. Atualizar `docs/DECISIONS.md` — tabela de experimentos MLflow
2. Atualizar `docs/MODEL_CARD.md` — seção Performance com novas métricas
3. Atualizar `models/mlp_config.json` com os hiperparâmetros do melhor run
4. Verificar se `models/test_results.json` reflete os novos resultados

## Promover modelo para produção

```bash
# Copiar artefatos do run para models/
mlflow artifacts download -r <run_id> -d models/

# Verificar integridade
uv run pytest tests/unit/ -v
make test
```
