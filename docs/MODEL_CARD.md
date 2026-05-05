# Model Card — Churn Prediction MLP

Documentação do modelo conforme boas práticas de ML responsável.

---

## Informações gerais

| Campo | Valor |
|-------|-------|
| Nome do modelo | Churn Prediction MLP |
| Versão | v1.0.0 |
| Tipo | Classificação binária |
| Framework | PyTorch |
| Data de treino | 2026-05-04 |
| Dataset de treino | Telco Customer Churn (IBM) |
| Versão do dataset | hash: `58235c7e5c2ce5014bc3ed883fa08c1f` |

---

## Uso pretendido

**Caso de uso principal**: identificar clientes com risco de cancelamento para ações preventivas de retenção.

**Usuários pretendidos**: equipes de CRM e retenção de clientes de operadoras de telecomunicações.

**Casos de uso fora do escopo**:
- Não deve ser usado para decisões automáticas sem revisão humana
- Não generaliza para outros setores sem retreino
- Não deve ser usado como único critério de ação sobre clientes

---

## Performance

### Métricas no test set (hold-out 20%, n=1.413)

| Métrica | Valor |
|---------|-------|
| **Recall** | **0.8467** ✅ (meta ≥ 0.75) |
| Precision | 0.4953 |
| F1 | 0.6250 |
| AUC-ROC | 0.8506 |
| PR-AUC | 0.6648 |
| Specificity | 0.6881 |

Matriz de confusão: TP=475 · FP=484 · FN=86 · TN=1068

### Comparação com baselines (StratifiedKFold k=5)

| Modelo | AUC-ROC | Recall | F1 | PR-AUC | Meta Recall≥0.75 |
|--------|---------|--------|----|--------|-----------------|
| DummyClassifier (most_frequent) | 0.500 | 0.000 | 0.000 | 0.265 | ✗ |
| DummyClassifier (stratified) | 0.505 | 0.275 | 0.274 | 0.268 | ✗ |
| LogisticRegression (balanced) | 0.845 | 0.802 | 0.626 | 0.655 | ✅ |
| **MLP v1 (este modelo)** | **0.8506** | **0.8467** | **0.625** | **0.6648** | ✅ |

### Análise de custo

| Tipo de erro | Custo | Impacto |
|---|---|---|
| Falso Positivo — cliente retido sem necessidade | R$ 60 (ação de retenção) | Baixo |
| Falso Negativo — cliente perdido sem ação | R$ 1.200 (LTV estimado) | Alto (20×) |

- Threshold: otimizado por Expected Profit = TP×1140 − FP×60 − FN×1200 (não fixo em 0.5)
- FN custa 20× mais que FP — modelo calibrado para minimizar falsos negativos

---

## Dados de treino

- **Fonte**: Telco Customer Churn — IBM Sample Dataset
- **Período**: dados históricos de clientes — sem data explícita
- **Tamanho**: ~7.043 registros, 20 features
- **Distribuição de classes**: 73.5% não-churn / 26.5% churn (1869/7043)
- **Validação**: StratifiedKFold (k=5, shuffle=True, seed=42) — mantém proporção de classes em cada fold
- **Pré-processamento**: `src/features/pipeline.py` — log_tenure, is_fiber, n_add_on_services; StandardScaler + OrdinalEncoder + OneHotEncoder; input_dim=30

---

## Limitações

> Preencher ao longo do projeto com limitações reais encontradas.

- [ ] Desbalanceamento de classes pode afetar recall em produção
- [ ] Dataset sem data — possível drift não detectável
- [ ] Features de uso (minutos, chamadas) podem variar por período do mês
- [ ] Modelo treinado em um único mercado — pode não generalizar para outros países
- [ ] `a complementar após análise de erros`

---

## Vieses identificados

> Preencher após análise exploratória e de erros por segmento.

- [ ] Analisar performance por: tipo de contrato, tenure, faixa de gasto mensal
- [ ] Verificar se modelo penaliza desproporcionalmente algum segmento
- [ ] Analisar performance segmentada por: tipo de contrato, tenure, faixa de gasto mensal

---

## Cenários de falha

| Cenário | Probabilidade | Impacto | Mitigação |
|---------|--------------|---------|-----------|
| Input com feature faltando | Alta | Erro 422 | Validação Pydantic |
| Drift de distribuição de dados | Média | Queda de AUC | Monitoramento contínuo |
| Modelo desatualizado | Alta (longo prazo) | Predições erradas | Retreino periódico |
| Timeout de inferência | Baixa | Erro 500 | Timeout configurado na API |

---

## Considerações éticas

- Modelo não deve ser usado para negar serviços a clientes
- Ações de retenção devem ser positivas (ofertas, suporte) — não punitivas
- Decisões finais devem envolver revisão humana
- Dados de clientes devem ser tratados conforme LGPD

---

## Contato e manutenção

- Retreino recomendado: trimestral ou quando AUC-ROC cair >5% abaixo de 0.850
- Repositório: Tech-Challenge01 (branch `main`)
- CI/CD: `.github/workflows/ci-cd.yml` — treino automático quando `src/models/`, `src/features/` ou `src/data/` mudam em `main`