locals {
  name_prefix = "${var.project_name}-${var.environment}"
}

# --------------------------------------------------
# Systems Manager API Endpoint
# --------------------------------------------------

resource "aws_vpc_endpoint" "ssm" {
  vpc_id            = var.vpc_id
  service_name      = "com.amazonaws.${var.aws_region}.ssm"
  vpc_endpoint_type = "Interface"

  subnet_ids = var.subnet_ids

  security_group_ids = [
    var.security_group_id
  ]

  private_dns_enabled = true

  tags = {
    Name = "${local.name_prefix}-ssm-endpoint"
  }
}

# --------------------------------------------------
# Systems Manager Session Manager Endpoint
# --------------------------------------------------

resource "aws_vpc_endpoint" "ssmmessages" {
  vpc_id            = var.vpc_id
  service_name      = "com.amazonaws.${var.aws_region}.ssmmessages"
  vpc_endpoint_type = "Interface"

  subnet_ids = var.subnet_ids

  security_group_ids = [
    var.security_group_id
  ]

  private_dns_enabled = true

  tags = {
    Name = "${local.name_prefix}-ssmmessages-endpoint"
  }
}