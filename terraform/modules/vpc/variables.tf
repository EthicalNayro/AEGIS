variable "project_name" {
  description = "Name of the project."
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
  description = "CIDR block for the public application subnet."
  type        = string
}

variable "database_subnet_cidr" {
  description = "CIDR block for the PostgreSQL private subnet."
  type        = string
}

variable "redis_subnet_cidr" {
  description = "CIDR block for the Redis private subnet."
  type        = string
}