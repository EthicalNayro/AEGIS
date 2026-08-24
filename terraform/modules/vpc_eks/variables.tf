variable "project_name" {
  description = "Project name used for resource naming."
  type        = string
}

variable "environment" {
  description = "Deployment environment."
  type        = string
}

variable "cluster_name" {
  description = "EKS cluster name associated with this network."
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block for the EKS VPC."
  type        = string
}

variable "availability_zones" {
  description = "Exactly two Availability Zones used by the EKS platform."
  type        = list(string)

  validation {
    condition     = length(var.availability_zones) == 2
    error_message = "Exactly two Availability Zones must be provided."
  }
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public load-balancer/NAT subnets."
  type        = list(string)

  validation {
    condition     = length(var.public_subnet_cidrs) == 2
    error_message = "Exactly two public subnet CIDRs must be provided."
  }
}

variable "eks_cluster_subnet_cidrs" {
  description = "CIDR blocks dedicated to EKS control-plane ENIs."
  type        = list(string)

  validation {
    condition     = length(var.eks_cluster_subnet_cidrs) == 2
    error_message = "Exactly two EKS cluster subnet CIDRs must be provided."
  }
}

variable "private_eks_subnet_cidrs" {
  description = "CIDR blocks for private EKS nodes and Pods."
  type        = list(string)

  validation {
    condition     = length(var.private_eks_subnet_cidrs) == 2
    error_message = "Exactly two private EKS subnet CIDRs must be provided."
  }
}

variable "private_data_subnet_cidrs" {
  description = "CIDR blocks for private managed data services."
  type        = list(string)

  validation {
    condition     = length(var.private_data_subnet_cidrs) == 2
    error_message = "Exactly two private data subnet CIDRs must be provided."
  }
}

variable "single_nat_gateway" {
  description = "Use one NAT Gateway for cost-optimized development. Set false for one NAT Gateway per AZ."
  type        = bool
  default     = true
}
