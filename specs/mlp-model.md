# Spec: MLP Model (PyTorch)

## Responsabilidade

Classificador binário de churn implementado como MLP em PyTorch.

## Arquitetura

```
Input(n_features) → Linear(256) → BatchNorm → ReLU → Dropout(0.3)
                  → Linear(128) → BatchNorm → ReLU → Dropout(0.3)
                  → Linear(64)  → BatchNorm → ReLU → Dropout(0.2)
                  → Linear(32)  → ReLU
                  → Linear(1)   → (logit, sem sigmoid — BCEWithLogitsLoss)
```

## Interface

```python
class ChurnMLP(nn.Module):
    def __init__(self, input_dim: int, hidden: list[int] = [256, 128, 64, 32],
                 dropout: list[float] = [0.3, 0.3, 0.2, 0.0]) -> None: ...
    def forward(self, x: torch.Tensor) -> torch.Tensor: ...
```

## Treinamento

| Parâmetro | Valor inicial | Ajustável |
|-----------|--------------|-----------|
| Optimizer | `Adam` | Sim |
| LR | `1e-3` | Sim |
| Loss | `BCEWithLogitsLoss(pos_weight=...)` | pos_weight calculado no EDA |
| Epochs | `100` (max) | — |
| Batch size | `64` | Sim |
| Early stopping patience | `10` | Sim |
| Scheduler | `ReduceLROnPlateau(patience=5)` | Opcional |

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

## Persistência

```python
torch.save(model.state_dict(), "models/mlp_best.pt")
# Para carga:
model = ChurnMLP(input_dim=n)
model.load_state_dict(torch.load("models/mlp_best.pt"))
```

## Testes esperados

- `test_forward_pass_shape` — output shape `(batch, 1)`
- `test_forward_no_nan` — sem NaN nos logits
- `test_training_loss_decreases` — loss cai nas primeiras 5 epochs
- `test_model_saves_and_loads` — state dict salvo/carregado corretamente
