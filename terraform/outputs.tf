output "api_gateway_url" {
  description = "The public URL of the API Gateway"
  value       = aws_apigatewayv2_api.http_api.api_endpoint
}

output "s3_bucket_name" {
  description = "The name of the S3 bucket used for media"
  value       = aws_s3_bucket.media_bucket.bucket
}

output "db_endpoint" {
  description = "The connection endpoint for the RDS PostgreSQL database"
  value       = aws_db_instance.postgres.endpoint
}
