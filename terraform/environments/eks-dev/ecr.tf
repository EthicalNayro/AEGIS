# ==================================================
# AEGIS Status-Page Container Registry
# ==================================================

resource "aws_ecr_repository" "status_page" {
  name = "${var.project_name}-${var.environment}-status-page"

  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  force_delete = false

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
    Component   = "status-page-container"
  }
}


resource "aws_ecr_lifecycle_policy" "status_page" {
  repository = aws_ecr_repository.status_page.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1

        description = "Remove untagged images after 7 days"

        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = 7
        }

        action = {
          type = "expire"
        }
      }
    ]
  })
}
