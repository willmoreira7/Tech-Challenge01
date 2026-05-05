---
name: iac
description: Valida, planeja e aplica a infraestrutura AWS com Terraform (EC2 + MLflow + FastAPI). Usar quando quiser provisionar, atualizar ou destruir recursos na AWS, ou testar a stack localmente.
---

Consulte `specs/iac.md` para a spec completa.

## Infraestrutura provisionada

- EC2 (t3.medium, Ubuntu 22.04) + ALB + Route53 + ACM
- Módulos Terraform: `keypair`, `networking`, `iam`, `storage`, `compute`, `alb`
- URLs: `https://mlflow.pocsarcotech.com/mlflow/` e `https://api.pocsarcotech.com`
- Estado remoto: S3 bucket `tech-terraform-poc` / key `environment-pos/terraform.tfstate`

## Pré-requisitos

```bash
terraform version   # requer >= 1.3.9
aws sts get-caller-identity   # confirma credenciais AWS ativas
```

## Comandos Terraform

```bash
cd iac
terraform init      # inicializa providers e backend S3
terraform validate  # valida sintaxe HCL — corrija antes de prosseguir
terraform plan      # preview das mudanças
terraform apply     # provisiona (somente se solicitado explicitamente)
terraform destroy   # destrói todos os recursos (confirmar com usuário antes)
```

## Após apply — verificar outputs

```bash
terraform output mlflow_url    # https://mlflow.pocsarcotech.com/mlflow/
terraform output api_url       # https://api.pocsarcotech.com
terraform output ssh_command   # acesso SSH à instância
```

Checklist:
- `GET https://mlflow.pocsarcotech.com/mlflow/health` → 200
- `GET https://api.pocsarcotech.com/health` → 200 com `{"status": "ok"}`
- Run MLflow visível após `make train`

## Teste local sem AWS

```bash
cd iac/flask-app
docker compose -f docker-compose.local.yml up -d --build
curl http://localhost:8080/health
```

**Atenção:** `iac/flask-app/` é um placeholder (Flask). A API real é FastAPI em `src/api/`.
Nunca force push em infra sem revisão. Confirmar com usuário antes de `terraform destroy`.
