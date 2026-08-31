variable "cluster_name" {
  description = "Name of the Amazon EKS cluster."
  type        = string
}

variable "cluster_version" {
  description = "Kubernetes minor version used by Amazon EKS."
  type        = string
  default     = "1.36"
}

variable "cluster_role_arn" {
  description = "Externally provisioned IAM role assumed by the EKS control plane."
  type        = string
}

variable "node_role_arn" {
  description = "Externally provisioned IAM role assumed by EKS worker nodes."
  type        = string
}

variable "vpc_cni_role_arn" {
  description = "Externally provisioned EKS Pod Identity role for the Amazon VPC CNI."
  type        = string
}

variable "cluster_admin_principal_arn" {
  description = "IAM principal granted cluster-admin access using the EKS Access API."
  type        = string
}

variable "cluster_subnet_ids" {
  description = "Dedicated subnet IDs used by EKS control-plane ENIs."
  type        = list(string)

  validation {
    condition     = length(var.cluster_subnet_ids) >= 2
    error_message = "At least two cluster subnets are required."
  }
}

variable "node_subnet_ids" {
  description = "Private subnets used by EKS managed worker nodes."
  type        = list(string)

  validation {
    condition     = length(var.node_subnet_ids) >= 2
    error_message = "At least two node subnets are required."
  }
}

variable "endpoint_public_access" {
  description = "Enable the public Kubernetes API endpoint."
  type        = bool
  default     = true
}

variable "endpoint_public_access_cidrs" {
  description = "CIDRs allowed to reach the public Kubernetes API endpoint."
  type        = list(string)
}

variable "node_instance_types" {
  description = "Instance types used by the general managed node group."
  type        = list(string)

  default = [
    "t3.medium",
  ]
}

variable "node_capacity_type" {
  description = "Capacity type for EKS nodes."
  type        = string
  default     = "ON_DEMAND"

  validation {
    condition = contains(
      [
        "ON_DEMAND",
        "SPOT",
      ],
      var.node_capacity_type
    )

    error_message = "node_capacity_type must be ON_DEMAND or SPOT."
  }
}

variable "node_min_size" {
  description = "Minimum number of worker nodes."
  type        = number
  default     = 2
}

variable "node_desired_size" {
  description = "Desired number of worker nodes."
  type        = number
  default     = 2
}

variable "node_max_size" {
  description = "Maximum number of worker nodes."
  type        = number
  default     = 4
}

variable "node_disk_size" {
  description = "Root disk size in GiB for worker nodes."
  type        = number
  default     = 30
}

variable "enabled_cluster_log_types" {
  description = "EKS control-plane logs sent to CloudWatch."
  type        = list(string)

  default = [
    "api",
    "audit",
    "authenticator",
    "controllerManager",
    "scheduler",
  ]
}
