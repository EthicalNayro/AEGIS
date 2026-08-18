module "vpc" {
  source = "../../modules/vpc"

  project_name = var.project_name
  environment  = var.environment

  vpc_cidr             = var.vpc_cidr
  public_subnet_cidr   = var.public_subnet_cidr
  database_subnet_cidr = var.database_subnet_cidr
  redis_subnet_cidr    = var.redis_subnet_cidr
}

module "security_groups" {
  source = "../../modules/security_groups"

  vpc_id             = module.vpc.vpc_id
  project_name       = var.project_name
  environment        = var.environment
  allowed_admin_cidr = var.allowed_admin_cidr
}