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

output "mlflow_url" {
  description = "MLflow tracking server URL"
  value       = "http://${module.compute.public_ip}:${var.mlflow_port}"
}

output "flask_app_url" {
  description = "Flask application URL"
  value       = "http://${module.compute.public_ip}:${var.flask_port}"
}

output "private_key_path" {
  description = "Local path of the generated SSH private key"
  value       = module.keypair.private_key_path
}

output "ssh_command" {
  description = "Ready-to-use SSH command"
  value       = "ssh -i ${module.keypair.private_key_path} ubuntu@${module.compute.public_ip}"
}
