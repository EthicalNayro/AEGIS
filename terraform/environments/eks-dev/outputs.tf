output "vpc_id" {
  value = module.vpc_eks.vpc_id
}

output "availability_zones" {
  value = module.vpc_eks.availability_zones
}

output "public_subnet_ids" {
  value = module.vpc_eks.public_subnet_ids
}

output "eks_cluster_subnet_ids" {
  value = module.vpc_eks.eks_cluster_subnet_ids
}

output "private_eks_subnet_ids" {
  value = module.vpc_eks.private_eks_subnet_ids
}

output "private_data_subnet_ids" {
  value = module.vpc_eks.private_data_subnet_ids
}

output "nat_gateway_ids" {
  value = module.vpc_eks.nat_gateway_ids
}

output "eks_cluster_name" {
  value = module.eks.cluster_name
}

output "eks_cluster_version" {
  value = module.eks.cluster_version
}

output "eks_cluster_endpoint" {
  value = module.eks.cluster_endpoint
}

output "eks_node_group_name" {
  value = module.eks.node_group_name
}

output "karpenter_controller_role_arn" {
  description = "IAM role assumed by the Karpenter controller through EKS Pod Identity."
  value       = module.karpenter.iam_role_arn
}

output "karpenter_node_role_name" {
  description = "IAM role used by EC2 nodes provisioned by Karpenter."
  value       = module.karpenter.node_iam_role_name
}

output "karpenter_interruption_queue_name" {
  description = "SQS queue used by Karpenter for AWS interruption events."
  value       = module.karpenter.queue_name
}

output "aegis_certificate_arn" {
  description = "ACM certificate ARN for the public AEGIS endpoint."
  value       = aws_acm_certificate.aegis.arn
}

output "aegis_certificate_validation" {
  description = "DNS record required to validate the AEGIS ACM certificate."

  value = {
    for option in aws_acm_certificate.aegis.domain_validation_options :
    option.domain_name => {
      name  = option.resource_record_name
      type  = option.resource_record_type
      value = option.resource_record_value
    }
  }
}

output "aegis_cloudwatch_dashboard_name" {
  description = "CloudWatch dashboard for AEGIS security and platform observability."
  value       = aws_cloudwatch_dashboard.aegis.dashboard_name
}

output "aegis_waf_security_alarm_name" {
  description = "CloudWatch alarm monitoring elevated AWS WAF blocks."
  value       = aws_cloudwatch_metric_alarm.waf_blocked_requests_high.alarm_name
}

output "aegis_security_events_queue_url" {
  description = "SQS queue URL for AEGIS security events."
  value       = aws_sqs_queue.security_events.url
}

output "aegis_security_events_queue_arn" {
  description = "SQS queue ARN for AEGIS security events."
  value       = aws_sqs_queue.security_events.arn
}

output "aegis_security_eventbridge_rule_name" {
  description = "EventBridge rule routing AEGIS security alarms."
  value       = aws_cloudwatch_event_rule.waf_security_alarm.name
}

output "aegis_security_events_dlq_url" {
  description = "AEGIS security events dead-letter queue URL"
  value       = aws_sqs_queue.security_events_dlq.url
}

output "aegis_security_events_dlq_arn" {
  description = "AEGIS security events dead-letter queue ARN"
  value       = aws_sqs_queue.security_events_dlq.arn
}

output "aegis_security_findings_table_name" {
  description = "AEGIS security findings DynamoDB table"
  value       = aws_dynamodb_table.security_findings.name
}

output "aegis_security_findings_table_arn" {
  description = "AEGIS security findings DynamoDB table ARN"
  value       = aws_dynamodb_table.security_findings.arn
}


# ==================================================
# Status-Page Managed Runtime
# ==================================================

output "status_page_rds_endpoint" {
  description = "Private PostgreSQL endpoint for Status-Page."
  value       = aws_db_instance.status_page.address
}

output "status_page_rds_port" {
  description = "PostgreSQL port."
  value       = aws_db_instance.status_page.port
}

output "status_page_rds_database_name" {
  description = "Status-Page PostgreSQL database name."
  value       = aws_db_instance.status_page.db_name
}

output "status_page_rds_master_secret_arn" {
  description = "AWS-managed Secrets Manager secret containing the RDS master credentials."
  value       = try(aws_db_instance.status_page.master_user_secret[0].secret_arn, null)
}

output "status_page_redis_primary_endpoint" {
  description = "Primary Redis endpoint."
  value       = aws_elasticache_replication_group.status_page.primary_endpoint_address
}

output "status_page_redis_reader_endpoint" {
  description = "Redis reader endpoint."
  value       = aws_elasticache_replication_group.status_page.reader_endpoint_address
}

output "status_page_redis_port" {
  description = "Redis port."
  value       = aws_elasticache_replication_group.status_page.port
}

output "status_page_ecr_repository_url" {
  description = "ECR repository used for the Status-Page container."
  value       = aws_ecr_repository.status_page.repository_url
}
