# ==================================================
# Amazon EKS Control Plane
# ==================================================

resource "aws_eks_cluster" "this" {
  name     = var.cluster_name
  version  = var.cluster_version
  role_arn = var.cluster_role_arn

  enabled_cluster_log_types = var.enabled_cluster_log_types

  vpc_config {
    subnet_ids = var.cluster_subnet_ids

    endpoint_private_access = true
    endpoint_public_access  = var.endpoint_public_access

    public_access_cidrs = var.endpoint_public_access_cidrs
  }

  access_config {
    authentication_mode                         = "API"
    bootstrap_cluster_creator_admin_permissions = false
  }

  tags = {
    Name = var.cluster_name
  }
}


# ==================================================
# Explicit Kubernetes Administrator
#
# aegis-project-role authenticates to Kubernetes
# through the EKS Access API.
# ==================================================

resource "aws_eks_access_entry" "cluster_admin" {
  cluster_name  = aws_eks_cluster.this.name
  principal_arn = var.cluster_admin_principal_arn

  type = "STANDARD"
}


resource "aws_eks_access_policy_association" "cluster_admin" {
  cluster_name  = aws_eks_cluster.this.name
  principal_arn = aws_eks_access_entry.cluster_admin.principal_arn

  policy_arn = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy"

  access_scope {
    type = "cluster"
  }
}


# ==================================================
# EKS Pod Identity Agent
#
# Required for workloads that use EKS Pod Identity.
# ==================================================

resource "aws_eks_addon" "pod_identity_agent" {
  cluster_name = aws_eks_cluster.this.name
  addon_name   = "eks-pod-identity-agent"

  resolve_conflicts_on_create = "OVERWRITE"
  resolve_conflicts_on_update = "PRESERVE"
}


# ==================================================
# Amazon VPC CNI
#
# aws-node receives a dedicated IAM role through
# EKS Pod Identity instead of inheriting the node
# IAM role permissions.
# ==================================================

resource "aws_eks_addon" "vpc_cni" {
  cluster_name = aws_eks_cluster.this.name
  addon_name   = "vpc-cni"

  resolve_conflicts_on_create = "OVERWRITE"
  resolve_conflicts_on_update = "PRESERVE"

  pod_identity_association {
    service_account = "aws-node"
    role_arn        = var.vpc_cni_role_arn
  }

  depends_on = [
    aws_eks_addon.pod_identity_agent
  ]
}

# ==================================================
# Kubernetes Metrics Server
#
# Provides CPU and memory metrics through the
# metrics.k8s.io API for HPA/VPA and kubectl top.
#
# Metrics Server is installed as an EKS Community
# Add-on and does not require AWS IAM permissions.
# ==================================================

resource "aws_eks_addon" "metrics_server" {
  cluster_name = aws_eks_cluster.this.name
  addon_name   = "metrics-server"

  resolve_conflicts_on_create = "OVERWRITE"
  resolve_conflicts_on_update = "PRESERVE"

  depends_on = [
    aws_eks_node_group.general
  ]
}



# ==================================================
# EKS Managed Node Group
#
# EC2 instances exist underneath EKS, but they are
# Kubernetes workers rather than application servers.
# ==================================================

resource "aws_eks_node_group" "general" {
  cluster_name = aws_eks_cluster.this.name

  node_group_name = "${var.cluster_name}-general"

  node_role_arn = var.node_role_arn

  subnet_ids = var.node_subnet_ids

  ami_type = "AL2023_x86_64_STANDARD"

  instance_types = var.node_instance_types
  capacity_type  = var.node_capacity_type
  disk_size      = var.node_disk_size

  scaling_config {
    min_size     = var.node_min_size
    desired_size = var.node_desired_size
    max_size     = var.node_max_size
  }

  update_config {
    max_unavailable = 1
  }

  labels = {
    workload = "general"
  }

  tags = {
    Name = "${var.cluster_name}-general"
  }

  depends_on = [
    aws_eks_access_policy_association.cluster_admin,
    aws_eks_addon.pod_identity_agent,
    aws_eks_addon.vpc_cni,
  ]
}
