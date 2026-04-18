---
name: train
description: Treina o modelo MLP de churn e registra no MLflow
---

Execute o pipeline de treinamento completo:

1. Carregue dados via `src/data/loader.py` — valide schema com pandera
2. Aplique `src/features/pipeline.py` — StandardScaler + OneHot/Ordinal + SelectKBest
3. Split estratificado: 70% train / 15% val / 15% test (`random_state=42`)
4. Treine baselines primeiro:
   - `DummyClassifier(strategy="most_frequent")`
   - `LogisticRegression(random_state=42, max_iter=1000)`
5. Treine `ChurnMLP` (PyTorch) com early stopping (patience=10)
6. Avalie todos os modelos com: AUC-ROC, PR-AUC, F1, Recall, Precision
7. Registre cada run no MLflow com params + métricas + dataset hash + artefatos

Seeds obrigatórios: `RANDOM_SEED = 42`.
Logging via structlog — sem print().

Ao final, atualize a tabela de experimentos em `docs/decisions.md`.
