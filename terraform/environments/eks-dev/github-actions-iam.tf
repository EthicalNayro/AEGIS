locals {
  github_actions_oidc_provider_arn = "arn:aws:iam::992382545251:oidc-provider/token.actions.githubusercontent.com"
}

resource "aws_iam_role" "github_actions_ci" {
  name = "aegis-eks-dev-github-ci"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
      {
        Sid    = "GitHubActionsOIDC"
        Effect = "Allow"

        Principal = {
          Federated = local.github_actions_oidc_provider_arn
        }

        Action = "sts:AssumeRoleWithWebIdentity"

        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"

            "token.actions.githubusercontent.com:sub" = "repo:EthicalNayro@252874744/AEGIS@1338594901:ref:refs/heads/phase-1-1/platform-modernization"
          }
        }
      }
    ]
  })

  tags = {
    Project     = "aegis"
    Environment = "eks-dev"
    Component   = "github-ci"
  }
}

resource "aws_iam_role_policy" "github_actions_ci_ecr" {
  name = "ecr-push-only"
  role = aws_iam_role.github_actions_ci.id

  policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
      {
        Sid    = "GetECRAuthorizationToken"
        Effect = "Allow"

        Action = [
          "ecr:GetAuthorizationToken"
        ]

        Resource = "*"
      },
      {
        Sid    = "PushStatusPageImage"
        Effect = "Allow"

        Action = [
          "ecr:BatchCheckLayerAvailability",
          "ecr:CompleteLayerUpload",
          "ecr:GetDownloadUrlForLayer",
          "ecr:InitiateLayerUpload",
          "ecr:PutImage",
          "ecr:UploadLayerPart",
          "ecr:BatchGetImage",
          "ecr:DescribeImages"
        ]

        Resource = aws_ecr_repository.status_page.arn
      }
    ]
  })
}

output "github_actions_ci_role_arn" {
  description = "GitHub Actions OIDC CI role"
  value       = aws_iam_role.github_actions_ci.arn
}
