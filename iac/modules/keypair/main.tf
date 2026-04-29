locals {
  key_path = var.private_key_path != "" ? var.private_key_path : pathexpand("~/.ssh/${var.project_name}-key.pem")
}

resource "tls_private_key" "this" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "aws_key_pair" "this" {
  key_name   = "${var.project_name}-key"
  public_key = tls_private_key.this.public_key_openssh
  tags       = var.tags
}

resource "local_sensitive_file" "private_key" {
  content         = tls_private_key.this.private_key_pem
  filename        = local.key_path
  file_permission = "0600"
}
