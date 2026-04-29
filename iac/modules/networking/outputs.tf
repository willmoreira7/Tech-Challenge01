output "security_group_id" {
  description = "ID of the created security group"
  value       = aws_security_group.this.id
}

output "vpc_id" {
  description = "ID of the VPC where the security group was created"
  value       = data.aws_vpc.this.id
}
