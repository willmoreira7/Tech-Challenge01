variable "project_name" {
  description = "Project name used as the EC2 instance Name tag"
  type        = string
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.medium"
}

variable "key_name" {
  description = "Name of the AWS key pair to attach to the instance"
  type        = string
}

variable "iam_instance_profile" {
  description = "Name of the IAM instance profile to attach"
  type        = string
}

variable "security_group_ids" {
  description = "List of security group IDs to associate with the instance"
  type        = list(string)
}

variable "volume_size" {
  description = "Root EBS volume size in GB"
  type        = number
  default     = 30
}

variable "mlflow_port" {
  description = "MLflow tracking server port injected into user_data"
  type        = number
  default     = 5000
}

variable "flask_port" {
  description = "Flask application port injected into user_data"
  type        = number
  default     = 8080
}

variable "mlflow_artifact_bucket" {
  description = "S3 bucket name for MLflow artifacts injected into user_data"
  type        = string
  default     = ""
}

variable "aws_region" {
  description = "AWS region injected into user_data for SDK configuration"
  type        = string
}

variable "tags" {
  description = "Tags to apply to the EC2 instance"
  type        = map(string)
  default     = {}
}
