output "app_instance_id" {
  description = "Application EC2 instance ID"
  value       = aws_instance.app.id
}

output "app_public_ip" {
  description = "Public IP address of the application server"
  value       = aws_instance.app.public_ip
}

output "app_private_ip" {
  description = "Private IP address of the application server"
  value       = aws_instance.app.private_ip
}

output "database_instance_id" {
  description = "PostgreSQL EC2 instance ID"
  value       = aws_instance.database.id
}

output "database_private_ip" {
  description = "Private IP address of PostgreSQL"
  value       = aws_instance.database.private_ip
}

output "redis_instance_id" {
  description = "Redis EC2 instance ID"
  value       = aws_instance.redis.id
}

output "redis_private_ip" {
  description = "Private IP address of Redis"
  value       = aws_instance.redis.private_ip
}