# monitoring_plan.md

Plano de monitoramento do modelo em produção.
Atualizar após Etapa 4 com valores reais de baseline.

---

## Métricas a monitorar

### Performance do modelo

| Métrica | Baseline (treino) | Alerta amarelo | Alerta vermelho | Frequência |
|---------|-------------------|----------------|-----------------|------------|
| AUC-ROC | `a preencher` | queda > 3% | queda > 5% | semanal |
| PR-AUC | `a preencher` | queda > 3% | queda > 5% | semanal |
| F1 | `a preencher` | queda > 5% | queda > 10% | semanal |
| Taxa de churn predita | `a preencher` | desvio > 10% | desvio > 20% | diária |

### Data drift (distribuição de features)

| Feature | Método de detecção | Threshold de alerta |
|---------|-------------------|---------------------|
| `tenure` | KS Test | p-value < 0.05 |
| `MonthlyCharges` | KS Test | p-value < 0.05 |
| `Contract` | Chi-quadrado | p-value < 0.05 |
| `TotalCharges` | KS Test | p-value < 0.05 |
| demais features | `a definir após EDA` | — |

### Métricas operacionais da API

| Métrica | SLO | Alerta |
|---------|-----|--------|
| Latência p50 | < 100ms | > 200ms |
| Latência p99 | < 500ms | > 1000ms |
| Taxa de erro 5xx | < 0.1% | > 1% |
| Taxa de erro 4xx (schema) | < 1% | > 5% |
| Disponibilidade | > 99.5% | < 99% |

---

## Fontes de dados para monitoramento

- **Logs de inferência**: cada request logado com structlog — `churn_probability`, `latency_ms`, `input_features`
- **Ground truth**: comparar predições com churn real após 30/60/90 dias
- **Feature store**: distribuição de features de entrada coletada por request

---

## Alertas

### Configuração

```
Canal de alertas: a definir (Slack / PagerDuty / email)
Responsável de plantão: a preencher
Horário de cobertura: a definir
```

### Regras

| Condição | Severidade | Ação imediata |
|----------|------------|---------------|
| AUC-ROC caiu > 5% | Crítico | Acionar playbook de retreino |
| Latência p99 > 1000ms | Alto | Verificar infra e logs |
| Taxa de erro 5xx > 1% | Alto | Verificar logs de inferência |
| Drift detectado em > 3 features | Médio | Análise de distribuição |
| AUC-ROC caiu > 3% | Médio | Monitorar por 48h |

---

## Playbook de resposta

### Queda de performance (AUC cai > 5%)

```
1. Verificar logs — houve mudança no input? Features faltando?
2. Rodar análise de drift nas últimas 2 semanas de dados
3. Se drift confirmado → acionar retreino com dados recentes
4. Se sem drift → investigar mudança de comportamento real dos clientes
5. Comunicar stakeholders se impacto em produção > 48h
6. Retreinar modelo e validar antes de promover para produção
```

### Erro de inferência (5xx elevado)

```
1. Checar logs estruturados — qual o tipo de erro?
2. Verificar se modelo está carregado corretamente (GET /health)
3. Verificar memória e CPU da instância
4. Se modelo corrompido → fazer rollback para versão anterior
5. Registrar incidente e causa raiz em docs/decisions.md
```

### Drift de dados detectado

```
1. Identificar quais features driftaram (KS Test / Chi-quadrado)
2. Investigar causa — mudança de produto? sazonalidade? bug de pipeline?
3. Se bug de pipeline → corrigir e reprocessar
4. Se mudança real → agendar retreino com dados recentes
5. Atualizar baseline de distribuição após retreino
```

---

## Retreino

| Trigger | Tipo | Prazo |
|---------|------|-------|
| AUC cai > 5% | Emergencial | < 48h |
| Drift em > 3 features | Planejado | < 1 semana |
| Trimestral | Preventivo | Agendado |
| Novo dado > 20% do dataset | Planejado | < 2 semanas |

### Processo de retreino

```
1. Coletar dados novos e validar qualidade (pandera)
2. Rodar pipeline completo — EDA rápida nos novos dados
3. Treinar novo modelo com mesma arquitetura
4. Comparar métricas: novo vs. atual em test set compartilhado
5. Se novo >= atual → promover para produção
6. Registrar experimento no MLflow com tag "retrain"
7. Atualizar model_card.md e decisions.md
```

---

## Dashboard (a implementar)

Métricas a exibir em tempo real:

- Distribuição de `churn_probability` das últimas 24h
- Taxa de churn predita vs. histórico
- Latência p50/p99 por hora
- Volume de requests por hora
- Contagem de erros 4xx e 5xx