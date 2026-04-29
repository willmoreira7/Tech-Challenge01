output "bucket_name" {
  description = "S3 bucket name (empty string if not enabled)"
  value       = var.enabled ? aws_s3_bucket.this[0].bucket : ""
}

output "bucket_arn" {
  description = "S3 bucket ARN (empty string if not enabled)"
  value       = var.enabled ? aws_s3_bucket.this[0].arn : ""
}
