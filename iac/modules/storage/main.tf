# Referencia bucket S3 existente — não cria nem destrói
data "aws_s3_bucket" "this" {
  count  = var.enabled ? 1 : 0
  bucket = var.bucket_name
}
