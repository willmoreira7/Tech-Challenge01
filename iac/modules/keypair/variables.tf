variable "project_name" {
  description = "Project name used as the key pair name prefix"
  type        = string
}

variable "private_key_path" {
  description = "Local path to save the generated private key"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Tags to apply to the AWS key pair"
  type        = map(string)
  default     = {}
}
