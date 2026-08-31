# ==================================================
# AWS WAFv2
#
# Protects the public AEGIS Application Load Balancer
# before requests reach the Kubernetes workloads.
# ==================================================

data "aws_lb" "aegis" {
  name = "aegis-eks-dev-alb"
}

resource "aws_wafv2_web_acl" "aegis" {
  name        = "${var.project_name}-${var.environment}-web-acl"
  description = "AWS WAF protection for the public AEGIS endpoint."
  scope       = "REGIONAL"

  default_action {
    allow {}
  }

  # ------------------------------------------------
  # AWS Core Rule Set
  #
  # Baseline protection against common web attacks
  # such as XSS, LFI and other malformed requests.
  # ------------------------------------------------

  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 10

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "aegis-common-rule-set"
      sampled_requests_enabled   = true
    }
  }

  # ------------------------------------------------
  # Known Bad Inputs
  #
  # Blocks request patterns associated with known
  # vulnerabilities and exploit payloads.
  # ------------------------------------------------

  rule {
    name     = "AWSManagedRulesKnownBadInputsRuleSet"
    priority = 20

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesKnownBadInputsRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "aegis-known-bad-inputs"
      sampled_requests_enabled   = true
    }
  }

  # ------------------------------------------------
  # Amazon IP Reputation List
  #
  # Blocks requests originating from IP addresses
  # with poor reputation according to AWS threat data.
  # ------------------------------------------------

  rule {
    name     = "AWSManagedRulesAmazonIpReputationList"
    priority = 30

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesAmazonIpReputationList"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "aegis-ip-reputation"
      sampled_requests_enabled   = true
    }
  }

  # ------------------------------------------------
  # Per-IP Rate Limiting
  #
  # Blocks clients that exceed 100 requests during
  # a rolling 60-second evaluation window.
  #
  # Each source IP is tracked independently.
  # ------------------------------------------------

  rule {
    name     = "RateLimitPerIP"
    priority = 40

    action {
      block {}
    }

    statement {
      rate_based_statement {
        limit                 = 20
        aggregate_key_type    = "IP"
        evaluation_window_sec = 60
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "aegis-rate-limit-per-ip"
      sampled_requests_enabled   = true
    }
  }

  # ------------------------------------------------
  # Web ACL Observability
  #
  # Exposes CloudWatch metrics and sampled requests
  # for the complete AEGIS Web ACL.
  # ------------------------------------------------

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "aegis-web-acl"
    sampled_requests_enabled   = true
  }

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
    Component   = "waf"
  }
}

# ==================================================
# Associate WAF with the AEGIS ALB
# ==================================================

resource "aws_wafv2_web_acl_association" "aegis_alb" {
  resource_arn = data.aws_lb.aegis.arn
  web_acl_arn  = aws_wafv2_web_acl.aegis.arn
}
