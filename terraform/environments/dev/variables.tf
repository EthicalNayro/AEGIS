variable "aws_region" {
  description = "AWS region used for the environment."
  type        = string
}

variable "project_name" {
  description = "Project name."
  type        = string
}

variable "environment" {
  description = "Deployment environment."
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC."
  type        = string
}

variable "public_subnet_cidr" {
  description = "Public application subnet."
  type        = string
}

variable "database_subnet_cidr" {
  description = "Private PostgreSQL subnet."
  type        = string
}

variable "redis_subnet_cidr" {
  description = "Private Redis subnet."
  type        = string
}

variable "owner_name" {
  description = "Name of the infrastructure owner."
  type        = string
}

variable "allowed_admin_cidr" {
  description = "IPv4 CIDR allowed to access SSH on the public application host."
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
