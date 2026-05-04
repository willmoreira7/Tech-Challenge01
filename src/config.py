from pathlib import Path

import structlog
import yaml

_DEFAULT_CONFIG = Path(__file__).resolve().parent.parent / "configs" / "mlp_default.yaml"


def load_config(path: str | Path = _DEFAULT_CONFIG) -> dict:
    """Load YAML config and return as dict."""
    with open(path) as f:
        return yaml.safe_load(f)


def configure_logging(level: str = "INFO") -> None:
    """Configurar structlog para a aplicação."""
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
