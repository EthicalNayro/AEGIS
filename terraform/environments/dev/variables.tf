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