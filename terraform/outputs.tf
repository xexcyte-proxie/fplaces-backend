output "alb_dns_name" {
  description = "The DNS name of the load balancer"
  value       = aws_lb.fplaces_alb.dns_name
}


output "ecr_repository_url" {
  description = "The URL of the ECR repository"
  value       = aws_ecr_repository.app_repo.repository_url
}

