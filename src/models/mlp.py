"""ChurnMLP — classificador binário de churn."""
import torch
import torch.nn as nn

_ACT_MAP = {"relu": nn.ReLU, "tanh": nn.Tanh, "gelu": nn.GELU}


def _hidden_block(in_dim: int, out_dim: int, act_fn, dropout: float) -> list[nn.Module]:
    return [nn.Linear(in_dim, out_dim), nn.BatchNorm1d(out_dim), act_fn(), nn.Dropout(dropout)]


class MLPChurnModel(nn.Module):
    """MLP com interface flat (hidden_dim, hidden_layers, activation)."""

    def __init__(
        self,
        input_dim: int = 30,
        hidden_dim: int = 64,
        hidden_layers: int = 2,
        dropout: float = 0.4,
        activation: str = "relu",
    ) -> None:
        super().__init__()
        act_fn = _ACT_MAP.get(activation, nn.ReLU)
        layers: list[nn.Module] = []
        in_dim = input_dim
        for _ in range(hidden_layers):
            layers.extend(_hidden_block(in_dim, hidden_dim, act_fn, dropout))
            in_dim = hidden_dim
        layers.append(nn.Linear(in_dim, 1))
        self.net = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class ChurnMLP(nn.Module):
    """MLP com interface por lista (hidden: list[int], dropout: list[float])."""

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
        for h, d in zip(hidden, dropout, strict=True):
            layers.extend(_hidden_block(in_dim, h, nn.ReLU, d))
            in_dim = h
        layers.append(nn.Linear(in_dim, 1))
        self.net = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)
