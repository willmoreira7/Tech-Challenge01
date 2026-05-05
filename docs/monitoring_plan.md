# monitoring_plan.md

Plano de monitoramento do modelo em produção.  
Atualizar após Etapa 4 com valores reais de baseline de produção.

---

## Stack de observabilidade (planejada)

Inicialmente pensamos em **Prometheus** (coleta de métricas time-series) + **Grafana** (dashboards e alertas sobre SLIs/SLOs):

- **API / infra:** latência `latency_ms`, taxas 4xx/5xx, throughput, disponibilidade, recursos do host/container — expostas para Prometheus (endpoint `/metrics` ou sidecar) e visualizadas no Grafana.
- **MLflow:** não substitui Prometheus para tempo real; faz sentido como **fonte de verdade de experimentos**, **Model Registry** (versões staging/production) e **runs de avaliação periódica** (job batch semanal que recalcula PR-AUC, Recall, Expected Profit em dados recentes ou rotulados e registra o run para comparar ao baseline de treino).

Fluxo resumido: operação em tempo real → **Prometheus/Grafana**; qualidade e linhagem do modelo → **jobs batch + MLflow** (e opcionalmente métricas derivadas exportadas para Prometheus).

---

## Escolha de testes para data drift (KS vs Chi-quadrado)

- **KS (Kolmogorov–Smirnov):** compara duas distribuições empíricas via funções de distribuição acumulada. Adequado para variáveis **contínuas ou quasi-contínuas** (ex.: `MonthlyCharges`, `log_tenure`, valores numéricos após transformação estável).
- **Chi-quadrado:** testa se as **frequências/contagens entre categorias** diferem entre referência (treino) e produção — adequado para variáveis **categóricas nominais** com poucas modalidades.

**Por que Chi-quadrado para `Contract` e não KS?**  
`Contract` é **nominal** (`Month-to-month`, `One year`, `Two year`, …). O KS pressupõe uma ordenação na variável; aplicá-lo a categorias sem ordem natural é enganoso. A pergunta correta é *“a proporção de cada tipo de contrato mudou?”* → tabela de contingência (referência × produção) → **teste Chi-quadrado** (ou métricas equivalentes como PSI por categoria).

Para outras categóricas (`InternetService`, `PaymentMethod`, `OnlineSecurity`, etc.) vale o mesmo raciocínio: **Chi-quadrado** (ou comparar proporções por categoria com alertas).

---

## Métricas a monitorar

### Performance do modelo

Baseline de referência (holdout / LogisticRegression registrado em `docs/decisions.md`) até existir baseline de produção:


| Métrica                           | Baseline (referência)                 | Alerta amarelo | Alerta vermelho | Frequência |
| --------------------------------- | ------------------------------------- | -------------- | --------------- | ---------- |
| AUC-ROC                           | 0,845                                 | queda > 3 pp   | queda > 5 pp    | semanal    |
| PR-AUC                            | 0,655                                 | queda > 3 pp   | queda > 5 pp    | semanal    |
| Recall                            | ≥ 0,75                                | < 0,73         | < 0,70          | semanal    |
| F1                                | 0,626                                 | queda > 5 pp   | queda > 10 pp   | semanal    |
| Expected Profit (threshold ótimo) | calibrar em validação                 | queda > 10%    | queda > 20%     | semanal    |
| Taxa média de churn **predita**   | comparar ao churn observado histórico | desvio > 10%   | desvio > 20%    | diária     |


Cálculo em produção: usar cohorts com **rotulagem tardia** (30/60/90 dias) quando houver ground truth; até lá, monitorar proxy (taxa predita, distribuição de scores).

### Data drift (distribuição de features)

Monitorar na **mesma granularidade que entra no pipeline** (pré-`engineer_features`: colunas do loader sem `Churn`). Métodos sugestivos:


| Feature / grupo                                                     | Método                                   | Threshold de alerta |
| ------------------------------------------------------------------- | ---------------------------------------- | ------------------- |
| `tenure`                                                            | KS (duas amostras)                       | p-value < 0,05      |
| `MonthlyCharges`                                                    | KS                                       | p-value < 0,05      |
| `SeniorCitizen`                                                     | Chi-quadrado (0/1) ou diff. de proporção | p-value < 0,05      |
| `Contract`                                                          | Chi-quadrado (contagens por categoria)   | p-value < 0,05      |
| `InternetService`                                                   | Chi-quadrado                             | p-value < 0,05      |
| `PaymentMethod`                                                     | Chi-quadrado                             | p-value < 0,05      |
| `OnlineSecurity`, `OnlineBackup`, `DeviceProtection`, `TechSupport` | Chi-quadrado (por feature)               | p-value < 0,05      |
| `Partner`, `Dependents`, `PaperlessBilling`                         | Chi-quadrado                             | p-value < 0,05      |
| Snapshot pós-engineering `log_tenure`                               | KS (opcional, se armazenado)             | p-value < 0,05      |


`TotalCharges`, `gender`, `PhoneService`, `MultipleLines`, `StreamingTV` e `StreamingMovies` **não entram** no modelo atual (`src/features/pipeline.py`); podem seguir sendo monitorados na **fonte** apenas para auditoria de ingestão, não para drift do modelo.

### Métricas operacionais da API


| Métrica                   | SLO      | Alerta    |
| ------------------------- | -------- | --------- |
| Latência p50              | < 100 ms | > 200 ms  |
| Latência p99              | < 500 ms | > 1000 ms |
| Taxa de erro 5xx          | < 0,1%   | > 1%      |
| Taxa de erro 4xx (schema) | < 1%     | > 5%      |
| Disponibilidade           | > 99,5%  | < 99%     |


Instrumentação alinhada ao stack **Prometheus + Grafana** (métricas HTTP e custom `latency_ms`).

---

## Fontes de dados para monitoramento

- **Logs de inferência:** structlog — `churn_probability`, `latency_ms`, `model_version`, inputs relevantes (sem dados sensíveis desnecessários).
- **Ground truth:** comparar predições com churn real após 30/60/90 dias (cohorts).
- **Amostras de entrada:** agregar distribuições para drift (batch diário/semanal).
- **MLflow:** runs periódicos de avaliação com as mesmas métricas da tabela de performance + tags (`environment=production_eval`).

---

## Alertas

### Configuração

```
Canal de alertas: a definir (Slack / PagerDuty / email)
Alertmanager (Prometheus) → integração com canal acima
Responsável de plantão: a preencher
Horário de cobertura: a definir
```

### Regras


| Condição                            | Severidade | Ação imediata                    |
| ----------------------------------- | ---------- | -------------------------------- |
| PR-AUC ou Recall abaixo do vermelho | Crítico    | Acionar playbook de retreino     |
| AUC-ROC caiu > 5 pp vs baseline     | Crítico    | Acionar playbook de retreino     |
| Latência p99 > 1000 ms              | Alto       | Verificar infra e logs (Grafana) |
| Taxa de erro 5xx > 1%               | Alto       | Verificar logs de inferência     |
| Drift detectado em > 3 features     | Médio      | Análise de distribuição          |
| Queda métrica “amarela”             | Médio      | Monitorar por 48 h               |


---

## Playbook de resposta

### Queda de performance (ex.: PR-AUC ou Recall no vermelho)

```
1. Verificar logs — mudança no payload? Features faltando ou tipos errados?
2. Rodar análise de drift nas últimas 2 semanas de dados de entrada
3. Se drift confirmado → acionar retreino com dados recentes
4. Se sem drift → investigar mudança de comportamento real dos clientes
5. Comunicar stakeholders se impacto em produção > 48h
6. Retreinar modelo, registrar run no MLflow, validar antes de promover (Registry)
```

### Erro de inferência (5xx elevado)

```
1. Checar logs estruturados — qual o tipo de erro?
2. Verificar se modelo está carregado (GET /health)
3. Verificar memória e CPU da instância (dashboards Grafana)
4. Se modelo corrompido → rollback para versão anterior no Registry
5. Registrar incidente em docs/decisions.md
```

### Drift de dados detectado

```
1. Identificar features com drift (KS para contínuas; Chi-quadrado para categóricas)
2. Investigar causa — produto? sazonalidade? bug de pipeline?
3. Se bug de pipeline → corrigir e reprocessar
4. Se mudança real → agendar retreino com dados recentes
5. Atualizar baseline de distribuição após retreino válido
```

---

## Retreino


| Trigger                                      | Tipo        | Prazo       |
| -------------------------------------------- | ----------- | ----------- |
| Recall ou PR-AUC no vermelho                 | Emergencial | < 48 h      |
| Drift em > 3 features                        | Planejado   | < 1 semana  |
| Trimestral                                   | Preventivo  | Agendado    |
| Novo volume significativo de dados rotulados | Planejado   | < 2 semanas |


### Processo de retreino

```
1. Coletar dados novos e validar qualidade
2. Rodar pipeline completo de features + treino
3. Comparar métricas: novo vs. atual em conjunto de validação compartilhado
4. Se novo >= política de promoção → atualizar artefato e Registry (MLflow)
5. Registrar experimento no MLflow com tag "retrain"
6. Atualizar model_card / decisions conforme necessário
```

---

## Dashboards

- **Grafana (via Prometheus):** latência p50/p99, taxa de requests, 4xx/5xx, disponibilidade, uso de CPU/memória.
- **MLflow UI:** comparação de runs de avaliação/retraining, linhagem de modelo.
- **Painéis conceituais (negócio):** distribuição de `churn_probability` nas últimas 24 h; taxa predita vs. histórico; volume por hora — podem ser Grafana (métricas agregadas por job) ou notebooks agendados.

