output "instance_id" {
  description = "EC2 instance ID"
  value       = module.compute.instance_id
}

output "public_ip" {
  description = "Public IP of the EC2 instance"
  value       = module.compute.public_ip
}

output "public_dns" {
  description = "Public DNS of the EC2 instance"
  value       = module.compute.public_dns
}

output "alb_dns_name" {
  description = "ALB DNS name — aponte seus CNAMEs para este valor"
  value       = module.alb.alb_dns_name
}

output "flask_app_url" {
  description = "FastAPI URL (HTTPS)"
  value       = "https://api.${var.base_domain}"
}

output "mlflow_url" {
  description = "MLflow UI URL (HTTPS)"
  value       = "https://mlflow.${var.base_domain}"
}

output "dns_records" {
  description = "Registros DNS a criar no seu provedor (CNAME)"
  value       = <<-EOT
    api.${var.base_domain}     CNAME  ${module.alb.alb_dns_name}
    mlflow.${var.base_domain}  CNAME  ${module.alb.alb_dns_name}
  EOT
}

output "flask_app_url_direct" {
  description = "FastAPI URL direto na EC2 (sem HTTPS, para debug)"
  value       = "http://${module.compute.public_ip}:${var.flask_port}"
}

output "mlflow_url_direct" {
  description = "MLflow URL direto na EC2 (sem HTTPS, para debug)"
  value       = "http://${module.compute.public_ip}:${var.mlflow_port}"
}

output "private_key_path" {
  description = "Local path of the generated SSH private key"
  value       = module.keypair.private_key_path
}

output "ssh_command" {
  description = "Ready-to-use SSH command"
  value       = "ssh -i ${module.keypair.private_key_path} ubuntu@${module.compute.public_ip}"
}
