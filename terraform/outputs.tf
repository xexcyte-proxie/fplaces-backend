output "alb_dns_name" {
  description = "The DNS name of the load balancer"
  value       = aws_lb.fplaces_alb.dns_name
}


output "ecr_repository_url" {
  description = "The URL of the ECR repository"
  value       = aws_ecr_repository.app_repo.repository_url
}

# The following are only populated once var.domain_name is set (see variables.tf).

output "backend_domain_validation_records" {
  description = "DNS record(s) to add manually to validate the ACM certificate, if route53_zone_id is not set (empty when Route 53 handled it automatically, or domain_name is unset)."
  value = var.domain_name != "" && var.route53_zone_id == "" ? [
    for dvo in aws_acm_certificate.backend[0].domain_validation_options : {
      name  = dvo.resource_record_name
      type  = dvo.resource_record_type
      value = dvo.resource_record_value
    }
  ] : []
}

output "backend_certificate_status" {
  description = "ACM certificate validation status, once domain_name is set."
  value       = var.domain_name != "" ? aws_acm_certificate.backend[0].status : null
}

output "backend_wss_url" {
  description = "The wss:// base URL once domain_name is set, DNS points at the ALB, and the certificate is issued."
  value       = var.domain_name != "" ? "wss://${var.domain_name}" : null
}
