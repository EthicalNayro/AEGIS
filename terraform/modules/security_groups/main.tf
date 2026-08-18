locals {
  name_prefix = "${var.project_name}-${var.environment}"
}

# --------------------------------------------------
# Application Security Group
# --------------------------------------------------

resource "aws_security_group" "app" {
  name        = "${local.name_prefix}-app-sg"
  description = "Security group for the Status-Page application server"
  vpc_id      = var.vpc_id

  tags = {
    Name = "${local.name_prefix}-app-sg"
  }
}

# HTTPS from the Internet
resource "aws_vpc_security_group_ingress_rule" "app_https" {
  security_group_id = aws_security_group.app.id

  description = "Allow HTTPS from the Internet"
  cidr_ipv4   = "0.0.0.0/0"
  from_port   = 443
  to_port     = 443
  ip_protocol = "tcp"
}

# SSH only from the administrator IP
resource "aws_vpc_security_group_ingress_rule" "app_ssh" {
  security_group_id = aws_security_group.app.id

  description = "Allow SSH from administrator"
  cidr_ipv4   = var.allowed_admin_cidr
  from_port   = 22
  to_port     = 22
  ip_protocol = "tcp"
}

# Django development server - testing only
resource "aws_vpc_security_group_ingress_rule" "app_dev" {
  security_group_id = aws_security_group.app.id

  description = "Allow Django development server from administrator"
  cidr_ipv4   = var.allowed_admin_cidr
  from_port   = 8000
  to_port     = 8000
  ip_protocol = "tcp"
}

# Application server needs outbound access
resource "aws_vpc_security_group_egress_rule" "app_outbound" {
  security_group_id = aws_security_group.app.id

  description = "Allow outbound traffic from application server"
  cidr_ipv4   = "0.0.0.0/0"
  ip_protocol = "-1"
}


# --------------------------------------------------
# PostgreSQL Security Group
# --------------------------------------------------

resource "aws_security_group" "database" {
  name        = "${local.name_prefix}-database-sg"
  description = "Security group for PostgreSQL"
  vpc_id      = var.vpc_id

  tags = {
    Name = "${local.name_prefix}-database-sg"
  }
}

resource "aws_vpc_security_group_ingress_rule" "database_from_app" {
  security_group_id = aws_security_group.database.id

  description                  = "Allow PostgreSQL access from application server"
  referenced_security_group_id = aws_security_group.app.id

  from_port   = 5432
  to_port     = 5432
  ip_protocol = "tcp"
}


# --------------------------------------------------
# Redis Security Group
# --------------------------------------------------

resource "aws_security_group" "redis" {
  name        = "${local.name_prefix}-redis-sg"
  description = "Security group for Redis"
  vpc_id      = var.vpc_id

  tags = {
    Name = "${local.name_prefix}-redis-sg"
  }
}

resource "aws_vpc_security_group_ingress_rule" "redis_from_app" {
  security_group_id = aws_security_group.redis.id

  description                  = "Allow Redis access from application server"
  referenced_security_group_id = aws_security_group.app.id

  from_port   = 6379
  to_port     = 6379
  ip_protocol = "tcp"
}