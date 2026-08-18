module "vpc" {
  source = "../../modules/vpc"

  project_name = var.project_name
  environment  = var.environment

  vpc_cidr             = var.vpc_cidr
  public_subnet_cidr   = var.public_subnet_cidr
  database_subnet_cidr = var.database_subnet_cidr
  redis_subnet_cidr    = var.redis_subnet_cidr
}