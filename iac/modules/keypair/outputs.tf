output "key_name" {
  description = "Name of the AWS key pair"
  value       = aws_key_pair.this.key_name
}

output "private_key_path" {
  description = "Local path of the saved private key file"
  value       = local_sensitive_file.private_key.filename
}

output "public_key_openssh" {
  description = "Public key in OpenSSH format"
  value       = tls_private_key.this.public_key_openssh
  sensitive   = true
}
