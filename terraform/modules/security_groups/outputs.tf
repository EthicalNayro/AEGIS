output "app_security_group_id" {
  description = "ID of the application security group."
  value       = aws_security_group.app.id
}

output "database_security_group_id" {
  description = "ID of the PostgreSQL security group."
  value       = aws_security_group.database.id
}

output "redis_security_group_id" {
  description = "ID of the Redis security group."
  value       = aws_security_group.redis.id
}