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
      description = "Flask application"
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
