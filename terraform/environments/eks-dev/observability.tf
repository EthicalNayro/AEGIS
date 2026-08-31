# ==================================================
# AEGIS Observability
#
# CloudWatch dashboard and alarms for:
# - AWS WAF security activity
# - Public ALB health and traffic
# - Security incident signals
# - AI decision quality
# - Human feedback quality
# ==================================================

locals {
  # Application Load Balancer CloudWatch dimension.
  #
  # CloudWatch expects:
  # app/<load-balancer-name>/<id>
  aegis_alb_dimension = data.aws_lb.aegis.arn_suffix

  # Actual AWS WAF CloudWatch WebACL dimension.
  #
  # Verified against live AWS/WAFV2 metrics.
  aegis_waf_web_acl_dimension = "aegis-eks-dev-web-acl"

  # Rule metric names configured in waf.tf.
  aegis_rate_limit_metric_name = "aegis-rate-limit-per-ip"
}


# ==================================================
# CloudWatch Dashboard
# ==================================================

resource "aws_cloudwatch_dashboard" "aegis" {
  dashboard_name = "${var.project_name}-${var.environment}-security-observability"

  dashboard_body = jsonencode({
    widgets = [

      # ------------------------------------------------
      # Dashboard Header
      # ------------------------------------------------

      {
        type   = "text"
        x      = 0
        y      = 0
        width  = 24
        height = 2

        properties = {
          markdown = <<-EOT
            # AEGIS Security & Platform Observability

            **Environment:** `${var.environment}` | **Region:** `us-east-1`

            Security visibility across **AWS WAF → ALB → EKS → AI Security Analysis**.
          EOT
        }
      },


      # ------------------------------------------------
      # WAF - Allowed vs Blocked
      # ------------------------------------------------

      {
        type   = "metric"
        x      = 0
        y      = 2
        width  = 12
        height = 6

        properties = {
          title   = "AWS WAF - Allowed vs Blocked Requests"
          region  = "us-east-1"
          view    = "timeSeries"
          stacked = false
          period  = 60
          stat    = "Sum"

          metrics = [
            [
              "AWS/WAFV2",
              "AllowedRequests",
              "WebACL",
              local.aegis_waf_web_acl_dimension,
              "Rule",
              "Default_Action",
              "Region",
              "us-east-1",
              {
                label = "Allowed Requests"
              }
            ],
            [
              "AWS/WAFV2",
              "BlockedRequests",
              "WebACL",
              local.aegis_waf_web_acl_dimension,
              "Rule",
              "ALL",
              "Region",
              "us-east-1",
              {
                label = "Blocked Requests"
              }
            ]
          ]
        }
      },


      # ------------------------------------------------
      # WAF - Rate Limiting
      # ------------------------------------------------

      {
        type   = "metric"
        x      = 12
        y      = 2
        width  = 12
        height = 6

        properties = {
          title   = "AWS WAF - Rate Limit Blocks"
          region  = "us-east-1"
          view    = "timeSeries"
          stacked = false
          period  = 60
          stat    = "Sum"

          metrics = [
            [
              "AWS/WAFV2",
              "BlockedRequests",
              "WebACL",
              local.aegis_waf_web_acl_dimension,
              "Rule",
              local.aegis_rate_limit_metric_name,
              "Region",
              "us-east-1",
              {
                label = "RateLimitPerIP Blocks"
              }
            ]
          ]
        }
      },


      # ------------------------------------------------
      # ALB - Request Volume
      # ------------------------------------------------

      {
        type   = "metric"
        x      = 0
        y      = 8
        width  = 8
        height = 6

        properties = {
          title  = "ALB - Request Volume"
          region = "us-east-1"
          view   = "timeSeries"
          period = 60
          stat   = "Sum"

          metrics = [
            [
              "AWS/ApplicationELB",
              "RequestCount",
              "LoadBalancer",
              local.aegis_alb_dimension,
              {
                label = "Requests"
              }
            ]
          ]
        }
      },


      # ------------------------------------------------
      # ALB - HTTP Errors
      # ------------------------------------------------

      {
        type   = "metric"
        x      = 8
        y      = 8
        width  = 8
        height = 6

        properties = {
          title   = "ALB - HTTP Errors"
          region  = "us-east-1"
          view    = "timeSeries"
          stacked = false
          period  = 60
          stat    = "Sum"

          metrics = [
            [
              "AWS/ApplicationELB",
              "HTTPCode_ELB_4XX_Count",
              "LoadBalancer",
              local.aegis_alb_dimension,
              {
                label = "ALB 4XX"
              }
            ],
            [
              "AWS/ApplicationELB",
              "HTTPCode_ELB_5XX_Count",
              "LoadBalancer",
              local.aegis_alb_dimension,
              {
                label = "ALB 5XX"
              }
            ]
          ]
        }
      },


      # ------------------------------------------------
      # ALB - Target Response Time
      # ------------------------------------------------

      {
        type   = "metric"
        x      = 16
        y      = 8
        width  = 8
        height = 6

        properties = {
          title  = "ALB - Target Response Time"
          region = "us-east-1"
          view   = "timeSeries"
          period = 60

          metrics = [
            [
              "AWS/ApplicationELB",
              "TargetResponseTime",
              "LoadBalancer",
              local.aegis_alb_dimension,
              {
                stat  = "Average"
                label = "Average"
              }
            ],
            [
              "AWS/ApplicationELB",
              "TargetResponseTime",
              "LoadBalancer",
              local.aegis_alb_dimension,
              {
                stat  = "p95"
                label = "p95"
              }
            ]
          ]

          yAxis = {
            left = {
              min   = 0
              label = "Seconds"
            }
          }
        }
      },


      # ==================================================
      # AEGIS AI Observability
      # ==================================================

      {
        type   = "text"
        x      = 0
        y      = 14
        width  = 24
        height = 2

        properties = {
          markdown = <<-EOT
            ## AEGIS AI Decision Quality & Human Feedback

            Bedrock security classification quality measured against **verified human analyst feedback**.
          EOT
        }
      },


      # ------------------------------------------------
      # AI - Accuracy vs Error Rate
      # ------------------------------------------------

      {
        type   = "metric"
        x      = 0
        y      = 16
        width  = 12
        height = 6

        properties = {
          title   = "AEGIS AI Decision Quality"
          region  = "us-east-1"
          view    = "timeSeries"
          stacked = false
          period  = 300
          stat    = "Average"

          metrics = [
            [
              "AEGIS/AIQuality",
              "AccuracyPercent",
              "System",
              "AEGIS",
              "Environment",
              "eks-dev",
              {
                label = "AI Accuracy %"
              }
            ],
            [
              "AEGIS/AIQuality",
              "ErrorRatePercent",
              "System",
              "AEGIS",
              "Environment",
              "eks-dev",
              {
                label = "AI Error Rate %"
              }
            ]
          ]

          yAxis = {
            left = {
              min   = 0
              max   = 100
              label = "Percent"
            }
          }
        }
      },


      # ------------------------------------------------
      # AI - Human Feedback
      # ------------------------------------------------

      {
        type   = "metric"
        x      = 12
        y      = 16
        width  = 12
        height = 6

        properties = {
          title   = "AEGIS Human Feedback"
          region  = "us-east-1"
          view    = "timeSeries"
          stacked = false
          period  = 300
          stat    = "Maximum"

          metrics = [
            [
              "AEGIS/AIQuality",
              "ReviewedFindings",
              "System",
              "AEGIS",
              "Environment",
              "eks-dev",
              {
                label = "Reviewed Findings"
              }
            ],
            [
              "AEGIS/AIQuality",
              "CorrectFindings",
              "System",
              "AEGIS",
              "Environment",
              "eks-dev",
              {
                label = "AI Correct"
              }
            ],
            [
              "AEGIS/AIQuality",
              "IncorrectFindings",
              "System",
              "AEGIS",
              "Environment",
              "eks-dev",
              {
                label = "AI Incorrect"
              }
            ],
            [
              "AEGIS/AIQuality",
              "PendingReview",
              "System",
              "AEGIS",
              "Environment",
              "eks-dev",
              {
                label = "Pending Review"
              }
            ]
          ]

          yAxis = {
            left = {
              min   = 0
              label = "Findings"
            }
          }
        }
      }
    ]
  })
}


# ==================================================
# Security Alarm
#
# Raises an alarm when AWS WAF blocks at least
# 5 requests within a 1-minute evaluation period.
#
# This intentionally uses a sensitive threshold
# for the AEGIS development/demo environment.
# ==================================================

resource "aws_cloudwatch_metric_alarm" "waf_blocked_requests_high" {
  alarm_name        = "${var.project_name}-${var.environment}-waf-blocked-requests-high"
  alarm_description = "AEGIS security signal: AWS WAF blocked at least 5 requests within 1 minute."

  comparison_operator = "GreaterThanOrEqualToThreshold"

  evaluation_periods = 1
  threshold          = 5

  namespace   = "AWS/WAFV2"
  metric_name = "BlockedRequests"

  period    = 60
  statistic = "Sum"

  dimensions = {
    WebACL = local.aegis_waf_web_acl_dimension
    Rule   = "ALL"
    Region = "us-east-1"
  }

  # Quiet periods with no WAF blocks should remain healthy.
  treat_missing_data = "notBreaching"

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
    Component   = "security-monitoring"
  }
}
