# ==================================================
# AEGIS Status-Page Human Review IAM
#
# Dedicated EKS Pod Identity used by the
# Status-Page Django workload.
#
# The workload may only:
# - list AEGIS security findings;
# - read a specific finding;
# - record human review feedback.
# ==================================================

locals {
  aegis_status_page_reviewer_role_name = "aegis-eks-dev-status-page-reviewer"

  aegis_status_page_service_account = "aegis-status-page"

  aegis_status_page_namespace = "aegis-system"

  aegis_security_findings_table_arn = "arn:aws:dynamodb:us-east-1:992382545251:table/aegis-eks-dev-security-findings"

  aegis_eks_cluster_arn = "arn:aws:eks:us-east-1:992382545251:cluster/aegis-eks-dev"
}


# --------------------------------------------------
# Reviewer IAM Role
# --------------------------------------------------

resource "aws_iam_role" "status_page_reviewer" {
  name = local.aegis_status_page_reviewer_role_name

  assume_role_policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
      {
        Sid    = "AllowAEGISStatusPagePodIdentity"
        Effect = "Allow"

        Principal = {
          Service = "pods.eks.amazonaws.com"
        }

        Action = [
          "sts:AssumeRole",
          "sts:TagSession"
        ]

        Condition = {
          StringEquals = {
            "aws:RequestTag/kubernetes-namespace" = (
              local.aegis_status_page_namespace
            )

            "aws:RequestTag/kubernetes-service-account" = (
              local.aegis_status_page_service_account
            )

            "aws:RequestTag/eks-cluster-arn" = (
              local.aegis_eks_cluster_arn
            )
          }
        }
      }
    ]
  })

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
    Component   = "status-page-reviewer"
  }
}


# --------------------------------------------------
# Least-Privilege DynamoDB Runtime Policy
# --------------------------------------------------

resource "aws_iam_role_policy" "status_page_reviewer_dynamodb" {
  name = "AEGISStatusPageHumanReview"

  role = aws_iam_role.status_page_reviewer.id

  policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
      {
        Sid    = "ReadAndReviewAEGISSecurityFindings"
        Effect = "Allow"

        Action = [
          "dynamodb:Scan",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem"
        ]

        Resource = local.aegis_security_findings_table_arn
      },
      {
        Sid    = "ReadOnlyStatusPageRDSCredentials"
        Effect = "Allow"

        Action = [
          "secretsmanager:GetSecretValue"
        ]

        Resource = aws_db_instance.status_page.master_user_secret[0].secret_arn
      }
    ]
  })
}


# --------------------------------------------------
# EKS Pod Identity Association
# --------------------------------------------------

resource "aws_eks_pod_identity_association" "status_page_reviewer" {
  cluster_name = "aegis-eks-dev"

  namespace = (
    local.aegis_status_page_namespace
  )

  service_account = (
    local.aegis_status_page_service_account
  )

  role_arn = (
    aws_iam_role.status_page_reviewer.arn
  )

  depends_on = [
    aws_iam_role_policy.status_page_reviewer_dynamodb
  ]

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
    Component   = "status-page-reviewer"
  }
}
