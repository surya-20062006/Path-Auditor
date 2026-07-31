# Decision Path Auditor — Enterprise Deployment Guide

## 1. Option A: Single-Host Production Docker Compose Stack
For on-premise deployments or dedicated staging servers, use the multi-container Docker Compose setup.

### Step-by-Step Deployment
```bash
# 1. Clone repository
git clone https://github.com/enterprise/decision-path-auditor.git
cd decision-path-auditor

# 2. Configure production environment variables
cp .env.example .env
# Edit .env with secure JWT secret keys and database passwords

# 3. Build and deploy all 7 services in detached mode
docker-compose up --build -d

# 4. Verify container health status
docker-compose ps
```

### Accessing Deployed Services
- **FastAPI Backend Server**: `http://localhost:8000` (Healthcheck: `/api/v1/health`)
- **Next.js Enterprise Dashboard**: `http://localhost:3000`
- **Prometheus Metrics Scraper**: `http://localhost:9090`
- **Grafana Observability UI**: `http://localhost:3001` (login: `admin` / `admin`)
- **PostgreSQL Database**: Port `5432`
- **Redis Cache & Broker**: Port `6379`

---

## 2. Option B: AWS Cloud Deployment (Terraform IaC + ECS Fargate)
For high-availability enterprise production deployments, use the provided Terraform infrastructure modules.

### Prerequisites
- AWS CLI configured with administrator permissions.
- Terraform `>= 1.5.0` installed.
- Amazon ECR repository `dpa-backend` created.

### Step-by-Step AWS Provisioning
```bash
# 1. Navigate to Terraform directory
cd terraform

# 2. Initialize Terraform providers and backend
terraform init

# 3. Review infrastructure execution plan
terraform plan -out=tfplan -var="environment=production"

# 4. Apply Terraform infrastructure changes
terraform apply tfplan
```

### Provisioned AWS Resources
1. **AWS VPC**: Highly available 2-AZ network with public and private subnets, NAT Gateway, and IGW.
2. **AWS ECS Fargate**: Auto-scaled container tasks running behind an Application Load Balancer (`ALB`).
3. **AWS RDS PostgreSQL**: Multi-AZ `db.t3.medium` relational database with automated backups and encryption at rest.
4. **AWS S3 Audit Bucket**: WORM-compliant bucket with versioning and AES-256 server-side encryption for immutable trace archives.
5. **AWS Secrets Manager**: Secure management of database credentials, JWT secrets, and PII encryption keys.
