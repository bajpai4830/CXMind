# Deployment - Cloud Infrastructure & DevOps

## Overview
Infrastructure as Code and deployment configurations for cloud deployment.

## Components
- Containerization (Docker)
- Kubernetes orchestration
- CI/CD pipelines
- Infrastructure templates (Terraform/CloudFormation)
- Monitoring and logging

## Supported Platforms
- AWS
- Azure
- GCP

## Tech Stack (To Be Defined)
- Docker for containerization
- Kubernetes for orchestration
- Terraform for IaC
- GitHub Actions / GitLab CI for CI/CD

## Coming Soon

## Docker Compose (Local / Demo)
From the repo root:
```powershell
docker compose up --build
```

Services:
- Frontend (Nginx): `http://localhost:5173`
- Backend (FastAPI): `http://localhost:8000/docs`
- Database (Postgres): `localhost:5432` (user/pass: `postgres`/`postgres`, db: `cxmind`)

## Next
- Kubernetes manifests
- Terraform configurations
- CI/CD workflows
