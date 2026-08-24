variable "aws_region" {
  description = "AWS Region used by the environment."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name."
  type        = string
  default     = "aegis"
}

variable "environment" {
  description = "Environment name."
  type        = string
  default     = "eks-dev"
}

variable "owner_name" {
  description = "Owner tag required by the AWS environment."
  type        = string
  default     = "Oryan"
}

variable "cluster_name" {
  description = "EKS cluster name."
  type        = string
  default     = "aegis-eks-dev"
}

variable "vpc_cidr" {
  description = "CIDR for the modernized EKS VPC."
  type        = string
  default     = "10.10.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "Public subnet CIDRs."
  type        = list(string)

  default = [
    "10.10.0.0/24",
    "10.10.1.0/24",
  ]
}

variable "eks_cluster_subnet_cidrs" {
  description = "Dedicated EKS control-plane subnet CIDRs."
  type        = list(string)

  default = [
    "10.10.2.0/28",
    "10.10.2.16/28",
  ]
}

variable "private_eks_subnet_cidrs" {
  description = "Private EKS node and Pod subnet CIDRs."
  type        = list(string)

  default = [
    "10.10.16.0/20",
    "10.10.32.0/20",
  ]
}

variable "private_data_subnet_cidrs" {
  description = "Private data subnet CIDRs."
  type        = list(string)

  default = [
    "10.10.64.0/24",
    "10.10.65.0/24",
  ]
}

variable "single_nat_gateway" {
  description = "Use one NAT Gateway in development to reduce cost."
  type        = bool
  default     = true
}
