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