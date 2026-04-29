variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment name used for tagging"
  type        = string
  default     = "pos"
}

variable "project_name" {
  description = "Project name used as prefix for all resource names"
  type        = string
  default     = "mlflow-flask-project"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.medium"
}

variable "allowed_cidr" {
  description = "CIDR allowed to reach the instance; restrict to your IP in production"
  type        = string
  default     = "0.0.0.0/0"

  validation {
    condition     = can(cidrnetmask(var.allowed_cidr))
    error_message = "allowed_cidr must be a valid CIDR block."
  }
}

variable "mlflow_port" {
  description = "Host port for the MLflow tracking server"
  type        = number
  default     = 5000
}

variable "flask_port" {
  description = "Host port for the Flask application"
  type        = number
  default     = 8080
}

variable "mlflow_artifact_bucket" {
  description = "S3 bucket name for MLflow artifacts; leave empty to use local instance storage"
  type        = string
  default     = ""
}

variable "volume_size" {
  description = "Root EBS volume size in GB"
  type        = number
  default     = 30
}
