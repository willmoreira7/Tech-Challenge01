variable "enabled" {
  description = "Set to true to reference the existing S3 bucket"
  type        = bool
  default     = false
}

variable "bucket_name" {
  description = "S3 bucket name; required when enabled = true"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Tags to apply to the S3 bucket"
  type        = map(string)
  default     = {}
}
