# Spec: Infrastructure as Code (Terraform + AWS)

## Responsabilidade

Provisionar a infraestrutura AWS necessária para hospedar o MLflow Tracking Server e a
aplicação Flask (futuramente FastAPI) em uma instância EC2, com rede, IAM e armazenamento
de artefatos opcionais via S3.

---

## Arquitetura

```
Internet
    │ HTTPS (443)
    ▼
ALB (Application Load Balancer)
    ├── api.pocsarcotech.com     → EC2:8080  (FastAPI)
    └── mlflow.pocsarcotech.com  → EC2:5000  (MLflow)
         ACM: wildcard cert *.pocsarcotech.com

EC2 (Ubuntu 22.04, t3.medium)
    ├── Docker Compose
    │   ├── mlflow   — MLflow Tracking Server (porta 5000, prefixo /mlflow)
    │   └── fastapi  — API FastAPI (porta 8080)
    ├── IAM Instance Profile → S3 (artefatos MLflow)
    └── Security Group → SSH (22), ALB health checks (8080, 5000)

S3 (fiap-mlflow-artifacts) — artefatos MLflow
Route53 — CNAMEs apontando para o ALB
```

### URLs de Produção

| Serviço | URL |
|---------|-----|
| API FastAPI | https://api.pocsarcotech.com |
| API Docs (Swagger) | https://api.pocsarcotech.com/docs |
| MLflow UI | https://mlflow.pocsarcotech.com/mlflow/ |
| API (acesso direto EC2) | http://100.24.64.84:8080 |
| MLflow (acesso direto EC2) | http://100.24.64.84:5000 |

### Módulos Terraform

| Módulo | Caminho | Responsabilidade |
|--------|---------|-----------------|
| `keypair` | `modules/keypair/` | Gera par de chaves RSA 4096, salva `.pem` localmente em `~/.ssh/` |
| `networking` | `modules/networking/` | Security Group na VPC default com regras de ingress configuráveis |
| `iam` | `modules/iam/` | IAM Role + Instance Profile + política S3 |
| `storage` | `modules/storage/` | S3 bucket para artefatos MLflow (`fiap-mlflow-artifacts`) |
| `compute` | `modules/compute/` | EC2 com user_data que instala Docker e sobe os containers |
| `alb` | `modules/alb/` | ALB + listener HTTPS (ACM) + host-based rules por subdomínio |

### Backend remoto

Estado armazenado em S3:

```hcl
backend "s3" {
  bucket  = "tech-terraform-poc"
  key     = "environment-pos/terraform.tfstate"
  region  = "us-east-1"
  encrypt = true
}
```

---

## Variáveis

| Variável | Tipo | Default | Descrição |
|----------|------|---------|-----------|
| `aws_region` | string | `"us-east-1"` | Região AWS para deploy |
| `environment` | string | `"pos"` | Ambiente (usado em tags) |
| `project_name` | string | `"mlflow-flask-project"` | Prefixo de todos os recursos |
| `instance_type` | string | `"t3.medium"` | Tipo da instância EC2 |
| `allowed_cidr` | string | `"0.0.0.0/0"` | CIDR permitido (restringir em produção) |
| `mlflow_port` | number | `5000` | Porta do MLflow Tracking Server |
| `flask_port` | number | `8080` | Porta da aplicação FastAPI |
| `mlflow_artifact_bucket` | string | `"fiap-mlflow-artifacts"` | Nome do bucket S3 para artefatos MLflow |
| `volume_size` | number | `30` | Tamanho do volume EBS raiz (GB) |
| `base_domain` | string | `"pocsarcotech.com"` | Domínio base — requer wildcard ACM cert `*.pocsarcotech.com` |

---

## Outputs

| Output | Descrição |
|--------|-----------|
| `instance_id` | ID da instância EC2 |
| `public_ip` | IP público da instância (`100.24.64.84`) |
| `public_dns` | DNS público da instância |
| `alb_dns_name` | DNS do ALB (usado para CNAMEs no Route53) |
| `flask_app_url` | URL HTTPS da API: `https://api.pocsarcotech.com` |
| `mlflow_url` | URL HTTPS do MLflow: `https://mlflow.pocsarcotech.com` |
| `flask_app_url_direct` | URL direta EC2 (debug): `http://100.24.64.84:8080` |
| `mlflow_url_direct` | URL direta EC2 (debug): `http://100.24.64.84:5000` |
| `dns_records` | CNAMEs a criar no provedor DNS |
| `private_key_path` | Caminho local da chave SSH gerada |
| `ssh_command` | Comando SSH pronto para uso |

---

## Flask App (`iac/flask-app/`)

Aplicação standalone de demonstração usada durante o desenvolvimento da infra,
**antes** da migração para a API FastAPI (`src/api/`).

| Arquivo | Descrição |
|---------|-----------|
| `app.py` | Flask app com `/health`, `/train`, `/predict` |
| `Dockerfile` | Imagem Python 3.11-slim com gunicorn |
| `requirements.txt` | flask, mlflow, gunicorn, scikit-learn, pandas, numpy |
| `docker-compose.local.yml` | Stack local: mlflow + flask-app para desenvolvimento |

### Endpoints

- `GET /health` → `{"status": "ok", "mlflow_uri": "..."}`
- `POST /train` → treina LinearRegression simples, loga no MLflow, retorna `run_id` e `r2_score`
- `POST /predict` → predição com modelo em memória

> **Nota:** Esta app é um placeholder. A API de produção está em `src/api/` (FastAPI + ChurnMLP).
> Quando o modelo MLP estiver pronto, o `user_data.sh` deve ser atualizado para clonar o repo
> e usar a API FastAPI em vez do Flask placeholder.

---

## Comandos

```bash
# Inicializar (uma vez)
cd iac && terraform init

# Validar sintaxe
terraform validate

# Verificar plano de mudanças (sem aplicar)
terraform plan

# Provisionar infra
terraform apply

# Destruir tudo
terraform destroy

# Testar app localmente (sem AWS)
cd iac/flask-app && docker compose -f docker-compose.local.yml up -d --build
```

---

## Critérios de Aceitação

- [x] `terraform validate` retorna sem erros
- [x] `terraform plan` lista recursos esperados sem diff inesperado
- [x] Após `apply`: `mlflow_url` e `flask_app_url` acessíveis via HTTPS
- [x] `GET https://api.pocsarcotech.com/health` → HTTP 200
- [x] `POST https://api.pocsarcotech.com/api/v1/predict` → HTTP 200 com `churn_probability`
- [x] MLflow UI acessível em `https://mlflow.pocsarcotech.com/mlflow/` com runs registradas
- [x] ALB com host-based routing funcionando (api.* → FastAPI, mlflow.* → MLflow)
- [x] ACM wildcard cert `*.pocsarcotech.com` emitido e associado ao listener HTTPS
- [x] Chave SSH salva em `~/.ssh/mlflow-flask-project-key.pem` e `ssh_command` funcional

---

## Pré-requisitos

- `terraform >= 1.3.9` instalado
- AWS CLI configurado (`aws configure` ou variáveis de ambiente `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`)
- Acesso de escrita ao bucket S3 de backend (`tech-terraform-poc`)
- Docker instalado (apenas para testes locais com `docker-compose.local.yml`)

---

## Limitações conhecidas

- `allowed_cidr = "0.0.0.0/0"` — restringir ao seu IP em produção (`var.allowed_cidr = "<seu-ip>/32"`)
- Flask app é placeholder; produção deve usar `src/api/` (FastAPI + ChurnMLP)
- Backend S3 hardcoded em `versions.tf` — alterar para ambiente de produção real
