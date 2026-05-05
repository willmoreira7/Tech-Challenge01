---
name: train
description: Treina o modelo MLP de churn e registra no MLflow. Usar quando quiser retreinar, ajustar hiperparâmetros ou verificar se Recall≥0.75 está sendo atingido.
---

Consulte `specs/mlp-model.md` e `specs/model-training.md` para detalhes completos.

## Estado atual

Script implementado em `src/models/train.py`. Resultados mais recentes: Recall=0.8467, AUC-ROC=0.8506, PR-AUC=0.6648, F1=0.625.

## Comando

```bash
make train
# ou com config customizada:
uv run python src/models/train.py --config models/mlp_config.json
```

## Hiperparâmetros (models/mlp_config.json)

Modificar aqui antes de retreinar — não hardcode no script:
- `hidden_dim`, `hidden_layers`, `dropout`, `activation`
- `learning_rate`, `batch_size`, `epochs`, `early_stopping_patience`

## Pipeline de execução

1. Dados: `data/raw/WA_Fn-UseC_-Telco-Customer-Churn.csv` via `src/data/loader.py`
2. Features: `src/features/pipeline.py` — output `input_dim=30`
3. Split: 80/20 estratificado (`random_state=42`) — hold-out fixo
4. CV: `StratifiedKFold(k=5)` no conjunto de treino
5. Artefatos salvos em `models/`: `mlp_best.pt`, `pipeline.pkl`, `mlp_config.json`, `test_results.json`
6. Exit code `2` se `Recall < 0.75` no test set

## MLflow

- Experiment: `churn-mlp` (ou `$MLFLOW_EXPERIMENT_NAME`)
- Params: input_dim, hidden_dims, dropout, lr, batch_size, epochs, n_folds, pos_weight
- Metrics: por fold (`fold{k}_*`) + CV agregado (`cv_*_mean/std`) + test set
- Tags: `dataset_hash`, `recall_target_met`
- Artefatos: `mlp_best.pt`, `pipeline.pkl`

Seeds: `RANDOM_SEED = 42`. Logging via structlog — sem print().
