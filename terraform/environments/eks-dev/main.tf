data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  selected_availability_zones = slice(
    data.aws_availability_zones.available.names,
    0,
    2
  )
}

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
