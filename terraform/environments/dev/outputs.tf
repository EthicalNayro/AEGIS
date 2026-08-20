output "vpc_id" {
  description = "ID of the AEGIS VPC."
  value       = module.vpc.vpc_id
}

output "public_app_subnet_id" {
  description = "ID of the public application subnet."
  value       = module.vpc.public_app_subnet_id
}

output "private_database_subnet_id" {
  description = "ID of the private PostgreSQL subnet."
  value       = module.vpc.private_database_subnet_id
}

output "private_redis_subnet_id" {
  description = "ID of the private Redis subnet."
  value       = module.vpc.private_redis_subnet_id
}

output "app_security_group_id" {
  description = "ID of the application security group."
  value       = module.security_groups.app_security_group_id
}

output "database_security_group_id" {
  description = "ID of the PostgreSQL security group."
  value       = module.security_groups.database_security_group_id
}

output "redis_security_group_id" {
  description = "ID of the Redis security group."
  value       = module.security_groups.redis_security_group_id
}

output "app_public_ip" {
  description = "Public IP of the Status-Page application server"
  value       = module.ec2.app_public_ip
}

output "app_private_ip" {
  description = "Private IP of the Status-Page application server"
  value       = module.ec2.app_private_ip
}

output "database_private_ip" {
  description = "Private IP of the PostgreSQL server"
  value       = module.ec2.database_private_ip
}

output "redis_private_ip" {
  description = "Private IP of the Redis server"
  value       = module.ec2.redis_private_ip
}

output "nat_gateway_id" {
  description = "NAT Gateway ID"
  value       = module.vpc.nat_gateway_id
}

output "nat_eip" {
  description = "Public Elastic IP of the NAT Gateway"
  value       = module.vpc.nat_eip
}