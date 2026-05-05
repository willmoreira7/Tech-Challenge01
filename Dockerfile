FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# torch CPU-only primeiro (~800 MB vs ~2 GB GPU) — camada separada para cache
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Dependências da API (não mudam a cada deploy de código)
RUN pip install --no-cache-dir \
    "fastapi>=0.115" \
    "uvicorn[standard]>=0.30" \
    "mlflow>=2.12" \
    "scikit-learn>=1.4" \
    "pandas>=2.0" \
    "numpy>=1.26" \
    "structlog>=25.0" \
    "pydantic>=2.0" \
    "joblib>=1.3" \
    "python-dotenv>=1.0"

# Código fonte (camada mais frequente — rebuild rápido)
COPY src/ ./src/
COPY configs/ ./configs/

ENV PYTHONPATH=/app

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "2"]
