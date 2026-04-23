from pathlib import Path

import yaml

_DEFAULT_CONFIG = Path(__file__).resolve().parent.parent / "configs" / "mlp_default.yaml"


def load_config(path: str | Path = _DEFAULT_CONFIG) -> dict:
    """Load YAML config and return as dict."""
    with open(path) as f:
        return yaml.safe_load(f)
