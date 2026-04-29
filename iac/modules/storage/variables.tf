variable "enabled" {
  description = "Set to true to create the S3 bucket"
  type        = bool
  default     = false
}

variable "bucket_name" {
  description = "S3 bucket name; required when enabled = true"
  type        = string
  default     = ""
}

variable "versioning_enabled" {
  description = "Enable S3 bucket versioning"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Tags to apply to the S3 bucket"
  type        = map(string)
  default     = {}
}
