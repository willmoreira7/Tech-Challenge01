---
name: train
description: Treina o modelo MLP de churn e registra no MLflow
---

Implemente e execute seguindo **exatamente** `specs/mlp-model.md` e `specs/feature-pipeline.md`.

1. Carregue dados via `src/data/loader.py`
2. Aplique `src/features/pipeline.py` (conforme `specs/feature-pipeline.md`)
3. Split estratificado: 70% train / 15% val / 15% test (`random_state=42`)
4. Implemente `ChurnMLP` em `src/models/mlp.py` (conforme `specs/mlp-model.md`):
   - Arquitetura: `Input → 256 → 128 → 64 → 32 → 1` (BatchNorm + ReLU + Dropout)
   - Loss: `BCEWithLogitsLoss(pos_weight=tensor(2.7683))`
   - Optimizer: `Adam(lr=1e-3)` + `ReduceLROnPlateau(patience=5)`
   - Early stopping: patience=10, monitorar `val_loss`
5. Treine com loop em `src/models/train.py`, salve melhor modelo em `models/mlp_best.pt`
6. Avalie com 5 métricas: Recall, Precision, F1, AUC-ROC, PR-AUC
7. Otimize threshold via Expected Profit (`TP×1140 - FP×60 - FN×1200`)
8. Registre no MLflow (`experiment=churn-mlp`): params + métricas + dataset hash + artefatos
9. Atualize tabela de experimentos em `docs/decisions.md`

Meta a superar (LogisticRegression): Recall≥0.75 · PR-AUC>0.655 · AUC-ROC>0.845 · F1>0.626

Seeds obrigatórios: `RANDOM_SEED = 42`.
Logging via structlog — sem print().
