# Spec: MLP Model (PyTorch)

## Responsabilidade

Classificador binário de churn implementado como MLP em PyTorch.
Dataset: IBM Telco Customer Churn (~7k amostras, ~30 features pós feature-engineering).

## Pré-requisitos

O input do modelo assume features já transformadas por `src/features/pipeline.py`
(StandardScaler em numéricos, ordinal encoding em binários, one-hot em categóricos).

## Arquitetura

```
Input(n_features) → Linear(64) → BatchNorm → ReLU → Dropout(0.3)
                  → Linear(32) → BatchNorm → ReLU → Dropout(0.2)
                  → Linear(1)  → (logit, sem sigmoid — BCEWithLogitsLoss)
```

### Por que 1 nó na saída e não 2?

Para classificação binária (churn/não-churn), 1 nó é suficiente: a saída é um
valor escalar (logit) que, após sigmoid, representa P(Churn). A probabilidade
complementar P(Não-Churn) = 1 - P(Churn) é derivada automaticamente.

Usar 2 nós + softmax seria redundante — as duas probabilidades sempre somam 1,
então o segundo nó não traz informação nova. Para problemas multiclasse (3+
classes) usaríamos N nós + softmax.

### Por que Linear(1) sem sigmoid explícito?

A camada final é `Linear(1)` e produz um **logit** (valor real, sem limites).
O sigmoid não é aplicado na arquitetura porque a loss function
`BCEWithLogitsLoss` já o aplica internamente antes de calcular o erro.

Isso é feito por **estabilidade numérica**: quando sigmoid satura (saída ~0 ou
~1), o `log()` dentro da BCE pode gerar valores infinitos ou gradientes que
explodem. `BCEWithLogitsLoss` combina sigmoid + BCE numa fórmula equivalente
que usa o log-sum-exp trick para evitar esses problemas.

Na inferência, aplica-se `torch.sigmoid(logit)` para obter a probabilidade.

### Justificativa do tamanho

> A Logistic Regression balanceada já atinge Recall 0.802±0.015 / AUC-ROC 0.845±0.013 (StratifiedKFold k=5).
> Redes maiores (256→128→64→32) geram ~45k parâmetros com razão amostras/parâmetros
> de ~125:1, criando alto risco de overfitting sem ganho significativo.
> Escalar somente se houver evidência de underfitting (gap treino-validação pequeno
> com métricas abaixo do target).

## Interface

```python
class ChurnMLP(nn.Module):
    def __init__(self, input_dim: int, hidden: list[int] = [64, 32],
                 dropout: list[float] = [0.3, 0.2]) -> None: ...
    def forward(self, x: torch.Tensor) -> torch.Tensor: ...
```

## Reprodutibilidade

```python
RANDOM_SEED = 42

torch.manual_seed(RANDOM_SEED)
torch.cuda.manual_seed_all(RANDOM_SEED)
torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = False
```

## Treinamento

Valores default definidos em `configs/mlp_default.yaml`. O treino lê esse arquivo
via `src/config.py::load_config()` — nenhum hiperparâmetro é hardcoded no código.

| Parâmetro               | Valor default                          | Ajustável                   |
| ----------------------- | -------------------------------------- | --------------------------- |
| Optimizer               | `AdamW(weight_decay=1e-4)`             | Sim                         |
| LR                      | `1e-3`                                 | Sim                         |
| Weight decay            | `1e-4`                                 | Sim (range `1e-5` a `1e-3`) |
| Loss                    | `BCEWithLogitsLoss(pos_weight=2.7683)` | pos_weight calculado no EDA |
| Epochs                  | `100` (max)                            | Sim                         |
| Batch size              | `32`                                   | Sim                         |
| Early stopping patience | `10`                                   | Sim                         |
| Scheduler               | `ReduceLROnPlateau(patience=5)`        | Opcional                    |

## Hyperparameter Search

Busca via random search (`src/models/search.py`) sobre combinações discretas definidas
na seção `search_space` do config YAML. Cada trial é um treino completo logado como
run separada no MLflow, permitindo comparação no UI.

| Hiperparâmetro | Valores no search space | Justificativa |
|---|---|---|
| `learning_rate` | `[1e-4, 5e-4, 1e-3, 5e-3]` | Abaixo de 1e-4 converge lento demais; acima de 5e-3 instável com AdamW |
| `batch_size` | `[16, 32, 64]` | Menor = mais ruído/generaliza melhor; maior = mais estável/rápido |
| `hidden_dims` | `[32,16]`, `[64,32]`, `[128,64]`, `[128,64,32]` | Varia capacidade; 3 camadas testa profundidade |
| `dropout` | `[0.2,0.1]`, `[0.3,0.2]`, `[0.4,0.3]`, `[0.4,0.3,0.2]` | Alinhado com hidden_dims (rede maior precisa mais regularização) |
| `epochs` | `[50, 100, 150]` | Com early stopping o valor é um teto; variar para ver se mais épocas ajudam |

Total de combinações possíveis: 4×3×4×4×3 = **576**. Random search com `n_trials=10`
amostra um subconjunto representativo.


## Validação

Usar **StratifiedKFold (k=5, seed=42)** para comparação justa com os baselines existentes.
Reportar média ± desvio de todas as métricas nos 5 folds.

Para o modelo final de produção: retreinar no dataset completo (train+val) com os
melhores hiperparâmetros e avaliar no holdout test set.

## Early Stopping

Monitorar `val_loss`. Salvar melhor modelo em `models/mlp_best.pt`. Restaurar ao fim do treino.

## Métricas de avaliação (mínimo 4)

- AUC-ROC
- PR-AUC
- F1 (threshold = 0.5, ajustável)
- Recall ≥ 0.75 (critério de negócio)
- Precision (informativo)

## Threshold

Otimizar threshold via curva PR para maximizar `Expected Profit = TP×1140 - FP×60 - FN×1200`.

## MLflow


| Item              | Valor                                                             |
| ----------------- | ----------------------------------------------------------------- |
| Experiment name   | `churn-mlp`                                                       |
| Params            | Todos da tabela de treinamento + `hidden`, `dropout`, `input_dim` |
| Métricas por fold | Recall, Precision, F1, AUC-ROC, PR-AUC                            |
| Métricas finais   | Média ± std de cada métrica, Expected Profit, threshold ótimo     |
| Artefatos         | `mlp_best.pt`, curva ROC (png), curva PR (png)                    |
| Tags              | `dataset_hash` (do loader), `seed=42`                             |


## Persistência

```python
torch.save(model.state_dict(), "models/mlp_best.pt")
# Para carga:
model = ChurnMLP(input_dim=n)
model.load_state_dict(torch.load("models/mlp_best.pt", weights_only=True))
```

## Testes esperados

- `test_forward_pass_shape` — output shape `(batch, 1)`
- `test_forward_no_nan` — sem NaN nos logits
- `test_training_loss_decreases` — loss cai nas primeiras 5 epochs
- `test_model_saves_and_loads` — state dict salvo/carregado corretamente
- `test_reproducibility` — mesma seed produz mesmos logits

