# ==================================================
# AEGIS Managed Data Services
#
# Status-Page runtime dependencies:
# - Amazon RDS PostgreSQL
# - Amazon ElastiCache Redis
#
# Both services are deployed only in the
# private data subnets across two Availability Zones.
# ==================================================


# --------------------------------------------------
# Existing VPC / EKS subnet discovery
# --------------------------------------------------

data "aws_vpc" "aegis_eks" {
  id = module.vpc_eks.vpc_id
}


data "aws_subnet" "aegis_private_eks" {
  for_each = toset(module.vpc_eks.private_eks_subnet_ids)

  id = each.value
}


# ==================================================
# PostgreSQL
# ==================================================

resource "aws_db_subnet_group" "status_page" {
  name = "${var.project_name}-${var.environment}-status-page-db"

  subnet_ids = module.vpc_eks.private_data_subnet_ids

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
    Component   = "status-page-database"
  }
}


resource "aws_security_group" "status_page_postgres" {
  name        = "${var.project_name}-${var.environment}-status-page-postgres"
  description = "PostgreSQL access only from AEGIS EKS Pod subnets."
  vpc_id      = module.vpc_eks.vpc_id

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
    Component   = "status-page-database"
  }
}


resource "aws_vpc_security_group_ingress_rule" "postgres_from_eks" {
  for_each = data.aws_subnet.aegis_private_eks

  security_group_id = aws_security_group.status_page_postgres.id

  description = "PostgreSQL from private EKS Pod subnet ${each.value.cidr_block}"

  cidr_ipv4   = each.value.cidr_block
  from_port   = 5432
  to_port     = 5432
  ip_protocol = "tcp"
}


resource "aws_vpc_security_group_egress_rule" "postgres_to_vpc" {
  security_group_id = aws_security_group.status_page_postgres.id

  description = "Restrict PostgreSQL egress to the AEGIS VPC."

  cidr_ipv4   = data.aws_vpc.aegis_eks.cidr_block
  ip_protocol = "-1"
}


resource "aws_db_instance" "status_page" {
  identifier = "${var.project_name}-${var.environment}-status-page"

  engine         = "postgres"
  engine_version = "16"

  instance_class = "db.t4g.micro"

  db_name  = "statuspage"
  username = "statuspage"

  # AWS manages the database password in Secrets Manager.
  # The password is therefore not stored directly in Terraform code.
  manage_master_user_password = true

  port = 5432

  allocated_storage     = 20
  max_allocated_storage = 100
  storage_type          = "gp3"
  storage_encrypted     = true

  multi_az = true

  db_subnet_group_name = aws_db_subnet_group.status_page.name

  vpc_security_group_ids = [
    aws_security_group.status_page_postgres.id
  ]

  publicly_accessible = false

  backup_retention_period = 7
  backup_window           = "03:00-04:00"
  maintenance_window      = "sun:04:00-sun:05:00"

  auto_minor_version_upgrade = true

  enabled_cloudwatch_logs_exports = [
    "postgresql",
    "upgrade"
  ]

  deletion_protection = true
  skip_final_snapshot = true

  apply_immediately = true

  copy_tags_to_snapshot = true

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
    Component   = "status-page-database"
    DataClass   = "application-state"
  }
}


# ==================================================
# Redis
# ==================================================

resource "aws_elasticache_subnet_group" "status_page" {
  name = "${var.project_name}-${var.environment}-status-page-redis"

  subnet_ids = module.vpc_eks.private_data_subnet_ids

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
    Component   = "status-page-cache"
  }
}


resource "aws_security_group" "status_page_redis" {
  name        = "${var.project_name}-${var.environment}-status-page-redis"
  description = "Redis access only from AEGIS EKS Pod subnets."
  vpc_id      = module.vpc_eks.vpc_id

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
    Component   = "status-page-cache"
  }
}


resource "aws_vpc_security_group_ingress_rule" "redis_from_eks" {
  for_each = data.aws_subnet.aegis_private_eks

  security_group_id = aws_security_group.status_page_redis.id

  description = "Redis from private EKS Pod subnet ${each.value.cidr_block}"

  cidr_ipv4   = each.value.cidr_block
  from_port   = 6379
  to_port     = 6379
  ip_protocol = "tcp"
}


resource "aws_vpc_security_group_egress_rule" "redis_to_vpc" {
  security_group_id = aws_security_group.status_page_redis.id

  description = "Restrict Redis egress to the AEGIS VPC."

  cidr_ipv4   = data.aws_vpc.aegis_eks.cidr_block
  ip_protocol = "-1"
}


resource "aws_elasticache_replication_group" "status_page" {
  replication_group_id = "${var.project_name}-${var.environment}-status-page"

  description = "AEGIS Status-Page Redis HA replication group."

  engine         = "redis"
  engine_version = "7.1"

  node_type = "cache.t4g.micro"
  port      = 6379

  # Primary + one replica distributed across AZs.
  num_cache_clusters = 2

  automatic_failover_enabled = true
  multi_az_enabled           = true

  subnet_group_name = aws_elasticache_subnet_group.status_page.name

  security_group_ids = [
    aws_security_group.status_page_redis.id
  ]

  at_rest_encryption_enabled = true
  transit_encryption_enabled = true

  auto_minor_version_upgrade = true

  snapshot_retention_limit = 3
  snapshot_window          = "02:00-03:00"
  maintenance_window       = "sun:05:00-sun:06:00"

  apply_immediately = true

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
    Component   = "status-page-cache"
    DataClass   = "application-cache"
  }
}
