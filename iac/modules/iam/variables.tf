variable "project_name" {
  description = "Project name used as prefix for IAM resource names"
  type        = string
}

variable "artifact_bucket_name" {
  description = "S3 bucket name for MLflow artifacts; empty string disables S3 policy"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Tags to apply to IAM resources"
  type        = map(string)
  default     = {}
}
