terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.40"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "DecisionPathAuditor"
      Environment = var.environment
      ManagedBy   = "Terraform"
      Compliance  = "Enterprise-AIGov"
    }
  }
}

module "vpc" {
  source   = "./modules/vpc"
  vpc_cidr = var.vpc_cidr
  env      = var.environment
}

module "s3" {
  source      = "./modules/s3"
  bucket_name = "dpa-enterprise-audit-traces-${var.environment}"
  env         = var.environment
}

module "rds" {
  source             = "./modules/rds"
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  db_password        = var.db_password
  env                = var.environment
}

module "ecs" {
  source          = "./modules/ecs"
  vpc_id          = module.vpc.vpc_id
  public_subnets  = module.vpc.public_subnet_ids
  private_subnets = module.vpc.private_subnet_ids
  db_endpoint     = module.rds.endpoint
  s3_bucket_name  = module.s3.bucket_name
  env             = var.environment
}
