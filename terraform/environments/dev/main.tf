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

module "ec2" {
  source = "../../modules/ec2"

  project_name = var.project_name
  environment  = var.environment

  # Subnets
  public_app_subnet_id       = module.vpc.public_app_subnet_id
  private_database_subnet_id = module.vpc.private_database_subnet_id
  private_redis_subnet_id    = module.vpc.private_redis_subnet_id

  # Security Groups
  app_security_group_id      = module.security_groups.app_security_group_id
  database_security_group_id = module.security_groups.database_security_group_id
  redis_security_group_id    = module.security_groups.redis_security_group_id

  # Instance Types
  app_instance_type      = var.app_instance_type
  database_instance_type = var.database_instance_type
  redis_instance_type    = var.redis_instance_type

  # SSH
  ssh_public_key_path = var.ssh_public_key_path
}
