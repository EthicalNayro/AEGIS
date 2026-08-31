# ==================================================
# AEGIS WAF Security Logging
#
# Sends blocked AWS WAF requests to CloudWatch Logs
# for security investigation and future AEGIS agents.
# ==================================================

data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

# --------------------------------------------------
# CloudWatch Log Group
#
# AWS WAF requires the destination name to begin
# with "aws-waf-logs-".
# --------------------------------------------------

resource "aws_cloudwatch_log_group" "waf" {
  name              = "aws-waf-logs-${var.project_name}-${var.environment}"
  retention_in_days = 7

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
    Component   = "waf-security-logging"
  }
}

# --------------------------------------------------
# CloudWatch Logs Resource Policy
#
# Allows the AWS log delivery service to write
# WAF security events into this specific Log Group.
# --------------------------------------------------

data "aws_iam_policy_document" "waf_log_delivery" {
  statement {
    sid    = "AWSWAFLogDelivery"
    effect = "Allow"

    principals {
      type = "Service"

      identifiers = [
        "delivery.logs.amazonaws.com"
      ]
    }

    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]

    resources = [
      "${aws_cloudwatch_log_group.waf.arn}:*"
    ]

    condition {
      test     = "ArnLike"
      variable = "aws:SourceArn"

      values = [
        "arn:aws:logs:${data.aws_region.current.region}:${data.aws_caller_identity.current.account_id}:*"
      ]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"

      values = [
        data.aws_caller_identity.current.account_id
      ]
    }
  }
}

resource "aws_cloudwatch_log_resource_policy" "waf" {
  resource_arn    = aws_cloudwatch_log_group.waf.arn
  policy_document = data.aws_iam_policy_document.waf_log_delivery.json
}

# --------------------------------------------------
# AWS WAF Logging Configuration
#
# Only BLOCK actions are retained.
# Allowed traffic is intentionally dropped from logs
# to reduce noise and CloudWatch cost.
# --------------------------------------------------

resource "aws_wafv2_web_acl_logging_configuration" "aegis" {
  resource_arn = aws_wafv2_web_acl.aegis.arn

  log_destination_configs = [
    aws_cloudwatch_log_group.waf.arn
  ]

  logging_filter {
    default_behavior = "DROP"

    filter {
      behavior = "KEEP"

      condition {
        action_condition {
          action = "BLOCK"
        }
      }

      requirement = "MEETS_ANY"
    }
  }

  depends_on = [
    aws_cloudwatch_log_resource_policy.waf
  ]
}
