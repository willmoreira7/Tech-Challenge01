terraform {
  required_version = ">= 1.3.9"

  backend "s3" {
    bucket = "tech-terraform-poc"
    key    = "environment-pos/terraform.tfstate"
    region = "us-east-1"

    encrypt = true
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}
