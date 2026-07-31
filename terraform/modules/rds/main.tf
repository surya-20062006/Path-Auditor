variable "vpc_id" { type = string }
variable "private_subnet_ids" { type = list(string) }
variable "db_password" { type = string }
variable "env" { type = string }

resource "aws_db_subnet_group" "pg_subnet_group" {
  name       = "dpa-rds-subnet-group-${var.env}"
  subnet_ids = var.private_subnet_ids
}

resource "aws_security_group" "rds_sg" {
  name        = "dpa-rds-sg-${var.env}"
  description = "Allow inbound postgres traffic from private subnets"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["10.20.0.0/16"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_db_instance" "postgres" {
  identifier              = "dpa-postgres-${var.env}"
  engine                  = "postgres"
  engine_version          = "15.5"
  instance_class          = "db.t3.medium"
  allocated_storage       = 50
  max_allocated_storage   = 200
  storage_type            = "gp3"
  storage_encrypted       = true
  db_name                 = "decision_path_auditor"
  username                = "admin"
  password                = var.db_password
  db_subnet_group_name    = aws_db_subnet_group.pg_subnet_group.name
  vpc_security_group_ids  = [aws_security_group.rds_sg.id]
  multi_az                = true
  skip_final_snapshot     = true
  backup_retention_period = 7
}

output "endpoint" { value = aws_db_instance.postgres.endpoint }
