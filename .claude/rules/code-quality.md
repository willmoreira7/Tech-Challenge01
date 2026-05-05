# Regras de Qualidade de Código

Aplicar SEMPRE — tanto ao escrever código novo quanto ao revisar existente.

## Sem duplicação

- Extraia lógica repetida para funções/helpers antes de copiar código.
- Um único `load_pipeline`, um único bloco de construção de layers, uma única verificação de model ready.
- Re-exporte explicitamente com `# noqa: F401` documentado quando necessário.

## Separação de responsabilidades

- Módulos de modelo (`src/models/`) não importam de `src/api/`.
- Handlers não fazem seed global — seeding pertence ao entrypoint de treino.
- Persistência de pipeline fica em `src/features/pipeline.py`, não duplicada em utils.

## Coesão e acoplamento

- Cada módulo tem uma responsabilidade clara. Middleware de log fica em um lugar só.
- Paths de arquivo: sempre `Path(__file__).resolve().parent...` — nunca `Path.cwd()`.
- Constantes de negócio (thresholds, limites) em um lugar; nunca hardcoded em múltiplos pontos.

## Simplicidade

- Não adicione classes/funções sem uso — delete código morto imediatamente.
- Prefira função helper a repetir 4 blocos idênticos de `if not hasattr(...)`.
- `zip(strict=True)` por padrão para detectar listas com tamanhos diferentes.

## Pydantic v2

- Usar `model_config = ConfigDict(...)` — nunca `class Config:` (deprecated).

## Antes de qualquer commit

- `ruff check src/ tests/` sem erros.
- Nenhum símbolo importado sem uso (sem `# noqa: F401` sem justificativa).
- Nenhum arquivo morto no repositório.
