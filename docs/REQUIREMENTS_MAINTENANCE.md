# Instruções para Manter requirements.txt Sincronizado

## Problema
`uv pip compile` inclui `pywin32==311` (dependência do Docker via MLflow),
que não tem wheels para Linux. Isso quebra CI/CD no GitHub Actions.

## Solução: Remover manualmente na compilação

### Opção 1: Compilar e Filtrar (Recomendada)
```bash
uv pip compile pyproject.toml | grep -v "^pywin32" > requirements.txt
```

**OU em PowerShell (Windows)**:
```powershell
$content = (uv pip compile pyproject.toml)
$content = $content | where { $_ -notmatch "^pywin32" }
$content | Out-File requirements.txt -Encoding UTF8
```

### Opção 2: Usar requirements-windows.txt
Manter dois arquivos:
- `requirements.txt` (Linux/macOS/CI/CD) - sem pywin32
- `requirements-windows.txt` (Windows devs) - com pywin32

### Opção 3: Adicionar ao .uv/config
```yaml
# Adicionar em pyproject.toml [tool.uv]
exclude-platforms = ["win32", "win_amd64"]  # Para deps específicas
```

## Checklist antes de Commit
- [ ] Rodar `uv pip compile pyproject.toml -o requirements.txt`
- [ ] Verificar se pywin32==311 foi incluído: `grep pywin32 requirements.txt`
- [ ] Se sim, remover a linha manualmente
- [ ] Commit requirements.txt

---

**Tomar nota**: Sempre verificar `grep pywin32 requirements.txt` ao atualizar!
