output "cluster_name" {
  description = "EKS cluster name."
  value       = aws_eks_cluster.this.name
}

output "cluster_arn" {
  description = "EKS cluster ARN."
  value       = aws_eks_cluster.this.arn
}

output "cluster_version" {
  description = "Kubernetes version used by the cluster."
  value       = aws_eks_cluster.this.version
}

output "cluster_endpoint" {
  description = "Kubernetes API endpoint."
  value       = aws_eks_cluster.this.endpoint
}

output "cluster_certificate_authority_data" {
  description = "Base64 encoded Kubernetes certificate authority."
  value       = aws_eks_cluster.this.certificate_authority[0].data
  sensitive   = true
}

output "cluster_security_group_id" {
  description = "Security Group created by EKS for the cluster."
  value       = aws_eks_cluster.this.vpc_config[0].cluster_security_group_id
}

output "node_group_name" {
  description = "Managed node group name."
  value       = aws_eks_node_group.general.node_group_name
}

output "node_group_status" {
  description = "Managed node group status."
  value       = aws_eks_node_group.general.status
}

output "vpc_cni_addon_arn" {
  description = "ARN of the Amazon VPC CNI EKS add-on."
  value       = aws_eks_addon.vpc_cni.arn
}
