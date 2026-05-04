# Model Training Pipeline Specification

## Objetivo

Modulo `src/models/train.py` responsável pelo treinamento reproduzivel do modelo MLP para previsão de churn de clientes de telecomunicações. Será executado no CI antes dos testes da API, garantindo que os artefatos (modelo, pipeline, config) estejam disponíveis.

## Contexto

- Dataset: `data/processed/telco_churn_cleaned.csv`
- Modelo: MLPChurnModel (PyTorch)
- Pipeline: Scikit-learn com OneHotEncoder, OrdinalEncoder, StandardScaler
- Validação: StratifiedKFold (5 folds)
- Saida: `models/mlp_best.pt`, `models/pipeline.pkl`, `models/mlp_config.json`

## Arquitetura

### Entrada
- CSV com dados processados: 7043 registros, 20 features, target `Churn`
- Sem missing values (já tratados em EDA)

### Processamento
1. Load dataset e split estratificado (70% treino, 30% test)
2. Build scikit-learn pipeline (OHE + OrdinalEncoder + StandardScaler)
3. Treinar MLP com hiperparâmetros otimizados (resultado do grid search)
4. Validação cruzada StratifiedKFold (5 folds)
5. Avaliar em test set holdout
6. Registrar em MLflow

### Saida
- `models/mlp_best.pt`: Weights do modelo treinado
- `models/pipeline.pkl`: Pipeline serializado (joblib)
- `models/mlp_config.json`: Configuração e métricas
- `models/test_results.json`: Resultados no test set

## Configuração do Treinamento

Lida de `models/mlp_config.json` (resultado otimizado do grid search):

```json
{
  "input_dim": 30,
  "hidden_dim": 32,
  "hidden_layers": 2,
  "dropout": 0.4,
  "activation": "relu",
  "batch_size": 64,
  "learning_rate": 0.001,
  "epochs": 100,
  "early_stopping_patience": 5,
  "metrics": {
    "auc_roc": 0.8461972207534021,
    "recall": 0.8389327751573454,
    "precision": 0.49569056995782185,
    "pr_auc": 0.6591510772153965,
    "f1": 0.6228619537316856
  }
}
```

O train.py carrega esta configuracao e treina o modelo com os hiperparametros otimizados.

## Fluxo de Configuração

1. **Load Config**: `load_config()` lê `models/mlp_config.json`
2. **Extract Hyperparams**: Extrai batch_size, learning_rate, epochs, etc
3. **Train with Config**: Passa dict config para `train_best_model()`
4. **Validate Performance**: Verifica se recall >= 0.75
5. **Update Metrics**: Sobrescreve seção "metrics" com novos resultados do test set
6. **Save Config**: Atualiza `models/mlp_config.json` com novas metricas
7. **Log MLflow**: Registra hyperparams e metricas para rastreabilidade

## Observacao

A config nao muda entre execucoes (mesmos hiperparametros sempre). Apenas a seção "metrics" é atualizada com os resultados do novo treinamento. Isso garante reproducibilidade e rastreabilidade.

## Especificação Tecnica

### Modulo: `src/models/train.py`

#### Funcoes Principais

**`load_config(config_path: str) -> dict`**
- Carrega configuracao do arquivo mlp_config.json
- Retorna: dict com hiperparametros e metricas anteriores
- Validacao: verifica se arquivo existe, formato JSON valido

**`train_best_model(X_train, y_train, config, device) -> Tuple[torch.nn.Module, dict]`**
- Treina modelo com hiperparametros do config
- Retorna: modelo treinado e historico de loss
- Aplica early stopping com patience do config

**`evaluate_on_test_set(model, X_test, y_test) -> dict`**
- Avalia modelo em test set holdout (30%)
- Retorna: dict com metricas (AUC-ROC, Recall, Precision, F1, PR-AUC)
- Calcula confusion matrix (TP, FP, FN, TN)

**`save_artifacts(model, pipeline, config_dict, metrics) -> None`**
- Salva modelo em `models/mlp_best.pt` (torch.save)
- Salva pipeline em `models/pipeline.pkl` (joblib.dump)
- Salva config em `models/mlp_config.json` (json.dump)
- Salva metricas test em `models/test_results.json` (json.dump)

**`register_in_mlflow(model, config, metrics) -> None`**
- Log params: todos hiperparametros
- Log metrics: CV e test metrics
- Log model: mlflow.pytorch.log_model()
- Log artifacts: config e test results
- Set tags: model_type, status, dataset_version, random_seed

#### Fluxo Principal

```python
def main():
    # 1. Setup
    set_random_seed(42)
    device = get_device()
    
    # 2. Load configuration from mlp_config.json
    config = load_config('models/mlp_config.json')
    
    # 3. Load data
    df = load_processed_data('data/processed/telco_churn_cleaned.csv')
    X, y = split_features_target(df)
    
    # 4. Split estratificado
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )
    
    # 5. Build pipeline e treinar
    pipeline = build_pipeline()
    X_train_processed = pipeline.fit_transform(X_train)
    X_test_processed = pipeline.transform(X_test)
    
    # 6. Treinar modelo com config otimizado
    model, history = train_best_model(
        X_train_processed, y_train, config, device
    )
    
    # 7. Avaliar em test set
    metrics = evaluate_on_test_set(model, X_test_processed, y_test, device)
    
    # 8. Atualizar config com metricas e salvar
    config['metrics'] = metrics
    save_artifacts(model, pipeline, config, metrics)
    
    # 9. Registrar em MLflow
    register_in_mlflow(model, config, metrics)
    
    # 10. Log summary
    log_summary(metrics)
```

## Conformidade CLAUDE.md

- Random seed: RANDOM_SEED=42 fixo em todo codigo
- Logging: Usar structlog em todos modulos src/, sem print()
- Metrica prioritaria: Recall >= 0.75 (FN custa 20x mais que FP)
- Linting: Passar `ruff check src/models/train.py` sem erros
- Cross-validation: StratifiedKFold (5 folds)
- MLflow: Log params, metrics, model, artifacts

## Integracao CI/CD

### Fluxo no GitHub Actions

```yaml
# .github/workflows/ci.yml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      # 1. Install dependencies
      - run: pip install -e ".[dev]"
      
      # 2. Train model (antes dos testes)
      - run: python src/models/train.py
      
      # 3. Lint
      - run: ruff check src/ tests/
      
      # 4. Run tests (dependem dos artefatos)
      - run: pytest tests/ -v
```

### Artefatos Gerados

Após `python src/models/train.py`, os seguintes arquivos existem:
```
models/
  mlp_best.pt              # Novo
  pipeline.pkl             # Novo
  mlp_config.json          # Novo/Atualizado
  test_results.json        # Novo/Atualizado
```

## Validacoes

### Pre-Treinamento
- Config existe: `models/mlp_config.json`
- Dataset existe: `data/processed/telco_churn_cleaned.csv`
- Sem missing values após load
- Distribuicao de classes mantida em splits (stratify=y)
- Shape esperado: (7043, 21) incluindo target

### During Training
- Loss decreasing em train set
- Early stopping acionado se val_loss nao melhora (patience do config)
- Epoch finaliza antes do limite de epochs (com early stopping)
- Hiperparametros do config sao respeitados

### Post-Training
- Recall >= 0.75 (metrica prioritaria)
- AUC-ROC >= metricas anteriores do config (nao degrada)
- Model weights salvo corretamente (load test)
- Pipeline pode transformar dados novos sem leakage
- Config atualizado com novas metricas test set

### Reproducibilidade
- Mesmo seed=42 produz mesmos weights (torch.manual_seed)
- Mesmo seed produz mesmos folds (StratifiedKFold random_state=42)
- Numpy seed fixo (np.random.seed)

## Dependencias

```python
# PyTorch
import torch
import torch.nn as nn
import torch.optim as optim

# Scikit-learn
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.metrics import roc_auc_score, f1_score, recall_score, precision_score
from sklearn.preprocessing import StandardScaler, OneHotEncoder, OrdinalEncoder

# Pandas, Numpy
import pandas as pd
import numpy as np

# Joblib, JSON
import joblib
import json

# Structlog
import structlog

# MLflow
import mlflow
import mlflow.pytorch

# Local imports
from src.features.pipeline import build_pipeline
from src.config import RANDOM_SEED, MODEL_DIR
```

## Exit Codes

- 0: Sucesso - modelo treinado e salvo
- 1: Dataset nao encontrado
- 2: Recall < 0.75 - modelo nao atende metrica prioritaria
- 3: Erro ao salvar artefatos
- 4: Erro em MLflow registration

## Exemplo de Uso

### Desenvolvimento
```bash
python src/models/train.py
```

### CI/CD (automatico)
Executado no `.github/workflows/ci.yml` apos checkout

### Monitoramento
```bash
mlflow ui --port 5000
# Acessa http://localhost:5000 para visualizar runs
```

## Observacoes

1. **Sem Grid Search**: train.py nao faz grid search. Usa configuracao otimizada do mlp_config.json
2. **Reproducibilidade**: Mesmo seed=42 produz mesmos weights (torch.manual_seed)
3. **Hiperparametros Fixos**: batch_size, learning_rate, epochs sempre os mesmos
4. **Metricas Atualizadas**: Apenas seção "metrics" é atualizada a cada execução
5. **MLflow Tracking**: Todos os runs registrados para comparacao de performance entre treinos
6. **Threshold**: Usa probabilidade >= 0.5 como default (pode ser otimizado com Expected Profit)
7. **Pos Weight**: BCEWithLogitsLoss com pos_weight calculado automaticamente para data desbalanceada
