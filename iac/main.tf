data "aws_acm_certificate" "wildcard" {
  domain      = "*.${var.base_domain}"
  statuses    = ["ISSUED"]
  most_recent = true
}

module "keypair" {
  source       = "./modules/keypair"
  project_name = var.project_name
  tags         = local.common_tags
}

module "networking" {
  source       = "./modules/networking"
  project_name = var.project_name
  tags         = local.common_tags

  ingress_rules = [
    {
      description = "SSH"
      port        = 22
      protocol    = "tcp"
      cidr_blocks = [var.allowed_cidr]
    },
    {
      description = "MLflow UI"
      port        = var.mlflow_port
      protocol    = "tcp"
      cidr_blocks = [var.allowed_cidr]
    },
    {
      description = "FastAPI application"
      port        = var.flask_port
      protocol    = "tcp"
      cidr_blocks = [var.allowed_cidr]
    },
  ]
}

module "iam" {
  source               = "./modules/iam"
  project_name         = var.project_name
  artifact_bucket_name = var.mlflow_artifact_bucket
  tags                 = local.common_tags
}

module "storage" {
  source             = "./modules/storage"
  enabled            = var.mlflow_artifact_bucket != ""
  bucket_name        = var.mlflow_artifact_bucket
  versioning_enabled = true
  tags               = local.common_tags
}

module "alb" {
  source              = "./modules/alb"
  project_name        = var.project_name
  instance_id         = module.compute.instance_id
  flask_port          = var.flask_port
  mlflow_port         = var.mlflow_port
  acm_certificate_arn = data.aws_acm_certificate.wildcard.arn
  flask_domain        = "api.${var.base_domain}"
  mlflow_domain       = "mlflow.${var.base_domain}"
  tags                = local.common_tags
}

data "aws_route53_zone" "this" {
  name         = var.base_domain
  private_zone = false
}

resource "aws_route53_record" "api" {
  zone_id = data.aws_route53_zone.this.zone_id
  name    = "api.${var.base_domain}"
  type    = "A"

  alias {
    name                   = trimsuffix(module.alb.alb_dns_name, ".")
    zone_id                = module.alb.alb_zone_id
    evaluate_target_health = true
  }
}

resource "aws_route53_record" "mlflow" {
  zone_id = data.aws_route53_zone.this.zone_id
  name    = "mlflow.${var.base_domain}"
  type    = "A"

  alias {
    name                   = trimsuffix(module.alb.alb_dns_name, ".")
    zone_id                = module.alb.alb_zone_id
    evaluate_target_health = true
  }
}

# Permite que o ALB alcance a EC2 nas portas das aplicações
resource "aws_security_group_rule" "alb_to_ec2_flask" {
  type                     = "ingress"
  from_port                = var.flask_port
  to_port                  = var.flask_port
  protocol                 = "tcp"
  security_group_id        = module.networking.security_group_id
  source_security_group_id = module.alb.alb_security_group_id
  description              = "ALB to Flask"
}

resource "aws_security_group_rule" "alb_to_ec2_mlflow" {
  type                     = "ingress"
  from_port                = var.mlflow_port
  to_port                  = var.mlflow_port
  protocol                 = "tcp"
  security_group_id        = module.networking.security_group_id
  source_security_group_id = module.alb.alb_security_group_id
  description              = "ALB to MLflow"
}

module "compute" {
  source                 = "./modules/compute"
  project_name           = var.project_name
  instance_type          = var.instance_type
  key_name               = module.keypair.key_name
  iam_instance_profile   = module.iam.instance_profile_name
  security_group_ids     = [module.networking.security_group_id]
  volume_size            = var.volume_size
  mlflow_port            = var.mlflow_port
  flask_port             = var.flask_port
  mlflow_artifact_bucket = var.mlflow_artifact_bucket
  aws_region             = var.aws_region
  tags                   = local.common_tags
}
