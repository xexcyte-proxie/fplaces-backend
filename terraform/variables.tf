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

variable "db_username" {
  description = "Database administrator username"
  type        = string
  default     = "fplaces_user"
}

variable "db_password" {
  description = "Database administrator password"
  type        = string
  sensitive   = true
}

variable "django_secret_key" {
  description = "Django Secret Key"
  type        = string
  sensitive   = true
}
