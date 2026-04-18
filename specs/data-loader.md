# Spec: Data Loader

## Responsabilidade

Carregar o dataset bruto, validar o schema e retornar um DataFrame limpo e tipado.

## Interface

```python
def load_raw(path: str = "data/raw/dataset.csv") -> pd.DataFrame:
    """Carrega e valida o dataset bruto. Lança SchemaError se inválido."""

def validate_schema(df: pd.DataFrame) -> pd.DataFrame:
    """Valida tipos, nulos permitidos e valores esperados via pandera."""
```

## Schema esperado (pandera)

| Coluna | Tipo | Nulos | Observação |
|--------|------|-------|------------|
| `customerID` | str | Não | Chave única |
| `gender` | str | Não | `Male` / `Female` |
| `SeniorCitizen` | int | Não | `0` / `1` |
| `Partner` | str | Não | `Yes` / `No` |
| `Dependents` | str | Não | `Yes` / `No` |
| `tenure` | int | Não | ≥ 0 |
| `PhoneService` | str | Não | `Yes` / `No` |
| `MultipleLines` | str | Não | — |
| `InternetService` | str | Não | — |
| `OnlineSecurity` | str | Não | — |
| `OnlineBackup` | str | Não | — |
| `DeviceProtection` | str | Não | — |
| `TechSupport` | str | Não | — |
| `StreamingTV` | str | Não | — |
| `StreamingMovies` | str | Não | — |
| `Contract` | str | Não | `Month-to-month` / `One year` / `Two year` |
| `PaperlessBilling` | str | Não | `Yes` / `No` |
| `PaymentMethod` | str | Não | — |
| `MonthlyCharges` | float | Não | > 0 |
| `TotalCharges` | float | Sim | Converter de str; nulos → imputar com mediana |
| `Churn` | str | Não | `Yes` / `No` → converter para int (1/0) |

## Tratamentos obrigatórios

- `TotalCharges`: converter para float (pode conter `" "` → `NaN`) → imputar com mediana
- `Churn`: mapear `{"Yes": 1, "No": 0}`
- Drop `customerID` após validação
- Logar quantidade de nulos encontrados via structlog

## Saída

DataFrame com 19 features + target `Churn` (int), sem `customerID`, sem nulos em features numéricas.

## Testes esperados

- `test_load_returns_dataframe` — retorna DataFrame não vazio
- `test_schema_rejects_missing_column` — lança `SchemaError` sem coluna obrigatória
- `test_total_charges_coercion` — espaços viram NaN e são imputados
- `test_churn_encoded_as_int` — target é 0/1
