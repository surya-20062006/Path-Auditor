variable "vpc_cidr" { type = string }
variable "env" { type = string }

resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "dpa-vpc-${var.env}"
  }
}

resource "aws_subnet" "public_a" {
  vpc_id                  = aws_vpc.this.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 4, 0)
  availability_zone       = "us-east-1a"
  map_public_ip_on_launch = true

  tags = { Name = "dpa-public-a-${var.env}" }
}

resource "aws_subnet" "public_b" {
  vpc_id                  = aws_vpc.this.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 4, 1)
  availability_zone       = "us-east-1b"
  map_public_ip_on_launch = true

  tags = { Name = "dpa-public-b-${var.env}" }
}

resource "aws_subnet" "private_a" {
  vpc_id            = aws_vpc.this.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 4, 2)
  availability_zone = "us-east-1a"

  tags = { Name = "dpa-private-a-${var.env}" }
}

resource "aws_subnet" "private_b" {
  vpc_id            = aws_vpc.this.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 4, 3)
  availability_zone = "us-east-1b"

  tags = { Name = "dpa-private-b-${var.env}" }
}

output "vpc_id" { value = aws_vpc.this.id }
output "public_subnet_ids" { value = [aws_subnet.public_a.id, aws_subnet.public_b.id] }
output "private_subnet_ids" { value = [aws_subnet.private_a.id, aws_subnet.private_b.id] }
