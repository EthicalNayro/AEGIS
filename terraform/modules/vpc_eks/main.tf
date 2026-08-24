locals {
  name_prefix = "${var.project_name}-${var.environment}"

  az_index = {
    for index, az in var.availability_zones :
    az => index
  }

  # Development can use one NAT Gateway to reduce cost.
  # Setting single_nat_gateway=false creates one NAT Gateway per AZ.
  nat_azs = var.single_nat_gateway ? {
    (var.availability_zones[0]) = 0
  } : local.az_index
}


# ==================================================
# VPC
# ==================================================

resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name    = "${local.name_prefix}-vpc"
    Cluster = var.cluster_name
  }
}


resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id

  tags = {
    Name = "${local.name_prefix}-igw"
  }
}


# ==================================================
# Public Subnets
# ALB + NAT Gateway placement
# ==================================================

resource "aws_subnet" "public" {
  for_each = local.az_index

  vpc_id                  = aws_vpc.this.id
  availability_zone       = each.key
  cidr_block              = var.public_subnet_cidrs[each.value]
  map_public_ip_on_launch = true

  tags = {
    Name                     = "${local.name_prefix}-public-${each.value + 1}"
    Tier                     = "public"
    "kubernetes.io/role/elb" = "1"
  }
}


# ==================================================
# Dedicated EKS Control-Plane Subnets
# ==================================================

resource "aws_subnet" "eks_cluster" {
  for_each = local.az_index

  vpc_id                  = aws_vpc.this.id
  availability_zone       = each.key
  cidr_block              = var.eks_cluster_subnet_cidrs[each.value]
  map_public_ip_on_launch = false

  tags = {
    Name = "${local.name_prefix}-eks-control-${each.value + 1}"
    Tier = "eks-control-plane"
  }
}


# ==================================================
# Private EKS Node / Pod Subnets
# ==================================================

resource "aws_subnet" "private_eks" {
  for_each = local.az_index

  vpc_id                  = aws_vpc.this.id
  availability_zone       = each.key
  cidr_block              = var.private_eks_subnet_cidrs[each.value]
  map_public_ip_on_launch = false

  tags = {
    Name                              = "${local.name_prefix}-private-eks-${each.value + 1}"
    Tier                              = "private-eks"
    "kubernetes.io/role/internal-elb" = "1"
  }
}


# ==================================================
# Private Data Subnets
# RDS / ElastiCache
# ==================================================

resource "aws_subnet" "private_data" {
  for_each = local.az_index

  vpc_id                  = aws_vpc.this.id
  availability_zone       = each.key
  cidr_block              = var.private_data_subnet_cidrs[each.value]
  map_public_ip_on_launch = false

  tags = {
    Name = "${local.name_prefix}-private-data-${each.value + 1}"
    Tier = "private-data"
  }
}


# ==================================================
# Public Routing
# ==================================================

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.this.id

  tags = {
    Name = "${local.name_prefix}-public-rt"
  }
}


resource "aws_route" "public_internet" {
  route_table_id         = aws_route_table.public.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.this.id
}


resource "aws_route_table_association" "public" {
  for_each = local.az_index

  subnet_id      = aws_subnet.public[each.key].id
  route_table_id = aws_route_table.public.id
}


# ==================================================
# NAT Gateways
# ==================================================

resource "aws_eip" "nat" {
  for_each = local.nat_azs

  domain = "vpc"

  tags = {
    Name = "${local.name_prefix}-nat-eip-${each.value + 1}"
  }
}


resource "aws_nat_gateway" "this" {
  for_each = local.nat_azs

  allocation_id = aws_eip.nat[each.key].id
  subnet_id     = aws_subnet.public[each.key].id

  depends_on = [
    aws_internet_gateway.this
  ]

  tags = {
    Name = "${local.name_prefix}-nat-${each.value + 1}"
  }
}


# ==================================================
# Private EKS Node Routing
# ==================================================

resource "aws_route_table" "private_eks" {
  for_each = local.az_index

  vpc_id = aws_vpc.this.id

  tags = {
    Name = "${local.name_prefix}-private-eks-rt-${each.value + 1}"
  }
}


resource "aws_route" "private_eks_internet" {
  for_each = local.az_index

  route_table_id         = aws_route_table.private_eks[each.key].id
  destination_cidr_block = "0.0.0.0/0"

  nat_gateway_id = var.single_nat_gateway ? (
    aws_nat_gateway.this[var.availability_zones[0]].id
    ) : (
    aws_nat_gateway.this[each.key].id
  )
}


resource "aws_route_table_association" "private_eks" {
  for_each = local.az_index

  subnet_id      = aws_subnet.private_eks[each.key].id
  route_table_id = aws_route_table.private_eks[each.key].id
}


# ==================================================
# EKS Control-Plane Routing
#
# No default Internet route is intentionally added.
# These subnets are reserved for EKS-managed ENIs.
# ==================================================

resource "aws_route_table" "eks_cluster" {
  for_each = local.az_index

  vpc_id = aws_vpc.this.id

  tags = {
    Name = "${local.name_prefix}-eks-control-rt-${each.value + 1}"
  }
}


resource "aws_route_table_association" "eks_cluster" {
  for_each = local.az_index

  subnet_id      = aws_subnet.eks_cluster[each.key].id
  route_table_id = aws_route_table.eks_cluster[each.key].id
}


# ==================================================
# Private Data Routing
#
# No default Internet route is intentionally added.
# Managed databases remain isolated from Internet egress.
# ==================================================

resource "aws_route_table" "private_data" {
  for_each = local.az_index

  vpc_id = aws_vpc.this.id

  tags = {
    Name = "${local.name_prefix}-private-data-rt-${each.value + 1}"
  }
}


resource "aws_route_table_association" "private_data" {
  for_each = local.az_index

  subnet_id      = aws_subnet.private_data[each.key].id
  route_table_id = aws_route_table.private_data[each.key].id
}
