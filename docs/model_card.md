# Model Card — Churn Prediction MLP

Documentação do modelo conforme boas práticas de ML responsável.
Atualizar após a Etapa 2 com resultados reais dos experimentos.

---

## Informações gerais

| Campo | Valor |
|-------|-------|
| Nome do modelo | Churn Prediction MLP |
| Versão | v1.0.0 |
| Tipo | Classificação binária |
| Framework | PyTorch |
| Data de treino | `a preencher` |
| Dataset de treino | Telco Customer Churn (IBM) |
| Versão do dataset | `hash: a preencher` |

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

> Preencher após Etapa 2 com resultados reais.

### Métricas globais

| Métrica | Treino | Validação | Teste |
|---------|--------|-----------|-------|
| AUC-ROC | — | — | — |
| PR-AUC | — | — | — |
| F1 | — | — | — |
| Recall | — | — | — |
| Precision | — | — | — |

### Comparação com baselines (StratifiedKFold k=5, média ± std)

| Modelo | AUC-ROC | Recall | F1 |
|--------|---------|--------|----|
| DummyClassifier (most_frequent) | 0.5000±0.000 | 0.0000±0.000 | 0.0000±0.000 |
| DummyClassifier (stratified) | 0.5050±0.007 | 0.2750±0.011 | 0.2738±0.011 |
| LogisticRegression (balanced) | **0.8449±0.013** | **0.8020±0.015** | **0.6258±0.009** |
| DecisionTree (balanced) | 0.6588±0.020 | 0.5029±0.036 | 0.4983±0.030 |
| RandomForest (balanced) | 0.8207±0.010 | 0.4746±0.035 | 0.5380±0.029 |
| **MLP (este modelo)** | — | — | — |

### Análise de custo

| Tipo de erro | Custo estimado | Impacto |
|--------------|----------------|---------|
| Falso Positivo (cliente retido desnecessariamente) | Custo da campanha | Baixo |
| Falso Negativo (cliente perdido sem ação) | LTV do cliente | Alto |

- Threshold escolhido: `a preencher`
- Justificativa: `a preencher após análise de custo`

---

## Dados de treino

- **Fonte**: Telco Customer Churn — IBM Sample Dataset
- **Período**: dados históricos de clientes — sem data explícita
- **Tamanho**: ~7.043 registros, 20 features
- **Distribuição de classes**: 73.5% não-churn / 26.5% churn (1869/7043)
- **Validação**: StratifiedKFold (k=5, shuffle=True, seed=42) — mantém proporção de classes em cada fold
- **Pré-processamento**: `a detalhar após Etapa 1`

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
- [ ] `a preencher após Etapa 2`

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

- Retreino recomendado: `a definir — sugestão: trimestral ou quando AUC cair >5%`
- Responsável: `a preencher`
- Repositório: `a preencher com URL do GitHub`