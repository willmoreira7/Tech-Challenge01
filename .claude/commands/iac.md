---
name: iac
description: Valida, planeja e aplica a infraestrutura AWS com Terraform (EC2 + MLflow + Flask)
---

Implemente e execute seguindo **exatamente** `specs/iac.md`.

1. Verifique pré-requisitos:
   - `terraform version` (requer >= 1.3.9)
   - `aws sts get-caller-identity` (confirma credenciais AWS ativas)
2. Entre no diretório `iac/` e inicialize se necessário (`terraform init`)
3. Valide a sintaxe: `terraform validate` — corrija qualquer erro antes de prosseguir
4. Gere o plano: `terraform plan` — liste os recursos que serão criados/modificados
5. Aplique (somente se solicitado explicitamente): `terraform apply`
6. Após apply, confirme os outputs:
   - `mlflow_url` → acesse via browser e verifique a UI do MLflow
   - `flask_app_url` → `GET /health` deve retornar HTTP 200
   - `ssh_command` → valide acesso SSH à instância
7. Para testes locais sem AWS, use o docker-compose da flask-app:
   ```bash
   cd iac/flask-app
   docker compose -f docker-compose.local.yml up -d --build
   curl http://localhost:8080/health
   ```

Critérios obrigatórios (conforme `specs/iac.md`):
- `terraform validate` sem erros
- `terraform plan` sem diff inesperado
- `GET /health` → HTTP 200
- `POST /train` → HTTP 200 com `run_id`
- Run visível no MLflow UI
