# 🎯 ML Canvas - Previsão de Churn em Telecomunicações (Brasil)

**Metodologia:** CRISP-DM | **Status:** Fase 1 - Planejamento | **Data:** 16/04/2026 | **Versão:** 3.0 (Brasil)

---

## 📋 Índice

1. [Contexto e Objetivos de Negócio](#1-contexto-e-objetivos-de-negócio)
2. [Stakeholders e Governança](#2-stakeholders-e-governança)
3. [Análise de Segmentos (Pós-Pago vs Pré-Pago)](#3-análise-de-segmentos-pós-pago-vs-pré-pago)
4. [Características do Dataset](#4-características-do-dataset)
5. [Metas de Performance Técnica](#5-metas-de-performance-técnica)
6. [Análise Econômica: Trade-off de Custos (Brasil 2026)](#6-análise-econômica-trade-off-de-custos-brasil-2026)
7. [Estratégia de Calibração Threshold](#7-estratégia-de-calibração-threshold)
8. [KPIs de Sucesso (Negócio × Técnico)](#8-kpis-de-sucesso-negócio--técnico)
9. [SLOs de Serviço](#9-slos-de-serviço)
10. [Monitoramento e Drift Detection](#10-monitoramento-e-drift-detection)
11. [Roadmap de Implementação](#11-roadmap-de-implementação)

---

## 1. Contexto e Objetivos de Negócio

### 1.1 Realidade do Mercado Brasileiro 2026

**Context Macro:**

- Base total de clientes Brasil: **~260 milhões de linhas** (móvel+fixo+banda larga)
- Portabilidades em 2025: **8,5 milhões** (recorde) - fenômeno crítico
- Churn mensal agregado (Brasil): **2,0% - 3,0%**
- Impacto financeiro: **~104-156 milhões** de linhas por ano em risco

### 1.2 Problema de Negócio Específico

> **Referência de Siglas:**
>
> - **ARPU:** Average Revenue Per User (Receita Média por Usuário/mês)
> - **CLV:** Customer Lifetime Value (Valor Presente do Cliente ao longo da vida)
> - **SAC:** Sales Acquisition Cost (Custo de Aquisição de Novo Cliente)

Uma operadora de telecomunicações brasileira enfrenta:

**Segmento Pós-Pago:**

- Churn mensal: **0,98% - 1,4%**
- ARPU: **R$ 50 - 55/mês**
- CLV líquido: **R$ 800 - 1.500** (24 meses)
- SAC: **R$ 150 - 500**
- Base estimada: **70 milhões de linhas**

**Segmento Pré-Pago:**

- Churn mensal: **3,0% - 6,0%** (muito maior!)
- ARPU: **R$ 12 - 18/mês**
- CLV líquido: **R$ 60 - 200** (muito menor)
- SAC: **R$ 20 - 50**
- Base estimada: **190 milhões de linhas**

**Impacto Financeiro Anual (Base Pós-Pago de 70M):**

```
Churn Rate = 1,2% (média)
Churners/ano = 70M × 0.012 = 840.000 clientes/ano

Receita perdida = 840.000 × R$ 50 × 12 = R$ 504 milhões/ano
CLV perdido = 840.000 × R$ 1.200 = R$ 1.008 bilhões!
```

**Desafio Crítico:**
Identificar **proativamente** clientes em risco de cancelamento nos próximos **30-60 dias** para viabilizar campanhas de retenção (desconto, upgrade, bundling), evitando portabilidades e churn.

### 1.3 Métrica Central: Lucro Esperado

O modelo será avaliado via **Lucro Esperado**, que consolida performance técnica com realidade econômica brasileira:

$$\text{EP} = (\text{TP} \times \text{Lucro}*{\text{retenção}}) - (\text{FP} \times \text{Custo}*{\text{campanha}}) - (\text{FN} \times \text{CLV}_{\text{perdido}})$$

**Parâmetros para Segmento Pós-Pago:**

- **TP (Churner detectado + retido):** 
  - CLV salvo: R$ 1.200
  - Custo campanha: R$ 60
  - **Lucro líquido: R$ 1.140**
- **FP (Não-churner recebe campanha desnecessária):**
  - Custo campanha: R$ 60
  - **Prejuízo: -R$ 60**
- **FN (Churner não detectado, perde cliente):**
  - CLV perdido: R$ 1.200
  - **Prejuízo: -R$ 1.200**

**Razão de Custo (FN vs FP):**
$$\text{Taxa} = \frac{\text{Prejuízo}*{\text{FN}}}{\text{Custo}*{\text{FP}}} = \frac{1.200}{60} = 20:1$$

**Insight Crítico:** FN é **20x mais caro** que FP (pós-pago). Para pré-pago, ainda pior!

---

### 1.4 Métrica Técnica Derivada: RECALL ≥ 75%

> **Conexão Negócio ↔ Técnico**
>
> Da análise de Lucro Esperado acima, deriva-se a **métrica técnica PRIMARY**:
>
> - Para maximizar EP, minimizamos FN (Falsos Negativos)
> - Minimizar FN = **Maximizar Recall** (TP / (TP + FN))
> - Mathematicamente: `Threshold ótimo ≈ 5%` implica **Recall ≥ 75%** obrigatório
> - Então: **O modelo será otimizado e treinado com Recall ≥ 75% como objetivo primário**
>
> Ver detalhes em **[Seção 5.0 - Métrica Técnica PRIMARY: RECALL](##-50--métrica-técnica-primary-recall)**.

---

## 2. Stakeholders e Governança

### 2.1 Mapa de Stakeholders

```
┌──────────────────────────────────────────────────────────────┐
│                    STAKEHOLDERS MAP                          │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  SPONSOR        │  VP de Receita / Diretor Executivo         │
│  ├─ Objetivo: Reduzir churn em -2% (ganho 1.68M clientes)    │
│  ├─ ROI esperado: ≥ 5:1 em 12 meses                          │
│  ├─ Budget: R$ 2-5 milhões para implementação                │
│  └─ SLA: Impacto positivo em 6 meses                         │
│                                                              │
│  CRM TEAM       │  Gerentes e Analistas de Retenção          │
│  ├─ Recebem scores de churn diariamente (ranking)            │
│  ├─ Executam campanhas via SMS/Email/WhatsApp                │
│  ├─ SLA: Contato em 24h pós-alerta, taxa contato ≥ 80%       │
│  └─ Feedback loop: Reportar conversão/churn real mensal      │
│                                                              │
│  ENGINEERS      │  Data Engineering / MLOps                  │
│  ├─ Deploy da API FastAPI em produção                        │
│  ├─ SLA: Uptime ≥ 99.5%, latência p99 ≤ 200ms                │
│  ├─ Monitoramento H24 via Prometheus + DataDog               │
│  └─ Retrainamento automático semanal                         │
│                                                              │
│  DATA TEAM      │  Data Scientists / Analytics Engineers     │
│  ├─ Desenvolvimento e otimização do modelo                   │
│  ├─ Feature engineering (20+ features)                       │
│  ├─ Documentação: Model Card + viés + limitações             │
│  └─ A/B testing de campanhas vs modelo                       │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 Responsabilidades por Fase


| Fase                 | Owner     | Entregável              | SLA       |
| -------------------- | --------- | ----------------------- | --------- |
| **Explor./Modeling** | Data Team | Modelo com AUROC ≥ 0.82 | 4 semanas |
| **Deployment**       | MLOps     | API em produção com SLA | 2 semanas |
| **Operação**         | CRM Team  | Campanhas executadas    | Daily     |
| **Monitoring**       | MLOps     | Dashboard + alertas     | 24/7      |
| **Retraining**       | Data Team | Modelo retreinado       | Semanal   |


---

## 3. Análise de Segmentos (Pós-Pago vs Pré-Pago)

### 3.1 Comparação de Parâmetros Econômicos


| Parâmetro        | Pós-Pago     | Pré-Pago   | Impacto                 |
| ---------------- | ------------ | ---------- | ----------------------- |
| **Churn Mensal** | 0,98-1,4%    | 3,0-6,0%   | Pré é 3-6x maior ⚠️     |
| **ARPU**         | R$ 50-55     | R$ 12-18   | Pós é 3-4x maior        |
| **CLV (24m)**    | R$ 800-1.500 | R$ 60-200  | Pós é 4-7x maior        |
| **SAC**          | R$ 150-500   | R$ 20-50   | Pós é 3-10x maior       |
| **Razão FN/FP**  | 10:1 - 15:1  | 5:1 - 10:1 | Ambas pedem Recall alto |
| **Base Brasil**  | ~70M         | ~190M      | Pré é 2.7x maior        |


### 3.2 Calibração por Segmento

**Estratégia Pós-Pago (Foco: Alto CLV)**

```
├─ Recall mínimo: ≥ 0.75 (não deixar CLV alto escapar)
├─ Threshold: ~0.25 (agressivo, FN é caro)
└─ Investimento em campanha: R$ 60/cliente (pode ser agressivo)
```

**Estratégia Pré-Pago (Foco: Volume)**

```
├─ Recall mínimo: ≥ 0.70 (churn já é natural)
├─ Threshold: ~0.35 (pouco mais conservador)
└─ Investimento em campanha: R$ 15/cliente (automação SMS)
```

### 3.3 Estimativa de Impacto (Ano 1)

**Cenário Pós-Pago com Modelo AUROC=0.85, Recall=0.80:**

```
Base analisada: 70 milhões clientes
Churn esperado/mês: 0.012 × 70M = 840.000
Churners detectados (Recall=0.80): 672.000
Campanhas disparadas (Precision=0.65): 672.000
Custo campanha: 672.000 × R$ 60 = R$ 40.32M

Cenários de Conversão:
├─ Low: 20% conversion → 134.400 retidos
│  EP = 134.400 × R$ 1.140 - R$ 40.32M = R$ 313M
│  ROI = 313M / 40.32M = 7.8:1
│
├─ Mid: 30% conversion → 201.600 retidos
│  EP = 201.600 × R$ 1.140 - R$ 40.32M = R$ 189.5M
│  ROI = 189.5M / 40.32M = 4.7:1
│
└─ High: 40% conversion → 268.800 retidos
   EP = 268.800 × R$ 1.140 - R$ 40.32M = R$ 266M
   ROI = 266M / 40.32M = 6.6:1
```

**Conclusão:** Modelo é **altamente rentável** mesmo com taxa de conversão conservadora (20%).

---

## 4. Características do Dataset

### 4.1 Especificação Técnica


| Aspecto           | Especificação                                              |
| ----------------- | ---------------------------------------------------------- |
| **Fonte**         | Sistema de CRM + Network Data + Billing System             |
| **Tamanho**       | ≥ 5.000 registros (mínimo); ideal 100K+ para cada segmento |
| **Timeframe**     | 24 meses histórico (captura sazonalidade anual)            |
| **Target**        | `churn` (0 = retido, 1 = churned) → BINÁRIA DESBALANCEADA  |
| **Desequilíbrio** | Pós: ~1,2% churn; Pré: ~4,5% churn                         |
| **Granularidade** | Account-level (um registro = um cliente)                   |


### 4.2 Variáveis Preditoras (20+ Features)

#### **Categoria 1: Demográficos**


| Feature        | Tipo       | Range           |
| -------------- | ---------- | --------------- |
| `age`          | Contínua   | 18-80 anos      |
| `gender`       | Categórica | M/F             |
| `region`       | Categórica | 27 (estados BR) |
| `income_class` | Categórica | A,B,C,D,E       |


#### **Categoria 2: Relacionamento & Histórico**


| Feature                     | Tipo       | Descrição            |
| --------------------------- | ---------- | -------------------- |
| `tenure_months`             | Contínua   | Meses como cliente   |
| `contract_type`             | Categórica | Pós/Pré/Controle     |
| `contract_length_months`    | Discreta   | Duração contrato     |
| `monthly_recurring_revenue` | Contínua   | ARPU real do cliente |
| `customer_lifetime_value`   | Contínua   | CLV estimado         |


#### **Categoria 3: Padrão de Uso**


| Feature                   | Tipo     | Descrição            |
| ------------------------- | -------- | -------------------- |
| `total_usage_gb_last_30d` | Contínua | Consumo de dados     |
| `voice_minutes_last_30d`  | Contínua | Minutos falados      |
| `sms_count_last_30d`      | Discreta | SMSs enviados        |
| `payment_delay_days`      | Discreta | Dias atraso médio    |
| `bill_amount_variance`    | Contínua | Variabilidade fatura |


#### **Categoria 4: Portfólio de Serviços**


| Feature               | Tipo     | Descrição                           |
| --------------------- | -------- | ----------------------------------- |
| `num_services_active` | Discreta | Qte serviços (voz, SMS, dados, etc) |
| `has_data_plan`       | Binária  | Internet contratada?                |
| `has_roaming`         | Binária  | Roaming internacional?              |
| `has_insurance`       | Binária  | Seguro do dispositivo?              |


#### **Categoria 5: Sinais Comportamentais (Engineered)**


| Feature                       | Tipo     | Descrição                           |
| ----------------------------- | -------- | ----------------------------------- |
| `inactivity_days_max_30d`     | Discreta | Maior período sem uso (últimos 30d) |
| `support_tickets_last_90d`    | Discreta | Tickets abertos                     |
| `complaint_resolution_rate`   | Contínua | % reclamações resolvidas            |
| `customer_satisfaction_score` | Ordinal  | 1-5 (NPS)                           |
| `days_since_last_interaction` | Discreta | Dias última compra/uso              |


### 4.3 Qualidade de Dados Esperada

```
├─ Missing Values:        < 1% (imputação KNN contínuas, moda categóricas)
├─ Outliers:             Detecção via IQR 1.5×range, validação com domínio
├─ Duplicatas:           < 0.1% (remover CPF/email duplicados)
├─ Consistência:         Validação de ranges, tipos, relacionamentos
├─ Balanceamento:        1-6% churn → SMOTE ou class_weight crítico
└─ Temporal:             Sem data leakage, features lagged corretamente
```

---

## 5. Metas de Performance Técnica

### 5.0 🎯 Métrica Técnica PRIMARY: RECALL

> **Decisão Estratégica**: O modelo será otimizado para **Recall ≥ 75%** como métrica técnica PRIMARY.
>
> **Por quê?** 
>
> - Objetivo de negócio é **detectar e reter churners** antes de perderem
> - Falsos Negativos (churner não detectado) custam **R$ 1.200** (CLV perdido)
> - Falsos Positivos (campanha desnecessária) custam apenas **R$ 60**
> - **Taxa FN/FP = 20:1** → Minimizar FN (maximize Recall) é essencial
> - Matematicamente: `Threshold ótimo ≈ 5%` → Recall agressivo obrigatório
>
> **Implicação**: É preferível enviar 100 campanhas (com 25% desnecessárias) para garantir que 75%+ dos verdadeiros churners sejam retidos.

### 5.1 Critérios de Sucesso (Calibrados para Brasil)

#### **Métrica 1: AUROC (Area Under ROC Curve)**

$$\text{AUROC} = \int_0^1 TPR(\theta)  d(FPR(\theta))$$

**Interpretação:** Probabilidade de modelo rankear churner real acima de não-churner.


| Faixa       | Interpretação | Decisão                   |
| ----------- | ------------- | ------------------------- |
| ≥ 0,88      | Excelente     | ✅ Aprovado imediato       |
| 0,82 - 0,88 | Bom           | ✅ Aprovado                |
| 0,75 - 0,82 | Aceitável     | ⚠️ Monitorar intensamente |
| < 0,75      | Fraco         | ❌ Rejeitar                |


**Meta:** AUROC ≥ 0,82 (aceitável), ideal ≥ 0,88

---

#### **Métrica 2: Recall (Sensibilidade)**

$$\text{Recall} = \frac{TP}{TP + FN}$$

**Interpretação:** De todos os churners reais, quantos o modelo detectou?

**Justificativa Matemática para Recall Agressivo:**

Razão de custo (FN vs FP) para pós-pago:
$$\text{Taxa} = \frac{\text{CLV}*{\text{perdido}}}{\text{Custo}*{\text{campanha}}} = \frac{R 1.200}{R 60} = 20:1$$

Equação econômica ótima:
$$\text{Threshold ótimo}^* = \frac{\text{Custo}*{\text{FP}}}{\text{Custo}*{\text{FP}} + \text{Ganho}_{\text{TP}}} = \frac{60}{60 + 1.140} = 0.050$$

**Resultado:** Threshold ~5% (muito baixo!) → **Recall ≥ 75% obrigatório**


| Faixa       | Interpretação | Decisão                |
| ----------- | ------------- | ---------------------- |
| ≥ 0,80      | Excelente     | ✅ Aprovado             |
| 0,75 - 0,80 | Adequado      | ✅ Aprovado             |
| 0,70 - 0,75 | Borderline    | ⚠️ Aceitar com cuidado |
| < 0,70      | Insuficiente  | ❌ Rejeitar (muitos FN) |


**Meta:** Recall ≥ 0,75

---

#### **Métrica 3: Precision**

$$\text{Precision} = \frac{TP}{TP + FP}$$

**Interpretação:** De todas as alertas geradas, quantas estão corretas?


| Faixa Esperada | Significado                                     |
| -------------- | ----------------------------------------------- |
| 0,55 - 0,75    | Normal em desbalanceado com Recall alto         |
| < 0,55         | Muitos FP (revisar threshold)                   |
| > 0,75         | Muito conservador (está desperdiçando detecção) |


**Meta Faixa:** 0,55 - 0,75

---

#### **Métrica 4: F1-Score**

$$\text{F}_1 = 2 \times \frac{\text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}}$$

Harmônica de Precision/Recall. NÃO é métrica principal, mas indica balanceamento.


| Faixa       | Interpretação              |
| ----------- | -------------------------- |
| ≥ 0,70      | Balanceamento adequado     |
| 0,65 - 0,70 | Aceitável (foco em Recall) |
| < 0,65      | Revisar trade-off          |


**Meta:** F1-Score ≥ 0,70

---

#### **Métrica 5: PR-AUC (Precision-Recall AUC)**

$$\text{PR-AUC} = \int_0^1 \text{Precision}(\theta)  d(\text{Recall}(\theta))$$

**Por que é crítico para Churn:**

- Baseline aleatório = % positivos (~1-5% para pós-pago)
- PR-AUC penaliza FP muito mais que AUROC
- **Métrica principal para dados desbalanceados**


| Valor       | Interpretação | Decisão                  |
| ----------- | ------------- | ------------------------ |
| ≥ 0,65      | Aceitável     | ✅ Monitore               |
| 0,55 - 0,65 | Borderline    | ⚠️ Intenso monitoramento |
| < 0,55      | Problemático  | ❌ Rejeitar               |


**Meta:** PR-AUC ≥ 0,65

---

### 5.2 Matriz de Aceitação Final

```
AUROC  │ Recall  │ F1    │ PR-AUC  │ Aprovado?  │ Ação
───────┼─────────┼───────┼─────────┼────────────┼──────────────────
≥0.88  │ ≥0.80   │ ≥0.72 │ ≥0.70   │ ✅ SIM     │ Deploy imediato
0.82-88│ 0.75-80 │ 0.68-72│ 0.65-70 │ ✅ SIM     │ Deploy com monitor
0.75-82│ 0.70-75 │ 0.65-68│ 0.60-65 │ ⚠️ TALVEZ  │ Retrainamento
<0.75  │ <0.70   │ <0.65 │ <0.60   │ ❌ NÃO    │ Rejeitar
```

**Regra de Decisão Automática:**

```python
if (AUROC >= 0.82) AND (Recall >= 0.75) AND (PR_AUC >= 0.65):
    aprovado_para_producao = True
    alerta_monitoramento = False
elif (AUROC >= 0.78) AND (Recall >= 0.70) AND (PR_AUC >= 0.60):
    aprovado_para_producao = True
    alerta_monitoramento = True  # ⚠️ Intensificar
else:
    aprovado_para_producao = False
    retrainamento_recomendado = True
```

---

## 6. Análise Econômica: Trade-off de Custos (Brasil 2026)

### 6.1 Matriz de Confusão com Impacto em Reais

```
                    │  Predição: Churner │  Predição: Retentor
                    │   (Campanh Enviada)│    (Sem Ação)
────────────────────┼────────────────────┼────────────────────
Real: Churner       │ TP: Lucro R$ 1.140 │ FN: Prejuízo -R$ 1.200
Real: Retentor      │ FP: Custo -R$ 60   │ TN: Neutro R$ 0
────────────────────┴────────────────────┴────────────────────

Pós-Pago (R$ 50-55 ARPU, R$ 800-1500 CLV):
├─ TP = CLV (R$ 1.200) - Campanha (R$ 60) = +R$ 1.140
├─ FP = -R$ 60 (campanha desperdiçada)
├─ FN = -R$ 1.200 (churn não evitado)
└─ TN = R$ 0 (cliente mantém já planejado)

Pré-Pago (R$ 12-18 ARPU, R$ 60-200 CLV):
├─ TP = CLV (R$ 150) - Campanha (R$ 15) = +R$ 135
├─ FP = -R$ 15 (campanha desperdiçada)
├─ FN = -R$ 150 (churn não evitado)
└─ Razão FN/FP = 150/15 = 10:1 (ainda agressiva)
```

### 6.2 Fórmula do Expected Profit

$$\text{EP}(\theta) = \sum_{i=1}^{N} \begin{cases}
+1.140 & \text{if } score_i > \theta \text{ AND } churner 
-60 & \text{if } score_i > \theta \text{ AND } não-churner 
-1.200 & \text{if } score_i \leq \theta \text{ AND } churner 
0 & \text{if } score_i \leq \theta \text{ AND } não-churner
\end{cases}$$

### 6.3 Exemplos Numéricos com Base Brasil

**Cenário 1: Base Pós-Pago 1M clientes (1,2% churn = 12.000 churners)**

**Modelo com AUROC=0.82, Recall=0.75:**

```
TP = 12.000 × 0.75 = 9.000   → Lucro: 9.000 × R$ 1.140 = R$ 10.26M
FN = 12.000 × 0.25 = 3.000   → Prejuízo: 3.000 × R$ 1.200 = R$ 3.6M
FP = 988.000 × 0.10 = 98.800 → Custo: 98.800 × R$ 60 = R$ 5.93M
TN = 988.000 × 0.90 = 889.200 → Neutro: R$ 0

Expected Profit = R$ 10.26M - R$ 3.6M - R$ 5.93M 
                = R$ 730K/base 1M
```

**Cenário 2: Mesmo modelo com Recall=0.80:**

```
TP = 12.000 × 0.80 = 9.600   → Lucro: 9.600 × R$ 1.140 = R$ 10.94M
FN = 12.000 × 0.20 = 2.400   → Prejuízo: 2.400 × R$ 1.200 = R$ 2.88M
FP = 988.000 × 0.12 = 118.560→ Custo: 118.560 × R$ 60 = R$ 7.11M
TN = 988.000 × 0.88 = 869.440 → Neutro: R$ 0

Expected Profit = R$ 10.94M - R$ 2.88M - R$ 7.11M 
                = R$ 950K/base 1M
```

**Conclusão:** Cada 1% de aumento em Recall = **+R$ 220K de lucro** (base 1M)!

---

## 7. Estratégia de Calibração Threshold

### 7.1 Threshold Ótimo Baseado em Custos

**Derivação Teórica:**

Para maximizar Expected Profit, o threshold ótimo é:

$$\theta^* = \frac{\text{Custo}*{\text{FP}}}{\text{Custo}*{\text{FP}} + \text{Ganho}_{\text{TP}}} = \frac{60}{60 + 1.140} = 0.050$$

**Interpretação:**

- Alertar clientes com **P(churn) > 5%** (muito baixo vs padrão de 50%)
- Isso maximiza Recall (captura até churners "improvável")
- Aceita muitos FP, mas evita FN caros

### 7.2 Otimização Iterativa

```python
best_threshold = 0.5
best_profit = -infinity

for threshold in np.linspace(0.01, 0.99, 100):
    y_pred = (y_proba >= threshold).astype(int)
    TP = ((y_pred == 1) & (y_true == 1)).sum()
    FP = ((y_pred == 1) & (y_true == 0)).sum()
    FN = ((y_pred == 0) & (y_true == 1)).sum()
    TN = ((y_pred == 0) & (y_true == 0)).sum()
    
    # Expected Profit em Reais
    profit = TP * 1140 - FP * 60 - FN * 1200 + TN * 0
    
    if profit > best_profit:
        best_profit = profit
        best_threshold = threshold

optimal_threshold = best_threshold  # Esperado: 0.05-0.15
```

### 7.3 Visualização: Expected Profit vs Threshold

```
Expected Profit (R$)
         │
    15M  │                    ╱╲
         │                  ╱    ╲      ← Peak Profit
    10M  │               ╱         ╲
         │              ╱            ╲
     5M  │            ╱               ╲
         │          ╱                   ╲
      0  │─────────╱──────────────────────╲──────
         │       ╱                          ╲
    -5M  │     ╱                             ╲
         │   ╱                                ╲
   -10M  │╱__________________________________╲____
         └──────┬──────┬──────┬──────┬──────┬──────
              0.01  0.05  0.10  0.20  0.50  0.99
              
              θ* ≈ 0.08 (Ótimo Econômico)
```

---

## 8. KPIs de Sucesso (Negócio × Técnico)

### 8.1 KPIs de Negócio (O que importa para Executivos)


| KPI                            | Meta      | Cálculo                         | Frequência |
| ------------------------------ | --------- | ------------------------------- | ---------- |
| **Expected Profit Mensal**     | ≥ R$ 2M   | ∑TP×1.140 - ∑FP×60 - ∑FN×1.200  | Diária     |
| **Taxa de Prevenção de Churn** | ≥ 40%     | (TP / Total_Churners) × 100     | Semanal    |
| **Churn Reduzido (%)**         | -1,0 pp   | (Churn_base - Churn_com_modelo) | Mensal     |
| **Impacto Anual Estimado**     | ≥ R$ 100M | EP_mensal × 12 × N_clientes     | Trimestral |
| **ROI da Solução**             | ≥ 5:1     | (Benefício - Custo) / Custo     | Anual      |


### 8.2 KPIs Técnicos (Monitoramento 24/7)


| KPI                           | Meta      | Alerta        | Frequência |
| ----------------------------- | --------- | ------------- | ---------- |
| **AUROC (Produção)**          | ≥ 0.82    | < 0.80 por 3d | Diária     |
| **Recall (Produção)**         | ≥ 0.75    | < 0.70 por 2d | Diária     |
| **PR-AUC (Produção)**         | ≥ 0.65    | < 0.60 por 2d | Semanal    |
| **Data Drift (KS Test)**      | KS < 0.15 | KS > 0.20     | Semanal    |
| **Model Drift (AUROC Queda)** | Estável   | > -5% em 7d   | Diária     |


### 8.3 Mapping Técnica → Negócio

```
AUROC 0.85        │
Recall 0.77       ├─→ TP = 77% de churners capturados
Precision 0.65    │    FP = 35% de não-churners alertas
                  │
                  ├─→ Base 1M (12K churners):
                  │    TP = 9.240
                  │    FP = 15.643
                  │
                  ├─→ Expected Profit = R$ 9.35M/1M clientes
                  │
                  └─→ Revenue Impact = R$ 1.122 bilhões/ano (70M base)
                      = +1,8pp em receita anual
```

---

## 9. SLOs de Serviço

### 9.1 Service Level Objectives para API FastAPI


| SLO              | Objetivo    | Medida         | Impact se quebrar          |
| ---------------- | ----------- | -------------- | -------------------------- |
| **Uptime**       | ≥ 99.5%     | Heartbeat 24/7 | Campanha potencial perdida |
| **Latência p50** | ≤ 100ms     | APM (DataDog)  | Detecção mais lenta        |
| **Latência p99** | ≤ 200ms     | APM            | SLA do CRM atingido        |
| **Throughput**   | ≥ 500 req/s | Load testing   | Não escala para 70M base   |
| **Error Rate**   | ≤ 0.1%      | Logs de app    | Perda de histórico         |


### 9.2 Endpoints da API

**Endpoint 1: `/predict/single` (1 cliente)**

```http
POST /api/v1/predict/single HTTP/1.1

{
    "customer_id": "12345678",
    "age": 42,
    "tenure_months": 24,
    "monthly_recurring_revenue": 52.50,
    "num_services": 4,
    ...
}

HTTP 200 OK
{
    "customer_id": "12345678",
    "churn_probability": 0.68,
    "churn_prediction": "sim",
    "risk_level": "alto",
    "recommended_action": "Contato em 24h",
    "model_version": "v2.5.1",
    "latency_ms": 47
}
```

**Endpoint 2: `/predict/batch` (N clientes)**

```http
POST /api/v1/predict/batch

{
    "customers": [{...}, {...}, ...]  # 100K clientes
}

HTTP 200 OK
{
    "predictions": [...],
    "processed_count": 100000,
    "latency_ms": 45000  # 45 segundos total
}
```

**Endpoint 3: `/health` (monitoramento)**

```http
GET /api/v1/health

HTTP 200 OK
{
    "status": "healthy",
    "model_version": "v2.5.1",
    "last_retraining": "2026-04-10T02:00:00Z",
    "auroc_last_validation": 0.852,
    "recall_last_validation": 0.785,
    "days_since_retrain": 6
}
```

---

## 10. Monitoramento e Drift Detection

### 10.1 Tipos de Drift

**Data Drift (Distribuição muda):**

```python
from scipy.stats import ks_2samp

ks_stat, p_value = ks_2samp(X_train['feature'], X_prod_recent['feature'])
if ks_stat > 0.15:
    trigger_retraining()  # Distribuição mudou muito
```

**Model Drift (Performance cai):**

```python
auroc_baseline = 0.850  # Produção
auroc_recent = calcular_auroc(y_true_recent, y_pred_recent)

if auroc_recent < 0.80:  # Queda de 5%
    trigger_retraining()  # Modelo se degradou
```

**Concept Drift (Comportamento muda):**

```
# Feature importance mudou?
# Novos padrões de churn?
# Efeito de campanhas acumulado?
→ Retrainamento mensal obrigatório
```

### 10.2 Dashboard de Monitoramento

```
┌──────────────────────────────────────────────────┐
│          ML MODEL MONITORING - BRASIL            │
├──────────────────────────────────────────────────┤
│                                                  │
│  [LIVE METRICS - ÚLTIMAS 24H]:                   │
│  ├─ AUROC:        0.845 ✅ (Meta: ≥0.82)        │
│  ├─ Recall:       0.782 ✅ (Meta: ≥0.75)        │
│  ├─ Precision:    0.671 ✅ (Range: 0.55-0.75)   │
│  ├─ PR-AUC:       0.682 ✅ (Meta: ≥0.65)        │
│  ├─ Data Drift:   KS=0.08 ✅ (Limiar: <0.15)    │
│  ├─ API Uptime:   99.82% ✅ (Meta: ≥99.5%)      │
│  ├─ Latência p99: 156ms ✅ (Meta: <200ms)       │
│  └─ Predictions:  284.456/dia (normal)           │
│                                                  │
│  [EXPECTED PROFIT - ÚLTIMOS 30 DIAS]:            │
│  ├─ Total:        R$ 2.18M ✅ (Meta: ≥R$2M)     │
│  ├─ Avg/día:      R$ 72.7K                       │
│  └─ Tendência:    ↗ +1.3% vs período anterior   │
│                                                  │
│  [ALERTAS]:                                      │
│  🟢 Nenhum alerta ativo                         │
│                                                  │
│  [PRÓXIMO RETRAINAMENTO]:                        │
│  Data: 2026-04-21 (próxima segunda-feira)        │
│  Dias: 5 dias                                    │
│                                                  │
└──────────────────────────────────────────────────┘
```

---

## 11. Roadmap de Implementação

### 11.1 Timeline CRISP-DM (8 Semanas)

```
SEMANA 1-2: BUSINESS & DATA UNDERSTANDING
├─ Alinhamento com stakeholders ✅ (HOJE)
├─ Definição de objetivos de negócio ✅
├─ Acesso a dados + exploração inicial
└─ Documentação do ML Canvas (ESTE DOC)

SEMANA 2-3: DATA PREPARATION
├─ Validação de schema + qualidade
├─ Feature engineering (20+ features)
├─ Tratamento de valores faltantes/outliers
├─ SMOTE ou class_weight para desbalanceamento
└─ Validação via StratifiedKFold (k=5, seed=42)

SEMANA 4-5: MODELING
├─ Baselines: DummyClassifier, LogisticRegression, DecisionTree, RandomForest (target AUROC ≥0.75)
├─ Main: Construção de MLP com PyTorch com early stopping e batching
├─ Hyperparameter tuning (Random Search)
├─ Threshold otimização via Expected Profit
└─ MLflow: Comparação de modelos

SEMANA 5-6: EVALUATION & VALIDATION
├─ Validação cruzada (5-fold stratified)
├─ Cross-checks econômicos
├─ Feature importance + explainability
└─ Model Card construction

SEMANA 6-7: DEPLOYMENT
├─ Refactoring para produção (clean code)
├─ API FastAPI com 3 endpoints
└─ Dockerização

SEMANA 8+: OPERATIONS & MAINTENANCE
├─ Monitoramento contínuo
├─ Retrainamento semanal (automático)
└─ Otimização iterativa
```

### 11.2 Entregáveis por Fase


| Fase          | Owner    | Entregável                  | Aceitação                |
| ------------- | -------- | --------------------------- | ------------------------ |
| Understanding | Product  | ML Canvas                   | ✅                        |
| Data Prep     | Data Eng | Dataset validado + features | Code review              |
| Modeling      | Data Sci | Modelo(s) com AUROC ≥0.82   | AUROC + PR-AUC + EP      |
| Deployment    | MLOps    | API em produção, SLA        | Smoke tests + load tests |
| Go-Live       | CRM      | Campanhas rodar             | Taxa contato ≥80%        |
| Operations    | MLOps    | Monitoring 24/7             | Dashboard + alertas      |


### 11.3 Critérios de Sucesso por Fase


| Fase           | GO? | Critério                                |
| -------------- | --- | --------------------------------------- |
| **Planning**   | ✅   | Stakeholders alinhados, budget aprovado |
| **Data Prep**  | ✅   | Features prontas, dataset validado      |
| **Modeling**   | ⏳   | AUROC ≥0.82, PR-AUC ≥0.65, Recall ≥0.75 |
| **Deployment** | ⏳   | Uptime 99.5%, latência <200ms p99       |
| **Go-Live**    | ⏳   | CRM operacional, campanhas rodando      |
| **Operations** | ⏳   | Expected Profit ≥R$2M/mês               |


---

## Conclusão Executiva

### Por Que Esta Estratégia Funciona

1. **Alinhamento Econômico:** Modelo otimizado para Expected Profit (R$), não apenas métricas técnicas
2. **Recall Agressivo:** Dado FN=R$1.200 vs FP=R$60 (razão 20:1), Recall ≥75% é obrigatório
3. **Threshold Econômico:** ~5-8% (não 50%), reflete custo real dos erros
4. **Monitoramento 24/7:** Drift detection automático + retrainamento semanal
5. **Impacto Mensurável:** Expected Profit ≥R$2M/mês em base 1M = ROI >5:1

### Projeção de Impacto (Ano 1)

```
Investimento: R$ 2-5 milhões (tech + time)
Benefício: R$ 2M/mês × 12 meses = R$ 24M/ano
ROI: 24M / 3.5M (mid) = 6.9:1

Churn Reduzido: ~1% (de 1.2% para 0.2%)
Clientes Retidos: ~840.000/ano (base 70M)
Revenue Salva: ~R$ 504M/ano
Lucro Operacional: ~R$ 100-150M/ano (após custos)
```

---

**Criado em:** 16/04/2026  
**Versão:** 3.0 (Brasil CRISP-DM)  
**Status:** 🟡 Pronto para Implementação (Fase 2)  
**Próximo Passo:** Validar dados + Feature Engineering