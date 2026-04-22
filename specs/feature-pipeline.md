# Spec: Feature Pipeline

## Responsabilidade

Transformar o DataFrame limpo (pós-loader ou `data/processed/telco_churn_cleaned.csv`) em arrays prontos para treino, com pipeline reprodutível (sklearn).

O pipeline encapsula duas etapas em sequência:
1. **Feature engineering** — cria features derivadas e remove colunas de baixo sinal
2. **Preprocessamento** — impute + scale numéricas, encode binárias, one-hot nominais

## Interface

```python
def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Cria features derivadas e remove colunas de baixo sinal."""

def build_pipeline() -> Pipeline:
    """Retorna pipeline sklearn completo (feature_eng + preprocessor)."""

def fit_transform(pipeline: Pipeline, X_train: pd.DataFrame) -> np.ndarray:
    """Ajusta e transforma treino."""

def transform(pipeline: Pipeline, X: pd.DataFrame) -> np.ndarray:
    """Transforma val/test sem re-ajustar."""
```

## Feature Engineering (step 1)

### Features criadas
- `log_tenure = log(tenure + 1)` — lineariza o decaimento exponencial do churn; **substitui** `tenure`
- `is_fiber` — 1 se `InternetService == "Fiber optic"`, 0 caso contrário; isola o maior driver de churn (41.9%)
- `n_add_on_services` — contagem de serviços adicionais contratados (0-6) entre `OnlineSecurity`, `OnlineBackup`, `DeviceProtection`, `TechSupport`, `StreamingTV`, `StreamingMovies`; proxy de engajamento/lock-in

### Features removidas (baixo sinal no EDA)
- `gender` — churn 26.9% vs 26.2%, sem poder discriminativo
- `PhoneService` — churn 26.7% vs 24.9%, sinal fraco, 90% da base é Yes
- `MultipleLines` — hierarquicamente dependente de `PhoneService`
- `TotalCharges` — correlação 0.826 com `tenure`, redundância conceitual (≈ tenure × MonthlyCharges)
- `StreamingTV` — sinal fraco (~3pp entre No/Yes), redundante com StreamingMovies; "No internet service" já coberto por InternetService/is_fiber; contagem absorvida em n_add_on_services
- `StreamingMovies` — mesma justificativa de StreamingTV

## Transformações por tipo (step 2)

### Numéricas: `log_tenure`, `MonthlyCharges`, `SeniorCitizen`, `n_add_on_services`
- `SimpleImputer(strategy="median")` + `StandardScaler()`

### Categóricas binárias: `Partner`, `Dependents`, `PaperlessBilling`, `is_fiber`
- `OrdinalEncoder(categories=[["No","Yes"], ..., [0,1]])` → 0/1

### Categóricas nominais: `InternetService`, `OnlineSecurity`, `OnlineBackup`, `DeviceProtection`, `TechSupport`, `Contract`, `PaymentMethod`
- `OneHotEncoder(drop="if_binary", sparse_output=False, handle_unknown="ignore")`

## Estrutura sklearn

```python
pipeline = Pipeline([
    ("feature_eng", FunctionTransformer(engineer_features, validate=False)),
    ("preprocessor", ColumnTransformer([
        ("num", num_pipeline, NUM_COLS),
        ("bin", bin_pipeline, BIN_COLS),
        ("cat", cat_pipeline, CAT_COLS),
    ])),
])
```

## Output shape estimado

- NUM: 4 colunas
- BIN: 4 colunas
- CAT (one-hot): ~22 colunas (InternetService(3) + OnlineSecurity(3) + OnlineBackup(3) + DeviceProtection(3) + TechSupport(3) + Contract(3) + PaymentMethod(4))
- **Total: ~30 colunas** (redução de 40 para ~30)

## Persistência

```python
import joblib
joblib.dump(pipeline, "models/pipeline.pkl")
```

## Testes esperados

- `test_pipeline_fit_transform_shape` — output shape correto após fit_transform
- `test_pipeline_no_nan_output` — sem NaN após transform
- `test_pipeline_deterministic` — mesmo input → mesmo output
- `test_unknown_category_handled` — categoria nova não quebra transform
- `test_engineer_features_creates_expected_columns` — novas colunas presentes, removidas ausentes
- `test_engineer_features_log_tenure_range` — `log_tenure` >= 0
- `test_engineer_features_n_add_on_range` — `n_add_on_services` entre 0 e 6
