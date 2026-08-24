output "vpc_id" {
  description = "ID of the EKS VPC."
  value       = aws_vpc.this.id
}

output "vpc_cidr" {
  description = "CIDR of the EKS VPC."
  value       = aws_vpc.this.cidr_block
}

output "availability_zones" {
  description = "Availability Zones used by the platform."
  value       = var.availability_zones
}

output "public_subnet_ids" {
  description = "Public subnet IDs for Internet-facing load balancers and NAT Gateways."
  value = [
    for az in var.availability_zones :
    aws_subnet.public[az].id
  ]
}

output "eks_cluster_subnet_ids" {
  description = "Dedicated subnet IDs for EKS control-plane ENIs."
  value = [
    for az in var.availability_zones :
    aws_subnet.eks_cluster[az].id
  ]
}

output "private_eks_subnet_ids" {
  description = "Private subnet IDs for EKS nodes and Pods."
  value = [
    for az in var.availability_zones :
    aws_subnet.private_eks[az].id
  ]
}

output "private_data_subnet_ids" {
  description = "Private subnet IDs for RDS and ElastiCache."
  value = [
    for az in var.availability_zones :
    aws_subnet.private_data[az].id
  ]
}

output "nat_gateway_ids" {
  description = "NAT Gateway IDs used by the EKS node subnets."
  value = [
    for az in sort(keys(local.nat_azs)) :
    aws_nat_gateway.this[az].id
  ]
}

output "public_route_table_id" {
  description = "Public route table ID."
  value       = aws_route_table.public.id
}

output "private_eks_route_table_ids" {
  description = "Private EKS route table IDs."
  value = [
    for az in var.availability_zones :
    aws_route_table.private_eks[az].id
  ]
}

output "eks_cluster_route_table_ids" {
  description = "EKS control-plane route table IDs."
  value = [
    for az in var.availability_zones :
    aws_route_table.eks_cluster[az].id
  ]
}

output "private_data_route_table_ids" {
  description = "Private data route table IDs."
  value = [
    for az in var.availability_zones :
    aws_route_table.private_data[az].id
  ]
}
