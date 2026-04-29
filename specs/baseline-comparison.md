# Spec: Baseline Comparison Notebook

**Objetivo:** Comparação interativa de modelos baseline via notebook, rastreando experimentação e métricas em MLflow.

---

## Escopo

Notebook `notebooks/baseline_comparison.ipynb` que executa validação cruzada de múltiplos modelos e consolida resultados.

**Modelos avaliados:**
- DummyClassifier (most_frequent)
- DummyClassifier (stratified)
- LogisticRegression (balanced)
- DecisionTreeClassifier (balanced)
- RandomForestClassifier (balanced)

**Validação:** StratifiedKFold(k=5, shuffle=True, random_state=42)

---

## Estrutura do Notebook

### Célula 1: Setup e Imports
```python
# Imports
import numpy as np
import pandas as pd
from pathlib import Path

from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, f1_score, precision_score, recall_score, 
    roc_auc_score, confusion_matrix, classification_report
)
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier

import mlflow
import mlflow.sklearn

# Config
RANDOM_SEED = 42
TARGET = "Churn"
N_SPLITS = 5
PROJECT_ROOT = Path.cwd()

print(f"🚀 Baseline Comparison Notebook | SEED={RANDOM_SEED} | CV={N_SPLITS}")
```

### Célula 2: Load & Explore Data
- Carregar CSV raw
- Mostrar shape, distribuição de classes
- Verificar nulos em `TotalCharges`
- Output: Tabela descritiva

### Célula 3: Data Cleaning
- Conversão `TotalCharges` → numérico (coerce)
- Encode target: `Churn` {"Yes": 1, "No": 0}
- Drop `customerID`
- Output: `X`, `y` preparados

### Célula 4: Define Preprocessor
- Definir colunas por tipo (NUM, BIN, CAT)
- Montar ColumnTransformer (impute + scale + encode)
- Output: Pipeline preprocessor

### Célula 5: Initialize Models
- Instanciar dict de modelos com seeds fixados
- Logs: `{modelo: pipeline_spec}`

### Célula 6: Cross-Validation Loop
- Iterar StratifiedKFold(5)
- Para cada fold:
  - Fit modelo
  - Predições (y_pred, y_prob)
  - Calcula: accuracy, roc_auc, recall, precision, f1
  - Append a fold_metrics
- Output: DataFrame com fold_metrics

### Célula 7: Aggregate Metrics
- Média e std por modelo
- Log ao MLflow:
  - params: {model, random_seed, cv_folds}
  - metrics: {mean_accuracy, mean_roc_auc, ...}
  - artifacts: telco_churn_cleaned.csv (para rastreabilidade)
- Output: `all_results` dict

### Célula 8: Comparison Table
- DataFrame comparativo (modelo × métrica)
- Formatação: highlight de melhor modelo por métrica
- Mostrar ± std inline

### Célula 9: Visualizations
- Plot 1: Heatmap de métricas (modelo × métrica)
- Plot 2: Box plot de recalls por fold (visualizar variância)
- Plot 3: ROC-AUC vs Recall scatter (trade-off)

### Célula 10: Summary & Next Steps
- Texto markdown com conclusões:
  - Modelo melhor (por métrica)
  - Meta de recall (≥0.75) atingida?
  - Recomendação para próxima fase (MLP)

---

## Inputs

| Fonte | Path |
|-------|------|
| Dataset raw | `data/raw/WA_Fn-UseC_-Telco-Customer-Churn.csv` |
| Config MLflow | SQLite (criar automaticamente em `mlflow.db`) |

---

## Outputs

| Tipo | Path | Descrição |
|------|------|-----------|
| Dataset cleaned | `data/processed/telco_churn_cleaned.csv` | Salvo como artifact no MLflow run |
| MLflow runs | `mlflow.db` | Experiment: `churn-baselines` · 5 runs (um por modelo) |
| Notebook | `notebooks/baseline_comparison.ipynb` | Este arquivo |

---

## Métricas Rastreadas

Por modelo, por fold:
- `accuracy`
- `roc_auc`
- `recall`
- `precision`
- `f1`

Agregadas (média ± std) no MLflow.

---

## Dependências

```
scikit-learn >= 1.0.0
mlflow >= 2.0.0
pandas >= 1.3.0
numpy >= 1.21.0
structlog >= 21.0.0
matplotlib >= 3.4.0
seaborn >= 0.11.0
```

---

## Critérios de Aceitação

- [ ] Notebook executa sem erros (end-to-end)
- [ ] 5 runs MLflow criados (1 por modelo)
- [ ] Tabela comparativa exibe μ ± σ para todas as 5 métricas
- [ ] Recall do LogisticRegression ≥ 0.75 (validar contra decisions.md)
- [ ] Visualizações renderizam sem warnings
- [ ] Dataset cleaned salvo em `data/processed/`

---

## Notas

1. **MLflow tracking:** Setup automático, não exigir login manual
2. **print() em notebooks:** Permitido (diferente de `src/` que exige structlog). Usar para output exploratório interativo.
3. **Reprodutibilidade:** RANDOM_SEED=42 fixado globalmente
