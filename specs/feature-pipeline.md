# Spec: Feature Pipeline

## Responsabilidade

Transformar o DataFrame limpo em tensores/arrays prontos para treino, com pipeline reprodutível (sklearn).

## Interface

```python
def build_pipeline() -> Pipeline:
    """Retorna pipeline sklearn completo (preprocessor + opcional selector)."""

def fit_transform(pipeline: Pipeline, X_train: pd.DataFrame) -> np.ndarray:
    """Ajusta e transforma treino."""

def transform(pipeline: Pipeline, X: pd.DataFrame) -> np.ndarray:
    """Transforma val/test sem re-ajustar."""
```

## Transformações por tipo

### Numéricas: `tenure`, `MonthlyCharges`, `TotalCharges`
- `StandardScaler()` — média 0, desvio 1
- Imputação: `SimpleImputer(strategy="median")` (caso restem nulos)

### Categóricas binárias: `gender`, `Partner`, `Dependents`, `PhoneService`, `PaperlessBilling`
- `OrdinalEncoder(categories=[["Female","Male"], ["No","Yes"], ...])` → 0/1

### Categóricas nominais: `InternetService`, `Contract`, `PaymentMethod`, `MultipleLines`, etc.
- `OneHotEncoder(drop="if_binary", sparse_output=False, handle_unknown="ignore")`

## Seleção de features (opcional, pós-EDA)

- `SelectKBest(f_classif, k=15)` ou `SelectFromModel(LogisticRegression)`
- Decisão final após análise de correlação no EDA

## Estrutura sklearn

```python
preprocessor = ColumnTransformer([
    ("num", num_pipeline, NUM_COLS),
    ("bin", bin_pipeline, BIN_COLS),
    ("cat", cat_pipeline, CAT_COLS),
])
pipeline = Pipeline([("preprocessor", preprocessor)])
```

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
