---
name: eda
description: Executa análise exploratória do dataset de churn
---

Execute a EDA completa do projeto de churn:

1. Leia `data/raw/dataset.csv` e verifique: shape, tipos, nulos, duplicatas
2. Analise a distribuição do target `Churn` (proporção positiva/negativa)
3. Para features numéricas (`tenure`, `MonthlyCharges`, `TotalCharges`): histograma + boxplot + correlação com target
4. Para features categóricas: contagem por categoria + taxa de churn por categoria
5. Calcule `pos_weight` para BCEWithLogitsLoss: `(n_neg / n_pos)`
6. Identifique features com alta correlação entre si (>0.85)
7. Verifique `TotalCharges` — pode ter valores não numéricos

Ao final, atualize `CLAUDE.md` em "Decisões ativas" com:
- Métrica principal escolhida (justificada pelo desbalanceamento)
- Valor de `pos_weight` calculado
- Features candidatas a drop

Salve os resultados no notebook `notebooks/eda.ipynb`.
