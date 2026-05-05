"""ChurnMLP — classificador binário de churn."""
import torch
import torch.nn as nn


class ChurnMLP(nn.Module):
    def __init__(
        self,
        input_dim: int,
        hidden: list[int] | None = None,
        dropout: list[float] | None = None,
    ) -> None:
        super().__init__()
        hidden = hidden or [64, 32]
        dropout = dropout or [0.3, 0.2]

        layers: list[nn.Module] = []
        in_dim = input_dim
        for h, d in zip(hidden, dropout, strict=False):
            layers.extend([
                nn.Linear(in_dim, h),
                nn.BatchNorm1d(h),
                nn.ReLU(),
                nn.Dropout(d),
            ])
            in_dim = h
        layers.append(nn.Linear(in_dim, 1))
        self.net = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)
