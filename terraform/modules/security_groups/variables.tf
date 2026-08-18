variable "vpc_id" {
  description = "ID of the VPC where the security groups will be created."
  type        = string
}

variable "project_name" {
  description = "Project name used for resource naming."
  type        = string
}

variable "environment" {
  description = "Deployment environment."
  type        = string
}

variable "allowed_admin_cidr" {
  description = "IPv4 CIDR allowed to access administrative ports."
  type        = string
}