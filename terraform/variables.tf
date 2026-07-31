variable "aws_region" {
  type        = string
  default     = "us-east-1"
  description = "AWS deployment region"
}

variable "environment" {
  type        = string
  default     = "production"
  description = "Deployment environment name"
}

variable "vpc_cidr" {
  type        = string
  default     = "10.20.0.0/16"
  description = "VPC IPv4 CIDR block"
}

variable "db_password" {
  type        = string
  sensitive   = true
  default     = "enterprise_secure_pg_password_2026!"
  description = "PostgreSQL root administrator password"
}
