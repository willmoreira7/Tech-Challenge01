data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_instance" "this" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  key_name               = var.key_name
  iam_instance_profile   = var.iam_instance_profile
  vpc_security_group_ids = var.security_group_ids

  root_block_device {
    volume_type           = "gp3"
    volume_size           = var.volume_size
    delete_on_termination = true
    encrypted             = true
  }

  user_data = templatefile("${path.module}/templates/user_data.sh", {
    mlflow_port            = var.mlflow_port
    flask_port             = var.flask_port
    mlflow_artifact_bucket = var.mlflow_artifact_bucket
    aws_region             = var.aws_region
  })

  tags = merge(var.tags, { Name = var.project_name })
}
