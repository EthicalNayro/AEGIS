# ==================================================
# AEGIS Security Event Pipeline
#
# CloudWatch Alarm
#        ↓
# EventBridge
#        ↓
# SQS Security Events Queue
#
# The queue will later be consumed by the
# AEGIS security analysis / Bedrock agent layer.
# ==================================================

# ==================================================
# SQS Security Events Queue
# ==================================================

resource "aws_sqs_queue" "security_events_dlq" {
  name = "${var.project_name}-${var.environment}-security-events-dlq"

  # Failed security events are important forensic evidence.
  message_retention_seconds = 1209600 # 14 days

  sqs_managed_sse_enabled = true

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
    Component   = "security-event-pipeline"
    Purpose     = "dead-letter-queue"
  }
}

resource "aws_sqs_queue" "security_events" {
  name = "${var.project_name}-${var.environment}-security-events"

  message_retention_seconds  = 345600 # 4 days
  visibility_timeout_seconds = 60

  sqs_managed_sse_enabled = true

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.security_events_dlq.arn
    maxReceiveCount     = 3
  })

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
    Component   = "security-event-pipeline"
  }
}

# ==================================================
# EventBridge Rule
#
# Matches ONLY:
# - CloudWatch Alarm state changes
# - the AEGIS WAF security alarm
# - transitions into ALARM
# ==================================================

resource "aws_cloudwatch_event_rule" "waf_security_alarm" {
  name        = "${var.project_name}-${var.environment}-waf-alarm-to-security-events"
  description = "Routes AEGIS WAF security alarms into the security event pipeline."

  event_pattern = jsonencode({
    source = [
      "aws.cloudwatch"
    ]

    detail-type = [
      "CloudWatch Alarm State Change"
    ]

    resources = [
      aws_cloudwatch_metric_alarm.waf_blocked_requests_high.arn
    ]

    detail = {
      state = {
        value = [
          "ALARM"
        ]
      }
    }
  })

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
    Component   = "security-event-pipeline"
  }
}

# ==================================================
# EventBridge → SQS Target
# ==================================================

resource "aws_cloudwatch_event_target" "security_events" {
  rule      = aws_cloudwatch_event_rule.waf_security_alarm.name
  target_id = "AEGISSecurityEventsQueue"

  arn = aws_sqs_queue.security_events.arn
}

# ==================================================
# SQS Resource Policy
#
# Only the specific AEGIS EventBridge rule may send
# messages into this queue.
# ==================================================

data "aws_iam_policy_document" "security_events_queue" {

  # --------------------------------------------------
  # EventBridge may publish security events.
  # --------------------------------------------------

  statement {
    sid    = "AllowAEGISEventBridge"
    effect = "Allow"

    principals {
      type = "Service"

      identifiers = [
        "events.amazonaws.com"
      ]
    }

    actions = [
      "sqs:SendMessage"
    ]

    resources = [
      aws_sqs_queue.security_events.arn
    ]

    condition {
      test     = "ArnEquals"
      variable = "aws:SourceArn"

      values = [
        aws_cloudwatch_event_rule.waf_security_alarm.arn
      ]
    }
  }

  # --------------------------------------------------
  # TEMPORARY DEV VALIDATION ACCESS
  #
  # Allows the AEGIS deployment role to verify that
  # EventBridge events reached the queue.
  #
  # No DeleteMessage permission is intentionally given.
  # --------------------------------------------------

  statement {
    sid    = "AllowAEGISDeploymentRoleReadForValidation"
    effect = "Allow"

    principals {
      type = "AWS"

      identifiers = [
        "arn:aws:iam::992382545251:role/aegis-project-role"
      ]
    }

    actions = [
      "sqs:ReceiveMessage",
      "sqs:GetQueueAttributes"
    ]

    resources = [
      aws_sqs_queue.security_events.arn
    ]
  }
}

resource "aws_sqs_queue_policy" "security_events" {
  queue_url = aws_sqs_queue.security_events.id
  policy    = data.aws_iam_policy_document.security_events_queue.json
}
