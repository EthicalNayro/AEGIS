output "ec2_role_name" {
  description = "Name of the IAM role used by EC2 instances."
  value       = aws_iam_role.ec2.name
}

output "ec2_role_arn" {
  description = "ARN of the IAM role used by EC2 instances."
  value       = aws_iam_role.ec2.arn
}

output "ec2_instance_profile_name" {
  description = "Name of the EC2 instance profile."
  value       = aws_iam_instance_profile.ec2.name
}

output "ssm_endpoint_security_group_id" {
  description = "Security group ID for the SSM VPC endpoints"
  value       = aws_security_group.ssm_endpoint.id
}