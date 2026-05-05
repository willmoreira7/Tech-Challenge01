---
name: baseline
description: Treina baselines (DummyClassifier + LogisticRegression), registra no MLflow e gera notebook comparativo. Usar quando quiser estabelecer ou re-verificar o piso de performance que o MLP deve superar.
---

Consulte `specs/baseline-comparison.md` para a spec completa.

## Estado atual

Baselines concluídos. Resultados em `notebooks/baselines.ipynb` e `docs/DECISIONS.md`.

| Modelo | Recall | F1 | AUC-ROC | PR-AUC |
|--------|--------|----|---------|--------|
| DummyClassifier (most_frequent) | 0.000 | 0.000 | 0.500 | 0.265 |
| DummyClassifier (stratified) | 0.275 | 0.274 | 0.505 | 0.268 |
| LogisticRegression (balanced) | **0.802** | 0.626 | 0.845 | **0.655** |

**Meta para o MLP:** superar PR-AUC=0.655 e manter Recall≥0.75.

## Para re-executar

O notebook é **autocontido** (sem imports de `src/`):

```bash
uv run jupyter nbconvert --to notebook --execute --inplace notebooks/baselines.ipynb
```

## Estrutura do notebook (se recriar do zero)

1. Setup: `RANDOM_SEED = 42`, imports diretos (pandas, numpy, sklearn, mlflow)
2. Dados: `pd.read_csv('../data/raw/WA_Fn-UseC_-Telco-Customer-Churn.csv')` com fix inline de `TotalCharges` e encode de `Churn`
3. Pipeline sklearn inline: `ColumnTransformer` com `StandardScaler`, `OrdinalEncoder`, `OneHotEncoder`
4. `StratifiedKFold(k=5, random_state=42)` para cada modelo
5. MLflow experiment `churn-baselines`: params (model, random_seed, cv_folds, dataset_hash, pos_weight) + metrics (recall_mean, f1_mean, roc_auc_mean, pr_auc_mean)
6. Tabela comparativa com highlight por coluna
7. Curvas ROC + PR sobrepostas
8. Threshold ótimo para LogReg via Expected Profit (`TP×1140 - FP×60 - FN×1200`)
9. Conclusão: qual baseline o MLP deve superar e em qual métrica

Seeds: `RANDOM_SEED = 42` em todo código.
