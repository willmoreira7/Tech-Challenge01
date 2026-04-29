output "instance_profile_name" {
  description = "Name of the IAM instance profile to attach to EC2"
  value       = aws_iam_instance_profile.this.name
}

output "role_arn" {
  description = "ARN of the IAM role"
  value       = aws_iam_role.this.arn
}
