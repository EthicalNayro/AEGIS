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


# ==================================================
# EKS
# ==================================================

variable "kubernetes_version" {
  description = "Kubernetes minor version used by Amazon EKS."
  type        = string
  default     = "1.36"
}

variable "eks_cluster_role_name" {
  description = "Existing EKS control-plane IAM role."
  type        = string
  default     = "aegis-eks-cluster-role"
}

variable "eks_node_role_name" {
  description = "Existing EKS managed-node IAM role."
  type        = string
  default     = "aegis-eks-node-role"
}

variable "vpc_cni_role_name" {
  description = "Existing VPC CNI Pod Identity IAM role."
  type        = string
  default     = "aegis-vpc-cni-role"
}

variable "project_role_name" {
  description = "Existing AEGIS deployment/operator IAM role."
  type        = string
  default     = "aegis-project-role"
}

variable "cluster_endpoint_public_access_cidrs" {
  description = "CIDRs allowed to access the Kubernetes public API endpoint."
  type        = list(string)
}

variable "eks_node_instance_types" {
  description = "EC2 instance types used by EKS worker nodes."
  type        = list(string)

  default = [
    "t3.medium",
  ]
}

variable "eks_node_capacity_type" {
  description = "Capacity type used by the EKS managed node group."
  type        = string
  default     = "ON_DEMAND"
}

variable "eks_node_min_size" {
  description = "Minimum EKS worker node count."
  type        = number
  default     = 2
}

variable "eks_node_desired_size" {
  description = "Desired EKS worker node count."
  type        = number
  default     = 2
}

variable "eks_node_max_size" {
  description = "Maximum EKS worker node count."
  type        = number
  default     = 4
}


variable "deployment_role_name" {
  description = "IAM role used by Terraform and granted Kubernetes administrator access."
  type        = string
  default     = "aegis-project-role"
}

variable "deployment_role_arn" {
  description = "IAM role assumed by Terraform for AEGIS infrastructure deployment."
  type        = string
}