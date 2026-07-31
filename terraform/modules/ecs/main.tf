variable "vpc_id" { type = string }
variable "public_subnets" { type = list(string) }
variable "private_subnets" { type = list(string) }
variable "db_endpoint" { type = string }
variable "s3_bucket_name" { type = string }
variable "env" { type = string }

resource "aws_ecs_cluster" "main" {
  name = "dpa-cluster-${var.env}"
}

resource "aws_security_group" "alb_sg" {
  name        = "dpa-alb-sg-${var.env}"
  description = "Allow inbound HTTP/HTTPS from internet"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 80
    to_port     = 80
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

resource "aws_lb" "api_alb" {
  name               = "dpa-api-alb-${var.env}"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_sg.id]
  subnets            = var.public_subnets
}

output "alb_dns_name" { value = aws_lb.api_alb.dns_name }
