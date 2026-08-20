locals {
  name_prefix = "${var.project_name}-${var.environment}"
}

data "aws_iam_policy_document" "ec2_assume_role" {
  statement {
    effect = "Allow"

    actions = [
      "sts:AssumeRole"
    ]

    principals {
      type = "Service"

      identifiers = [
        "ec2.amazonaws.com"
      ]
    }
  }
}

resource "aws_iam_role" "ec2" {
  name = "${local.name_prefix}-ec2-role"

  assume_role_policy = data.aws_iam_policy_document.ec2_assume_role.json

  tags = {
    Name = "${local.name_prefix}-ec2-role"
  }
}

resource "aws_iam_role_policy_attachment" "ssm" {
  role = aws_iam_role.ec2.name

  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "ec2" {
  name = "${local.name_prefix}-ec2-instance-profile"

  role = aws_iam_role.ec2.name

  tags = {
    Name = "${local.name_prefix}-ec2-instance-profile"
  }
}

# --------------------------------------------------
# SSM VPC Endpoint Security Group
# --------------------------------------------------

resource "aws_security_group" "ssm_endpoint" {
  name        = "${local.name_prefix}-ssm-endpoint-sg"
  description = "Security group for SSM VPC interface endpoints"
  vpc_id      = var.vpc_id

  tags = {
    Name = "${local.name_prefix}-ssm-endpoint-sg"
  }
}

resource "aws_vpc_security_group_ingress_rule" "ssm_from_app" {
  security_group_id = aws_security_group.ssm_endpoint.id

  description                  = "Allow HTTPS from application server to SSM endpoints"
  referenced_security_group_id = aws_security_group.app.id

  from_port   = 443
  to_port     = 443
  ip_protocol = "tcp"
}

resource "aws_vpc_security_group_ingress_rule" "ssm_from_database" {
  security_group_id = aws_security_group.ssm_endpoint.id

  description                  = "Allow HTTPS from database server to SSM endpoints"
  referenced_security_group_id = aws_security_group.database.id

  from_port   = 443
  to_port     = 443
  ip_protocol = "tcp"
}

resource "aws_vpc_security_group_ingress_rule" "ssm_from_redis" {
  security_group_id = aws_security_group.ssm_endpoint.id

  description                  = "Allow HTTPS from Redis server to SSM endpoints"
  referenced_security_group_id = aws_security_group.redis.id

  from_port   = 443
  to_port     = 443
  ip_protocol = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "database_to_ssm" {
  security_group_id = aws_security_group.database.id

  description                  = "Allow HTTPS from database server to SSM endpoints"
  referenced_security_group_id = aws_security_group.ssm_endpoint.id

  from_port   = 443
  to_port     = 443
  ip_protocol = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "redis_to_ssm" {
  security_group_id = aws_security_group.redis.id

  description                  = "Allow HTTPS from Redis server to SSM endpoints"
  referenced_security_group_id = aws_security_group.ssm_endpoint.id

  from_port   = 443
  to_port     = 443
  ip_protocol = "tcp"
}