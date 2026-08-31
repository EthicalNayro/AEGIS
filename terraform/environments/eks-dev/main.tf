data "aws_availability_zones" "available" {
  state = "available"
}


# ==================================================
# External IAM prerequisites
#
# These roles are intentionally provisioned outside
# this environment and consumed as data sources.
# ==================================================

data "aws_iam_role" "eks_cluster" {
  name = var.eks_cluster_role_name
}

data "aws_iam_role" "eks_node" {
  name = var.eks_node_role_name
}

data "aws_iam_role" "vpc_cni" {
  name = var.vpc_cni_role_name
}

data "aws_iam_role" "deployment" {
  name = var.deployment_role_name
}


locals {
  selected_availability_zones = slice(
    data.aws_availability_zones.available.names,
    0,
    2
  )
}


# ==================================================
# Multi-AZ VPC
# ==================================================

module "vpc_eks" {
  source = "../../modules/vpc_eks"

  project_name = var.project_name
  environment  = var.environment
  cluster_name = var.cluster_name

  vpc_cidr = var.vpc_cidr

  availability_zones = local.selected_availability_zones

  public_subnet_cidrs       = var.public_subnet_cidrs
  eks_cluster_subnet_cidrs  = var.eks_cluster_subnet_cidrs
  private_eks_subnet_cidrs  = var.private_eks_subnet_cidrs
  private_data_subnet_cidrs = var.private_data_subnet_cidrs

  single_nat_gateway = var.single_nat_gateway
}


# ==================================================
# Amazon EKS
# ==================================================

module "eks" {
  source = "../../modules/eks"

  cluster_name    = var.cluster_name
  cluster_version = var.kubernetes_version

  cluster_role_arn = data.aws_iam_role.eks_cluster.arn
  node_role_arn    = data.aws_iam_role.eks_node.arn
  vpc_cni_role_arn = data.aws_iam_role.vpc_cni.arn

  cluster_admin_principal_arn = data.aws_iam_role.deployment.arn

  cluster_subnet_ids = module.vpc_eks.eks_cluster_subnet_ids
  node_subnet_ids    = module.vpc_eks.private_eks_subnet_ids

  endpoint_public_access = true

  endpoint_public_access_cidrs = var.cluster_endpoint_public_access_cidrs

  node_instance_types = [
    "t3.medium",
  ]

  node_capacity_type = "ON_DEMAND"

  node_min_size     = 2
  node_desired_size = 2
  node_max_size     = 4

  node_disk_size = 30
}

# ==================================================
# Karpenter
#
# Provides dynamic EKS node provisioning.
#
# Terraform manages:
# - Controller IAM Role
# - EKS Pod Identity association
# - Karpenter Node IAM Role
# - EKS Node Access Entry
# - SQS interruption queue
# - EventBridge interruption rules
# ==================================================

module "karpenter" {
  source  = "terraform-aws-modules/eks/aws//modules/karpenter"
  version = "21.24.2"

  cluster_name = module.eks.cluster_name

  namespace       = "kube-system"
  service_account = "karpenter"

  # Karpenter controller receives AWS permissions
  # through EKS Pod Identity.
  create_pod_identity_association = true

  # Handle Spot interruptions, rebalance recommendations,
  # EC2 state changes and scheduled maintenance.
  enable_spot_termination = true

  iam_role_use_name_prefix = false
  iam_role_name = format(
    "%s-%s-karpenter-controller",
    var.project_name,
    var.environment
  )

  node_iam_role_use_name_prefix = false
  node_iam_role_name = format(
    "%s-%s-karpenter-node",
    var.project_name,
    var.environment
  )

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
    Component   = "karpenter"
  }
}

# ==================================================
# Karpenter Security Group Discovery
#
# Karpenter uses this tag to discover the EKS
# cluster security group that should be attached
# to dynamically provisioned worker nodes.
# ==================================================

data "aws_eks_cluster" "aegis" {
  name = module.eks.cluster_name

  depends_on = [
    module.eks
  ]
}

resource "aws_ec2_tag" "karpenter_cluster_security_group_discovery" {
  resource_id = data.aws_eks_cluster.aegis.vpc_config[0].cluster_security_group_id

  key   = "karpenter.sh/discovery"
  value = module.eks.cluster_name
}

# ==================================================
# AWS Load Balancer Controller
#
# Provides AWS permissions to the Kubernetes
# AWS Load Balancer Controller through EKS Pod Identity.
# ==================================================

resource "aws_iam_role" "aws_load_balancer_controller" {
  name = "${var.project_name}-${var.environment}-aws-load-balancer-controller"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
      {
        Sid    = "PodIdentity"
        Effect = "Allow"

        Principal = {
          Service = "pods.eks.amazonaws.com"
        }

        Action = [
          "sts:AssumeRole",
          "sts:TagSession"
        ]
      }
    ]
  })

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
    Component   = "aws-load-balancer-controller"
  }
}


resource "aws_iam_policy" "aws_load_balancer_controller" {
  name = "${var.project_name}-${var.environment}-AWSLoadBalancerControllerIAMPolicy"

  description = "IAM permissions for the AEGIS AWS Load Balancer Controller."

  policy = file(
    "${path.module}/policies/aws-load-balancer-controller.json"
  )

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
    Component   = "aws-load-balancer-controller"
  }
}


resource "aws_iam_role_policy_attachment" "aws_load_balancer_controller" {
  role       = aws_iam_role.aws_load_balancer_controller.name
  policy_arn = aws_iam_policy.aws_load_balancer_controller.arn
}


resource "aws_eks_pod_identity_association" "aws_load_balancer_controller" {
  cluster_name = module.eks.cluster_name

  namespace       = "kube-system"
  service_account = "aws-load-balancer-controller"

  role_arn = aws_iam_role.aws_load_balancer_controller.arn

  depends_on = [
    aws_iam_role_policy_attachment.aws_load_balancer_controller
  ]

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
    Component   = "aws-load-balancer-controller"
  }
}

# ==================================================
# ACM Certificate
#
# Public TLS certificate for the AEGIS endpoint.
# DNS validation is performed through Dynu.
# ==================================================

resource "aws_acm_certificate" "aegis" {
  domain_name       = "app.aegis-project.ddnsfree.com"
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
    Component   = "ingress-tls"
  }
}
