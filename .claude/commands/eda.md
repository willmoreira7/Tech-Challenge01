---
name: eda
description: Executa análise exploratória do dataset de churn. Usar quando o dataset mudar ou quando precisar revisitar decisões de features.
---

Consulte `specs/data-loader.md` para o contrato do loader.

## Estado atual

EDA concluída. Resultados em `notebooks/eda.ipynb`. Decisões registradas em `docs/DECISIONS.md` e `CLAUDE.md`.

**Resultados já obtidos:**
- pos_weight = 2.7683 (5174 neg / 1869 pos)
- Features de maior poder preditivo: `Contract`, `InternetService`, `tenure`, `OnlineSecurity`, `TechSupport`
- Features removidas: `gender`, `PhoneService`, `MultipleLines`, `TotalCharges`, `StreamingTV`, `StreamingMovies`

## Para re-executar (se dataset mudar)

```bash
uv run jupyter nbconvert --to notebook --execute --inplace notebooks/eda.ipynb
```

## Checklist da EDA

1. `pd.read_csv('data/raw/WA_Fn-UseC_-Telco-Customer-Churn.csv')` — shape, tipos, nulos, duplicatas
2. Distribuição do target `Churn` — proporção positiva/negativa → calcular `pos_weight = n_neg / n_pos`
3. Features numéricas (`tenure`, `MonthlyCharges`, `TotalCharges`): histograma + boxplot + correlação com target
4. Features categóricas: contagem por categoria + taxa de churn por categoria
5. Correlação entre features numéricas (>0.85 → candidata a drop)
6. `TotalCharges` — verificar espaços em branco (11 registros com tenure=0)
7. Feature engineering candidatas: `log_tenure`, `is_fiber`, `n_add_on_services`

## Ao final (se houver mudanças)

Atualizar `CLAUDE.md` em "Decisões ativas":
- Valor de `pos_weight` calculado
- Features candidatas a drop (com justificativa)
- Métrica principal escolhida

Seeds: `RANDOM_SEED = 42`.
