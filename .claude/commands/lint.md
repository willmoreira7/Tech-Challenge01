---
name: lint
description: Verifica qualidade de código — ruff + testes unitários. Usar antes de qualquer commit, após refatorações, ou quando quiser confirmar que o projeto está em estado válido.
---

## Checklist "pronto para commit"

```bash
# 1. Lint
uv run ruff check src/ tests/

# 2. Testes unitários (rápidos, sem artefatos de modelo)
uv run pytest tests/unit/ -v

# 3. Suite completa (requer make train ter rodado antes)
uv run pytest tests/ -v --cov=src --cov-report=term-missing
```

## O que verificar

- `ruff check src/ tests/` — zero erros obrigatório antes de qualquer commit
- Sem `# noqa: F401` sem comentário explicando o motivo
- Sem `class Config:` (Pydantic v1 deprecated) — usar `model_config = ConfigDict(...)`
- Sem `Path.cwd()` — usar `Path(__file__).resolve().parent...`
- Sem código morto (arquivos, classes, funções sem uso)
- Sem seeding global fora do entrypoint de treino
- `zip(strict=True)` em chamadas onde os iteráveis devem ter mesmo tamanho

## Se algo quebrar

- `ImportError` em testes: verificar se o símbolo foi movido — atualizar import ou re-exportar
- `ruff I001`: import fora de ordem — `ruff check --fix` corrige automaticamente
- `ruff B905`: `zip()` sem `strict=` — adicionar `strict=True` ou `strict=False` explícito
- Testes de artefatos falhando (`mlp_best.pt not found`): rode `make train` primeiro

Regras completas: `.claude/rules/code-quality.md`.
