variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "public_app_subnet_id" {
  description = "Subnet ID for the application server"
  type        = string
}

variable "private_database_subnet_id" {
  description = "Subnet ID for the PostgreSQL server"
  type        = string
}

variable "private_redis_subnet_id" {
  description = "Subnet ID for the Redis server"
  type        = string
}

variable "app_security_group_id" {
  description = "Security group ID for the application server"
  type        = string
}

variable "database_security_group_id" {
  description = "Security group ID for PostgreSQL"
  type        = string
}

variable "redis_security_group_id" {
  description = "Security group ID for Redis"
  type        = string
}

variable "app_instance_type" {
  description = "EC2 instance type for the application server"
  type        = string
}

variable "database_instance_type" {
  description = "EC2 instance type for PostgreSQL"
  type        = string
}

variable "redis_instance_type" {
  description = "EC2 instance type for Redis"
  type        = string
}

variable "ssh_public_key_path" {
  description = "Local path to the SSH public key"
  type        = string
}