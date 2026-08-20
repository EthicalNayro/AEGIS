output "vpc_id" {
  description = "ID of the VPC."
  value       = aws_vpc.main.id
}

output "public_app_subnet_id" {
  description = "ID of the public application subnet."
  value       = aws_subnet.public_app.id
}

output "private_database_subnet_id" {
  description = "ID of the private PostgreSQL subnet."
  value       = aws_subnet.private_database.id
}

output "private_redis_subnet_id" {
  description = "ID of the private Redis subnet."
  value       = aws_subnet.private_redis.id
}

output "public_route_table_id" {
  description = "ID of the public route table."
  value       = aws_route_table.public.id
}

output "private_route_table_id" {
  description = "ID of the private route table."
  value       = aws_route_table.private.id
}

output "nat_gateway_id" {
  description = "ID of the NAT Gateway"
  value       = aws_nat_gateway.main.id
}

output "nat_eip" {
  description = "Elastic IP address of the NAT Gateway"
  value       = aws_eip.nat.public_ip
}