resource "aws_dynamodb_table" "security_findings" {
  name         = "${var.project_name}-${var.environment}-security-findings"
  billing_mode = "PAY_PER_REQUEST"

  hash_key = "incident_id"

  attribute {
    name = "incident_id"
    type = "S"
  }

  server_side_encryption {
    enabled = true
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
    Component   = "security-feedback"
  }
}
