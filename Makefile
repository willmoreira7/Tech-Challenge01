.PHONY: install lint test train run mlflow

install:
	uv sync --all-extras

lint:
	uv run ruff check src/ tests/

test:
	uv run pytest tests/ -v

train:
	uv run python src/models/train.py

run:
	uv run uvicorn src.api.app:app --reload

mlflow:
	uv run mlflow ui --port 5000
