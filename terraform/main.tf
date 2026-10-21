terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

provider "aws" {
  region  = var.aws_region
  profile = "fplaces"
}

resource "random_id" "suffix" {
  byte_length = 4
}

# =====================================================================
# ENV CONFIGURATION PARSING
# =====================================================================
locals {
  # Parse the .env file located one directory up (in the project root)
  env_file = file("${path.module}/../.env")

  # Use regex to extract all KEY=VALUE pairs (ignoring comments and empty lines)
  env_vars = {
    for tuple in regexall("(?m)^\\s*([^#\\s=]+)\\s*=\\s*(.*)$", local.env_file) :
    tuple[0] => tuple[1]
  }

  # Convert into the map format required by ECS task definition
  ecs_environment = [
    for k, v in local.env_vars : {
      name  = k
      value = v
    }
  ]
}

# =====================================================================
# ECR REPOSITORY
# =====================================================================
resource "aws_ecr_repository" "app_repo" {
  name                 = "${var.project_name}-repo"
  image_tag_mutability = "MUTABLE"
  force_delete         = true
}

# =====================================================================
# NETWORKING (Using Default VPC)
# =====================================================================
data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

resource "aws_security_group" "alb_sg" {
  name        = "${var.project_name}-alb-sg"
  description = "Security group for ALB"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Open regardless of whether domain_name is set yet, so applying the HTTPS
  # listener later never requires a second security-group change.
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "ecs_tasks_sg" {
  name        = "${var.project_name}-ecs-tasks-sg"
  description = "Security group for ECS tasks"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    from_port       = 8080
    to_port         = 8080
    protocol        = "tcp"
    security_groups = [aws_security_group.alb_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# =====================================================================
# LOAD BALANCER
# =====================================================================
resource "aws_lb" "fplaces_alb" {
  name               = "${var.project_name}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_sg.id]
  subnets            = data.aws_subnets.default.ids
}

resource "aws_lb_target_group" "fplaces_tg" {
  name        = "${var.project_name}-tg"
  port        = 8080
  protocol    = "HTTP"
  vpc_id      = data.aws_vpc.default.id
  target_type = "ip"

  health_check {
    path                = "/"
    matcher             = "200-499"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 2
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.fplaces_alb.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.fplaces_tg.arn
  }
}

# =====================================================================
# HTTPS / ACM CERTIFICATE (only provisioned once var.domain_name is set)
# =====================================================================
# DNS-validated: ACM never sees your domain's actual DNS credentials, it just
# needs a CNAME record to exist proving you control the domain. Must live in
# the same region as the ALB (var.aws_region) — unlike CloudFront, which always
# requires us-east-1 regardless of the distribution's region.
resource "aws_acm_certificate" "backend" {
  count             = var.domain_name != "" ? 1 : 0
  domain_name       = var.domain_name
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }
}

# Auto-creates the validation CNAME only when DNS is hosted in this account's
# Route 53 (route53_zone_id set). Otherwise, add the record yourself using the
# backend_domain_validation_records output.
resource "aws_route53_record" "backend_cert_validation" {
  for_each = var.domain_name != "" && var.route53_zone_id != "" ? {
    for dvo in aws_acm_certificate.backend[0].domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  } : {}

  zone_id         = var.route53_zone_id
  name            = each.value.name
  type            = each.value.type
  records         = [each.value.record]
  ttl             = 60
  allow_overwrite = true
}

# Blocks until ACM confirms the validation record above is visible and issues
# the certificate. Only runs when Route 53 created that record automatically;
# with an external DNS host, the certificate is requested but stays
# PENDING_VALIDATION until you add the record yourself and ACM notices it
# (independent of this Terraform run).
resource "aws_acm_certificate_validation" "backend" {
  count                   = var.domain_name != "" && var.route53_zone_id != "" ? 1 : 0
  certificate_arn         = aws_acm_certificate.backend[0].arn
  validation_record_fqdns = [for r in aws_route53_record.backend_cert_validation : r.fqdn]
}

locals {
  # Prefer the validated cert's ARN (Route 53 path); fall back to the raw
  # (possibly still-pending) cert ARN for the manual-DNS path, since the
  # listener can reference it before validation completes.
  backend_certificate_arn = var.domain_name == "" ? "" : (
    var.route53_zone_id != "" ? aws_acm_certificate_validation.backend[0].certificate_arn : aws_acm_certificate.backend[0].arn
  )
}

resource "aws_lb_listener" "https" {
  count             = var.domain_name != "" ? 1 : 0
  load_balancer_arn = aws_lb.fplaces_alb.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-Res-PQ-2025-09"
  certificate_arn   = local.backend_certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.fplaces_tg.arn
  }
}

# Points domain_name at the ALB. Only when Route 53 hosts the domain's DNS —
# with an external host, create this (a CNAME/ALIAS to alb_dns_name) yourself.
resource "aws_route53_record" "backend_alias" {
  count   = var.domain_name != "" && var.route53_zone_id != "" ? 1 : 0
  zone_id = var.route53_zone_id
  name    = var.domain_name
  type    = "A"

  alias {
    name                   = aws_lb.fplaces_alb.dns_name
    zone_id                = aws_lb.fplaces_alb.zone_id
    evaluate_target_health = true
  }
}

# =====================================================================
# IAM ROLES FOR ECS
# =====================================================================
# Task Execution Role (allows ECS to pull images and read env file from S3)
resource "aws_iam_role" "ecs_task_execution_role" {
  name = "${var.project_name}-ecs-execution-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Task Role (allows your application code to interact with AWS APIs like S3 for media)
resource "aws_iam_role" "ecs_task_role" {
  name = "${var.project_name}-ecs-task-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
    }]
  })
}

# =====================================================================
# ECS CLUSTER AND FARGATE SERVICE
# =====================================================================
resource "aws_ecs_cluster" "fplaces_cluster" {
  name = "${var.project_name}-cluster"
}

resource "aws_cloudwatch_log_group" "ecs_log_group" {
  name              = "/ecs/${var.project_name}-app"
  retention_in_days = 7
}

resource "aws_ecs_task_definition" "app" {
  family                   = "${var.project_name}-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "${var.project_name}-container"
      image     = aws_ecr_repository.app_repo.repository_url # We'll start with empty or manual push first
      cpu       = 256
      memory    = 512
      essential = true
      portMappings = [
        {
          containerPort = 8080
          hostPort      = 8080
        }
      ]
      environment = local.ecs_environment
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs_log_group.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])
}

resource "aws_ecs_service" "app_service" {
  name            = "${var.project_name}-service"
  cluster         = aws_ecs_cluster.fplaces_cluster.id
  task_definition = aws_ecs_task_definition.app.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = data.aws_subnets.default.ids
    security_groups  = [aws_security_group.ecs_tasks_sg.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.fplaces_tg.arn
    container_name   = "${var.project_name}-container"
    container_port   = 8080
  }

  depends_on = [
    aws_lb_listener.http
  ]
}
