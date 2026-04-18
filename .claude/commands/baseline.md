---
name: baseline
description: Treina baselines (DummyClassifier + LogisticRegression), registra no MLflow e gera notebook comparativo
---

Gere o notebook `notebooks/baselines.ipynb` **standalone** (sem imports de `src/`) seguindo o padrão da aula:

O notebook deve ser autocontido — todo o código inline, sem dependências de `src/`:

1. Setup: imports diretos (pandas, numpy, sklearn, matplotlib, mlflow), `RANDOM_SEED = 42`
2. Carregamento: `pd.read_csv('../data/raw/dataset.csv')` com fix de `TotalCharges` e encode de `Churn` inline
3. Pipeline sklearn inline: `ColumnTransformer` com `StandardScaler`, `OrdinalEncoder`, `OneHotEncoder`
4. Treine com StratifiedKFold (k=5, random_state=42):
   - `DummyClassifier(strategy="most_frequent")`
   - `DummyClassifier(strategy="stratified")`
   - `LogisticRegression(max_iter=1000, class_weight="balanced")`
5. Avalie com 5 métricas: Recall, Precision, F1, AUC-ROC, PR-AUC
6. Registre cada run no MLflow (experiment="churn-baselines"):
   - params: model, random_seed, cv_folds, dataset_hash, pos_weight
   - metrics: recall_mean, precision_mean, f1_mean, roc_auc_mean, pr_auc_mean
7. Tabela comparativa de métricas (highlight melhor por coluna)
8. Curvas ROC e PR sobrepostas por modelo
9. Análise do threshold ótimo para LogisticRegression (Expected Profit = TP×1140 - FP×60 - FN×1200)
10. Conclusão: qual baseline o MLP precisa superar e em qual métrica

Seeds obrigatórios: `RANDOM_SEED = 42` em todo código.
