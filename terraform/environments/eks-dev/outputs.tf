output "vpc_id" {
  value = module.vpc_eks.vpc_id
}

output "availability_zones" {
  value = module.vpc_eks.availability_zones
}

output "public_subnet_ids" {
  value = module.vpc_eks.public_subnet_ids
}

output "eks_cluster_subnet_ids" {
  value = module.vpc_eks.eks_cluster_subnet_ids
}

output "private_eks_subnet_ids" {
  value = module.vpc_eks.private_eks_subnet_ids
}

output "private_data_subnet_ids" {
  value = module.vpc_eks.private_data_subnet_ids
}

output "nat_gateway_ids" {
  value = module.vpc_eks.nat_gateway_ids
}
