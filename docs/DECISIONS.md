# Decisões

## Registro vivo de decisões arquiteturais e experimentos.

## Dataset

- Fonte: [Telco Customer Churn — IBM](https://www.kaggle.com/datasets/blastchar/telco-customer-churn)
- Hash do arquivo raw: `58235c7e5c2ce5014bc3ed883fa08c1f`
- Registros: 7.043 · Features: 20 · Target: `Churn` (binário)
- Distribuição de classes: No=5.174 (73.5%) · Yes=1.869 (26.5%)
- Missing values: `TotalCharges` — 11 espaços em branco em clientes com tenure=0 → imputados com mediana (1397.47)
- Estratégia para desbalanceamento: `pos_weight=2.7683` no BCEWithLogitsLoss

---

## Pré-processamento

- Estratégia de encoding: `OrdinalEncoder` para binárias, `OneHotEncoder(drop="if_binary")` para nominais
- Scaler escolhido: `StandardScaler` — MLP sensível à escala
- Imputação: `SimpleImputer(median)` para numéricas — TotalCharges com 11 nulos pós-coerção
- Pipeline implementado em: `src/features/pipeline.py` · output shape: (7043, ~30)

### Feature Engineering (pós-EDA)

**Features criadas:**

- `log_tenure = log(tenure + 1)` — substitui `tenure`; lineariza o decaimento exponencial do churn (com ~7k registros, dar a transformação pronta ajuda a MLP a convergir)
- `is_fiber` — 1 se `InternetService == "Fiber optic"`; isola o maior driver de churn (41.9% vs 7.4%)
- `n_add_on_services` — contagem (0-6) de serviços adicionais contratados (`OnlineSecurity`, `OnlineBackup`, `DeviceProtection`, `TechSupport`, `StreamingTV`, `StreamingMovies`); proxy de engajamento/lock-in

**Features removidas (baixo sinal):**

- `gender` — churn 26.9% vs 26.2%, sem poder discriminativo
- `PhoneService` — churn 26.7% vs 24.9%, sinal fraco, ~90% da base é Yes
- `MultipleLines` — hierarquicamente dependente de `PhoneService` (se PhoneService é irrelevante, MultipleLines não agrega)
- `TotalCharges` — correlação 0.826 com `tenure`, redundância conceitual (≈ tenure × MonthlyCharges)
- `StreamingTV` — churn 33.5% (No) vs 30.1% (Yes), sinal fraco (~3pp); redundante com `StreamingMovies`; informação "No internet service" já coberta por `InternetService` e `is_fiber`; contagem absorvida em `n_add_on_services`
- `StreamingMovies` — mesma justificativa de `StreamingTV` (distribuições e taxas de churn quase idênticas)

**Composição final do pipeline:**

- Features numéricas: `log_tenure`, `MonthlyCharges`, `SeniorCitizen`, `n_add_on_services`
- Features binárias: `Partner`, `Dependents`, `PaperlessBilling`, `is_fiber`
- Features categóricas nominais: `InternetService`, `OnlineSecurity`, `OnlineBackup`, `DeviceProtection`, `TechSupport`, `Contract`, `PaymentMethod`

---

## Métricas

### Trade-off de custo: falso positivo e falso negativo

No contexto de negócio, os erros **não têm o mesmo custo**:

- **Falso negativo (FN):** o modelo indica que o cliente **não** vai cancelar, mas ele **cancela** — custo **alto** (perda de receita / cliente que poderia ter sido retido).
- **Falso positivo (FP):** o modelo indica risco de cancelamento, mas o cliente **permanece** — custo **baixo** (ação de retenção aplicada sem necessidade, por exemplo desconto ou benefício).

Oferecer desconto ou benefício a quem não ia cancelar é relativamente **barato**. Deixar escapar quem de fato iria churnar é **caro**. Por isso o modelo deve priorizar **reduzir falsos negativos** — e o **Recall** mede exatamente a capacidade de capturar os positivos reais (churn = sim entre todos os que realmente churnaram):

**Objetivo:** maximizar a captura de clientes em risco real, aceitando **alguns alertas desnecessários** (FP), desde que o custo marginal dos FN continue sendo o gargalo de negócio.

Essas decisões estão quantificadas na métrica econômica abaixo (FN pesando bem mais que FP).

- Métrica de negócio: **Recall ≥ 0.75** — FN custa 20× mais que FP
- Métrica técnica principal: **PR-AUC** — mais informativa que AUC-ROC em dados desbalanceados (26.5% positivos)
- Threshold de decisão: otimizar por `Expected Profit = TP×1140 - FP×60 - FN×1200` (não fixar em 0.5)
- Avaliação completa: Recall, Precision, F1, AUC-ROC, PR-AUC (≥4 métricas exigidas)

---

## Baselines (Etapa 1)

Experimento MLflow: `churn-baselines` · Dataset hash: `58235c7e5c2ce5014bc3ed883fa08c1f` · CV: StratifiedKFold(k=5, seed=42)


| Modelo                          | Recall    | Precision | F1    | AUC-ROC   | PR-AUC    | Meta (Recall≥0.75) |
| ------------------------------- | --------- | --------- | ----- | --------- | --------- | ------------------ |
| DummyClassifier (most_frequent) | 0.000     | 0.000     | 0.000 | 0.500     | 0.265     | ✗                  |
| DummyClassifier (stratified)    | 0.275     | 0.273     | 0.274 | 0.505     | 0.268     | ✗                  |
| LogisticRegression (balanced)   | **0.802** | 0.513     | 0.626 | **0.845** | **0.655** | ✅                  |


**Conclusão:** LogisticRegression já atinge Recall=0.802, superando a meta de negócio (0.75). O MLP precisa superar PR-AUC=0.655 e manter Recall≥0.75.

---

## Arquitetura MLP (Etapa 2)

- [x] Arquitetura implementada: `Input(30) → Linear(64)+BN+ReLU+Dropout(0.3) → Linear(32)+BN+ReLU+Dropout(0.2) → Linear(1)` — input_dim=30 confirmado após feature engineering
- [x] Loss function: `BCEWithLogitsLoss(pos_weight=tensor(2.7683))`
- [x] Otimizador: `AdamW(lr=1e-3, weight_decay=1e-4)` com `ReduceLROnPlateau(patience=5)`
- [x] Early stopping patience: `10 epochs` monitorando `val_loss`
- [x] Batch size: `64` — melhor resultado nos experimentos
- [x] Validação: `StratifiedKFold(k=5, seed=42)` no conjunto de treino + hold-out test 20%
- [x] Threshold: otimizado por Expected Profit (não fixo em 0.5) — encontrado via varredura `[0.05, 0.95, step=0.01]`
- [x] Implementado em: `src/models/mlp.py` (ChurnMLP) · `src/models/train.py` (loop + CV + MLflow)
- [x] Meta: superar LogisticRegression (PR-AUC=0.655, Recall=0.802)

---

## Experimentos MLflow

> Adicionar linha a cada experimento relevante.


| Modelo                          | AUC-ROC | PR-AUC | F1    | Recall | Observação                   |
| ------------------------------- | ------- | ------ | ----- | ------ | ---------------------------- |
| DummyClassifier (most_frequent) | 0.500   | 0.265  | 0.000 | 0.000  | piso absoluto                |
| DummyClassifier (stratified)    | 0.505   | 0.268  | 0.274 | 0.275  | piso probabilístico          |
| LogisticRegression (balanced)   | 0.845   | 0.655  | 0.626 | 0.802  | **meta de negócio atingida** |
| MLP v1 (atual)                  | 0.8506  | 0.6648 | 0.625 | 0.8467 | **supera baseline em PR-AUC** |


---

## API (Etapa 3)

- [x] Framework: **FastAPI** em `src/api/` — schemas Pydantic, middleware structlog, lifespan context
- [x] Endpoints implementados:
  - `GET /` → `RootResponse` (info da API)
  - `GET /health` → `HealthResponse` (`status`, `model_version`, `model_source`, `uptime_seconds`, `timestamp`)
  - `POST /api/v1/predict` → `PredictResponse { churn_probability, churn_predicted, model_version, processing_time_ms }`
  - `POST /api/v1/predict_batch` → `PredictBatchResponse` (até 10k registros)
- Decisão binária na inferência HTTP: **probabilidade ≥ 0,5**; avaliação no treino pode usar limiar derivado de custo/lucro — ver `train.py` / métricas MLflow.
- [x] Validação: Pydantic v2 (`model_config = ConfigDict(...)`) — 422 automático em payload inválido
- [x] Middleware: `LoggingMiddleware` (request/response + latência) + `RateLimitMiddleware` (10 req/30s por IP) — ambos em `src/api/utils.py`
- [x] Modelo carregado no **startup via lifespan** a partir de `models/mlp_best.pt` + `models/pipeline.pkl`
- [x] 51 testes de integração em `tests/integration/`

---

## Deploy (Etapa 4)

- [x] Estratégia: **real-time** via API REST (FastAPI) — inferência por request individual, sem batch
- [x] Justificativa: volume baixo (~7k clientes), decisão de retenção é individual e requer resposta imediata; batch não agrega valor operacional aqui
- [x] Plataforma: **AWS** — EC2 (t3.medium, Ubuntu 22.04) + ALB + Route53 + ACM
- [x] Serviços no EC2: dois containers Docker Compose — `mlflow` (porta 5000) + `flask-app` placeholder (porta 8080); FastAPI em `src/api/` é o alvo final
- [x] Roteamento HTTPS: ALB com host-based rules → `mlflow.pocsarcotech.com` → MLflow · `api.pocsarcotech.com` → API
- [x] Infraestrutura como código: Terraform em `iac/` — módulos keypair, networking, iam, storage, compute, alb
- [x] Estado Terraform remoto: S3 bucket `tech-terraform-poc` / key `environment-pos/terraform.tfstate`
- [x] URL MLflow: `https://mlflow.pocsarcotech.com/mlflow/`
- [x] URL API: `https://api.pocsarcotech.com`
- [x] CI/CD: três workflows separados por responsabilidade — `pr.yml` (lint + testes unitários em PRs), `cd.yml` (treino + build + smoke ao criar pre-release), `deploy.yml` (SSH + docker compose + health check ao promover para release)

---

## Monitoramento (planejado)

- **Prometheus + Grafana:** métricas operacionais da API (latência, erros, disponibilidade, uso de recurso) — stack inicialmente considerada para SLIs/SLOs em tempo quase real.
- **MLflow:** experimentos, Model Registry e runs **batch** de avaliação/retraining (PR-AUC, Recall, Expected Profit) para comparar ao baseline; não substitui dashboards de infra.
- **Drift:** variáveis contínuas → comparar distribuições com **KS**; categóricas nominais (ex.: `Contract`, `InternetService`) → **Chi-quadrado** sobre contagens por categoria — ver justificativa em [`docs/MONITORING_PLAN.md`](MONITORING_PLAN.md).
- Plano detalhado (métricas, alertas, playbook): [`docs/MONITORING_PLAN.md`](MONITORING_PLAN.md).

- [x] Etapa 1: LogisticRegression com `class_weight="balanced"` já atinge Recall=0.80 — o MLP precisa bater PR-AUC=0.655 mantendo Recall≥0.75. `TotalCharges` tinha correlação 0.826 com tenure — resolvido na etapa de feature engineering (removida; tenure substituída por log_tenure).
- [x] Etapa 2: `StratifiedKFold` obrigatório por spec — adicionado no `train.py` como CV no conjunto de treino (80%) + hold-out test separado (20%); fold-wise metrics logadas no MLflow com prefixo `fold{k}_*` e agregadas em `cv_*_mean/std`.
- [x] Etapa 3: Flask app em `iac/flask-app/` é placeholder — a API real é FastAPI em `src/api/`. Modelo carregado de `models/mlp_best.pt` no startup via lifespan. `--static-prefix /mlflow` no MLflow server desloca todos os endpoints para `/mlflow/*` — health check do ALB deve apontar para `/mlflow/health`, não `/health`.
- [x] Etapa 4: CI/CD reestruturado em três workflows com gatilhos de release — `pr.yml` roda em PRs, `cd.yml` dispara ao criar pre-release (garante treino + smoke antes de ir pra prod), `deploy.yml` dispara ao promover a release (garante que só imagem validada chega à EC2). Processo documentado no README.
