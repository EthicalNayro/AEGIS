locals {
  name_prefix = "${var.project_name}-${var.environment}"
}

# --------------------------------------------------
# Ubuntu AMI
# --------------------------------------------------

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  filter {
    name   = "root-device-type"
    values = ["ebs"]
  }
}

# --------------------------------------------------
# SSH Key
# --------------------------------------------------

resource "aws_key_pair" "aegis" {
  key_name   = "${local.name_prefix}-key"
  public_key = file(pathexpand(var.ssh_public_key_path))

  tags = {
    Name = "${local.name_prefix}-key"
  }
}

# --------------------------------------------------
# Application Server
# --------------------------------------------------

resource "aws_instance" "app" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = var.app_instance_type

  subnet_id = var.public_app_subnet_id

  vpc_security_group_ids = [
    var.app_security_group_id
  ]

  key_name = aws_key_pair.aegis.key_name

  associate_public_ip_address = true

  metadata_options {
    http_endpoint = "enabled"
    http_tokens   = "required"
  }

  root_block_device {
    volume_type           = "gp3"
    volume_size           = 16
    encrypted             = true
    delete_on_termination = true
  }

  tags = {
    Name = "${local.name_prefix}-app"
    Role = "application"
  }
}

# --------------------------------------------------
# PostgreSQL Server
# --------------------------------------------------

resource "aws_instance" "database" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = var.database_instance_type

  subnet_id = var.private_database_subnet_id

  vpc_security_group_ids = [
    var.database_security_group_id
  ]

  key_name = aws_key_pair.aegis.key_name

  associate_public_ip_address = false

  metadata_options {
    http_endpoint = "enabled"
    http_tokens   = "required"
  }

  root_block_device {
    volume_type           = "gp3"
    volume_size           = 20
    encrypted             = true
    delete_on_termination = true
  }

  tags = {
    Name = "${local.name_prefix}-database"
    Role = "postgresql"
  }
}

# --------------------------------------------------
# Redis Server
# --------------------------------------------------

resource "aws_instance" "redis" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = var.redis_instance_type

  subnet_id = var.private_redis_subnet_id

  vpc_security_group_ids = [
    var.redis_security_group_id
  ]

  key_name = aws_key_pair.aegis.key_name

  associate_public_ip_address = false

  metadata_options {
    http_endpoint = "enabled"
    http_tokens   = "required"
  }

  root_block_device {
    volume_type           = "gp3"
    volume_size           = 12
    encrypted             = true
    delete_on_termination = true
  }

  tags = {
    Name = "${local.name_prefix}-redis"
    Role = "redis"
  }
}