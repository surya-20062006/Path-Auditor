output "alb_dns_name" {
  description = "Application Load Balancer DNS URL for API and Dashboard"
  value       = module.ecs.alb_dns_name
}

output "rds_endpoint" {
  description = "PostgreSQL RDS connection endpoint"
  value       = module.rds.endpoint
}

output "s3_audit_bucket" {
  description = "AWS S3 WORM archive bucket name"
  value       = module.s3.bucket_name
}
