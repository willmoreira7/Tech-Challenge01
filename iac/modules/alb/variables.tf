variable "project_name" {
  description = "Project name used as prefix for resource names"
  type        = string
}

variable "instance_id" {
  description = "EC2 instance ID to attach to target groups"
  type        = string
}

variable "flask_port" {
  description = "Port where the Flask application listens on the EC2 instance"
  type        = number
  default     = 8080
}

variable "mlflow_port" {
  description = "Port where the MLflow server listens on the EC2 instance"
  type        = number
  default     = 5000
}

variable "acm_certificate_arn" {
  description = "ARN of the ACM certificate to attach to the HTTPS listener"
  type        = string
}

variable "flask_domain" {
  description = "Fully qualified domain name for the Flask API (e.g. api.pocsarcotech.com)"
  type        = string
}

variable "mlflow_domain" {
  description = "Fully qualified domain name for the MLflow UI (e.g. mlflow.pocsarcotech.com)"
  type        = string
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
