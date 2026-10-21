variable "aws_region" {
  description = "The AWS region to deploy to"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "The name of the project"
  type        = string
  default     = "fplaces"
}

# =====================================================================
# CUSTOM DOMAIN / HTTPS (optional)
# =====================================================================
# Leave domain_name empty (the default) to skip ACM/HTTPS provisioning entirely —
# every resource below that depends on it is conditional (count = 0) and the ALB
# keeps running exactly as it does today, HTTP-only. Set domain_name once you own
# a domain to point at this backend (e.g. "api.fplaces.app") to provision an ACM
# certificate and an HTTPS (443) listener on the existing ALB for wss:// support.
variable "domain_name" {
  description = "Custom domain for the backend (e.g. api.fplaces.app). Empty = no ACM/HTTPS resources are created."
  type        = string
  default     = ""
}

# Only needed if domain_name's DNS is hosted in this AWS account's Route 53. When
# set, certificate validation and the domain -> ALB record are fully automated.
# When domain_name is set but this is left empty, the ACM certificate is still
# requested, but you must add its DNS validation record yourself (see the
# backend_domain_validation_records output) at whatever registrar/DNS host you use,
# and point domain_name at the ALB's DNS name (see the alb_dns_name output) yourself.
variable "route53_zone_id" {
  description = "Route 53 hosted zone ID for domain_name, if DNS is managed in Route 53."
  type        = string
  default     = ""
}
