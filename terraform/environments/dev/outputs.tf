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