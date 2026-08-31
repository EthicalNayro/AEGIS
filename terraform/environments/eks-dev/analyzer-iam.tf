data "aws_iam_policy_document" "security_analyzer_assume_role" {
  statement {
    sid    = "AllowEKSAnalyzerPodIdentity"
    effect = "Allow"

    principals {
      type = "Service"

      identifiers = [
        "pods.eks.amazonaws.com"
      ]
    }

    actions = [
      "sts:AssumeRole",
      "sts:TagSession"
    ]

    condition {
      test     = "StringEquals"
      variable = "aws:RequestTag/kubernetes-namespace"

      values = [
        "aegis-system"
      ]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:RequestTag/kubernetes-service-account"

      values = [
        "aegis-security-analyzer"
      ]
    }
  }
}


resource "aws_iam_role" "security_analyzer" {
  name = "${var.project_name}-${var.environment}-security-analyzer"

  assume_role_policy = data.aws_iam_policy_document.security_analyzer_assume_role.json

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
    Component   = "security-analyzer"
  }
}


resource "aws_iam_role_policy" "security_analyzer_sqs" {
  name = "AEGISSecurityAnalyzerSQS"
  role = aws_iam_role.security_analyzer.id

  policy = jsonencode({
    Version = "2012-10-17"

    Statement = [

      # --------------------------------------------------
      # Consume security events from the AEGIS SQS queue.
      # --------------------------------------------------
      {
        Sid    = "ConsumeAEGISSecurityEvents"
        Effect = "Allow"

        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:ChangeMessageVisibility",
          "sqs:GetQueueAttributes"
        ]

        Resource = aws_sqs_queue.security_events.arn
      },

      # --------------------------------------------------
      # Enrich incidents using AEGIS WAF security logs.
      # --------------------------------------------------
      {
        Sid    = "ReadAEGISWAFSecurityLogs"
        Effect = "Allow"

        Action = [
          "logs:FilterLogEvents"
        ]

        Resource = "arn:aws:logs:us-east-1:992382545251:log-group:aws-waf-logs-aegis-eks-dev:*"
      },

      # --------------------------------------------------
      # Analyze enriched findings with Amazon Bedrock.
      #
      # Least privilege:
      # Analyzer can invoke only Amazon Nova Pro.
      # --------------------------------------------------
      {
        Sid    = "InvokeAEGISBedrockSecurityModel"
        Effect = "Allow"

        Action = [
          "bedrock:InvokeModel"
        ]

        Resource = [
          "arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-pro-v1:0"
        ]
      },

      # --------------------------------------------------
      # Persist AI security findings in DynamoDB.
      #
      # Used for:
      # - durable incident storage
      # - idempotency checks
      # - future human feedback loop
      #
      # Least privilege:
      # Analyzer can access only the AEGIS findings table.
      # --------------------------------------------------
      {
        Sid    = "StoreAEGISSecurityFindings"
        Effect = "Allow"

        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem"
        ]

        Resource = aws_dynamodb_table.security_findings.arn
      }

    ]
  })
}


resource "aws_eks_pod_identity_association" "security_analyzer" {
  cluster_name = "${var.project_name}-${var.environment}"
  namespace    = "aegis-system"

  service_account = "aegis-security-analyzer"

  role_arn = aws_iam_role.security_analyzer.arn

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
    Component   = "security-analyzer"
  }
}
