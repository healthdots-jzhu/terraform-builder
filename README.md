# Terraform Builder

Interactive Python CLI wizard that generates production-ready **Terraform scripts** and **GitHub Actions workflows** for AWS infrastructure — modeled after the [HealthDots Portfolio](https://github.com/healthdots-jzhu/portfolio) platform architecture.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Usage](#usage)
  - [Interactive Wizard (`init`)](#interactive-wizard-init)
  - [Regenerate from Config (`generate`)](#regenerate-from-config-generate)
  - [List Services (`list-services`)](#list-services-list-services)
- [Configuration Model](#configuration-model)
  - [Project Basics](#project-basics)
  - [Backend Framework](#backend-framework)
  - [Frontend (Optional)](#frontend-optional)
  - [AWS Service Toggles](#aws-service-toggles)
  - [Sub-Configurations](#sub-configurations)
  - [Dependency Resolution](#dependency-resolution)
- [Generated Output Structure](#generated-output-structure)
- [Template Reference](#template-reference)
  - [Terraform Templates](#terraform-templates)
  - [Workflow Templates](#workflow-templates)
  - [Dockerfile Templates](#dockerfile-templates)
  - [Miscellaneous Templates](#miscellaneous-templates)
- [Architecture](#architecture)
- [Examples](#examples)
  - [Example 1: Full-Stack .NET with All Services](#example-1-full-stack-net-with-all-services)
  - [Example 2: Minimal Python API](#example-2-minimal-python-api)
  - [Example 3: Go Microservice (No Frontend)](#example-3-go-microservice-no-frontend)
  - [Example 4: Node.js with Frontend](#example-4-nodejs-with-frontend)
- [Development](#development)
  - [Project Setup](#project-setup)
  - [Running Tests](#running-tests)
  - [Adding a New Template](#adding-a-new-template)
  - [Adding a New Service Toggle](#adding-a-new-service-toggle)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Overview

Terraform Builder solves the problem of scaffolding AWS infrastructure from scratch. Instead of copy-pasting Terraform files and GitHub Actions workflows between projects, you answer a series of questions and get a complete, working infrastructure codebase.

**What it generates:**
- **Terraform HCL** files with conditionally included AWS resources
- **GitHub Actions workflows** for CI/CD (OIDC auth, Docker build, deploy, destroy/recreate)
- **Bootstrap Terraform** modules for one-time CI role and GitHub secrets setup
- **Framework-specific Dockerfiles** (.NET, Node.js, Python, Go)
- **Project scaffolding** (README, .gitignore, .env.example, docker-compose.yml)

**Key features:**
- 15 toggleable AWS services with automatic dependency resolution
- 4 backend framework choices with tailored Dockerfiles
- Optional frontend with S3 + CloudFront
- Multi-environment support (staging, beta, prod — or custom)
- YAML config export/import for reproducibility
- 67 automated tests covering models, validators, and template rendering

---

## Quick Start

```powershell
# Clone and install
git clone https://github.com/healthdots-jzhu/terraform-builder.git
Set-Location terraform-builder
pip install -e ".[dev]"

# Run the interactive wizard
terraform-builder init

# Or generate from saved config
terraform-builder generate -c terraform-builder.yaml
```

---

## Installation

### Prerequisites

- Python 3.10 or higher
- pip (bundled with Python)

### Install

```powershell
# From the project root
pip install -e .

# With development dependencies (pytest, coverage)
pip install -e ".[dev]"
```

### Verify

```powershell
terraform-builder --version
# terraform-builder, version 0.1.0
```

---

## Usage

### Interactive Wizard (`init`)

```powershell
terraform-builder init [--output OUTPUT_DIR] [--config-out CONFIG_PATH]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--output`, `-o` | `.` | Output directory for generated files |
| `--config-out` | `terraform-builder.yaml` | Path to save the YAML config |

The wizard walks through 7 sections:

1. **Project Settings** — name, region, environments
2. **Backend Configuration** — framework, app path, path base pattern
3. **Frontend Configuration** — include?, framework, directory
4. **AWS Services** — checkbox of 10 optional services
5. **Networking** — VPC and subnet CIDRs (defaults available)
6. **Database / ECS / DNS** — detailed settings per service
7. **Output Directory** — where to write generated files

A summary table is shown before generation. Type `n` to abort.

**Example session:**

```
┌─────────────────────────────┐
│   Terraform Builder         │
│   Generate production-ready │
│   Terraform + GitHub Actions│
│   for AWS                   │
└─────────────────────────────┘

── Project Settings ──
? Project name: my-saas-app
? AWS region: us-west-2
? Select environments: staging, prod
? Default environment: staging

── Backend Configuration ──
? Backend framework: .NET (ASP.NET Core)
? Backend application path: APIs/MyApp
? API path base pattern: /{project}-{env}/api

── Frontend Configuration ──
? Include a frontend (S3 + CloudFront)? Yes
? Frontend framework: React (Vite)
? Frontend directory path: frontend

── AWS Services ──
? Select optional AWS services:
  ✓ RDS PostgreSQL
  ✓ ECS Fargate
  ✓ Route53
  ✓ KMS
  ✓ Secrets Manager
  ✓ SSM Parameter Store
  ○ Cognito
  ○ DynamoDB cache table
  ✓ Lambda scheduler
  ✓ EC2 bastion host

── Configuration Summary ──
┌──────────────┬───────────────────────────────┐
│ Setting      │ Value                         │
├──────────────┼───────────────────────────────┤
│ Project      │ my-saas-app                   │
│ Region       │ us-west-2                     │
│ Environments │ staging, prod                 │
│ Backend      │ dotnet                        │
│ Frontend     │ react                         │
│ AWS Services │ RDS, ECS, ALB, ECR, ROUTE53,  │
│              │ KMS, SECRETS MANAGER, SSM,    │
│              │ SCHEDULER, EC2 BASTION,       │
│              │ S3 FRONTEND, CLOUDFRONT       │
│ Output Dir   │ .                             │
└──────────────┴───────────────────────────────┘

? Generate files with this configuration? Yes
```

### Regenerate from Config (`generate`)

```powershell
terraform-builder generate -c terraform-builder.yaml
```

Skips the wizard entirely — reads the YAML config and regenerates all files. Useful for:
- Updating after editing the YAML manually
- CI pipelines that produce infra from versioned config
- Regenerating after upgrading terraform-builder

### List Services (`list-services`)

```powershell
terraform-builder list-services
```

Outputs a table of all 15 available AWS services with descriptions and default states.

---

## Configuration Model

Configuration is stored in a single `terraform-builder.yaml` file. The underlying Pydantic model (`ProjectConfig`) validates and resolves dependencies automatically.

### Project Basics

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `project_name` | string | `myproject` | Lowercase, hyphens allowed. Used in resource naming. |
| `aws_region` | string | `us-east-1` | AWS deployment region. |
| `environments` | list[str] | `[staging, beta, prod]` | Deployment environments. |
| `default_environment` | string | `beta` | Default for workflow `workflow_dispatch`. |

### Backend Framework

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `backend_framework` | enum | `dotnet` | One of: `dotnet`, `nodejs`, `python`, `go`. |
| `backend_app_path` | string | `APIs/App` | Relative path to backend source. |
| `path_base_pattern` | string | `/{project}-{env}/api` | ALB path pattern. `{project}` and `{env}` are substituted. |

### Frontend (Optional)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `include_frontend` | bool | `false` | Enable S3 + CloudFront frontend. |
| `frontend_framework` | enum/null | `null` | One of: `react`, `vue`, `angular`, `plain`. |
| `frontend_path` | string | `frontend` | Relative path to frontend source. |

### AWS Service Toggles

| Toggle | Default | Auto-Enabled By | Description |
|--------|---------|----------------|-------------|
| `include_vpc` | `true` | Always on | VPC with public/private subnets |
| `include_rds` | `true` | — | RDS PostgreSQL (auto-enables KMS) |
| `include_ecs` | `true` | — | ECS Fargate (auto-enables ECR + ALB) |
| `include_ecr` | `true` | ECS | Elastic Container Registry |
| `include_alb` | `true` | ECS, Route53 | Application Load Balancer |
| `include_route53` | `false` | — | DNS records for API subdomain |
| `include_kms` | `true` | RDS | Customer-managed encryption keys |
| `include_secrets_manager` | `true` | — | Secrets storage |
| `include_ssm` | `true` | — | Parameter Store |
| `include_cognito` | `false` | — | JWT auth via Cognito |
| `include_dynamodb_cache` | `false` | — | Pay-per-request cache table |
| `include_scheduler` | `false` | — | Lambda stop/start scheduler |
| `include_ec2_bastion` | `false` | — | SSM-managed bastion host |
| `include_s3_frontend` | `false` | Frontend | S3 static hosting |
| `include_cloudfront` | `false` | Frontend | CDN distribution |

### Sub-Configurations

<details>
<summary><strong>VpcConfig</strong></summary>

| Field | Default |
|-------|---------|
| `vpc_cidr` | `10.0.0.0/16` |
| `public_subnet_cidr` | `10.0.0.0/20` |
| `public_2b_cidr` | `10.0.16.0/24` |
| `private_subnet_cidr` | `10.0.128.0/20` |
| `private_2a_cidr` | `10.0.144.0/20` |
| `private_2b_cidr` | `10.0.160.0/20` |

</details>

<details>
<summary><strong>RdsConfig</strong></summary>

| Field | Default |
|-------|---------|
| `instance_class` | `db.t4g.micro` |
| `allocated_storage` | `20` |
| `postgres_version` | `16` |
| `database_name` | `appdb` |
| `username` | `postgres` |
| `storage_type` | `gp2` |
| `skip_final_snapshot` | `true` |
| `backup_retention_period` | `7` |
| `multi_az` | `false` |

</details>

<details>
<summary><strong>EcsConfig</strong></summary>

| Field | Default |
|-------|---------|
| `task_cpu` | `256` |
| `task_memory` | `512` |
| `desired_count` | `1` |
| `container_port` | `80` |
| `health_check_path` | `/api/v1/health` |

</details>

<details>
<summary><strong>DnsConfig</strong></summary>

| Field | Default |
|-------|---------|
| `route53_zone_name` | (empty) |
| `api_subdomain` | `api` |

</details>

<details>
<summary><strong>SchedulerConfig</strong></summary>

| Field | Default |
|-------|---------|
| `stop_cron` | `cron(0 5 * * ? *)` |
| `start_cron` | `cron(0 14 ? * MON-FRI *)` |

</details>

### Dependency Resolution

The `ProjectConfig` model validator automatically enables dependent services:

```
ECS → ECR + ALB
Frontend → S3 Frontend + CloudFront
RDS → KMS
Route53 → ALB
```

This means if you enable ECS, you don't need to manually enable ECR and ALB — they'll be turned on automatically.

---

## Generated Output Structure

```
output/
├── .github/
│   └── workflows/
│       ├── 0.1-onetime-provision-terraform-backend.yml
│       ├── 0.2-onetime-provision-github-oidc-secrets-variables.yml
│       ├── 1-deploy-infra.yml
│       ├── 2-backend-build-and-push.yml          # if ECS enabled
│       ├── 3-frontend-deploy.yml                  # if frontend enabled
│       ├── 4-destroy-infra-keep-rds.yml
│       └── 5-recreate-infra.yml
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── backend.tf
│   ├── ecs.tf                                     # if ECS enabled
│   ├── user_data.sh                               # if EC2 bastion enabled
│   ├── lambda/
│   │   └── scheduler.py                           # if scheduler enabled
│   ├── bootstrap_orchestration/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   ├── backend.tf
│   │   └── bootstrap_environments.tfvars
│   ├── ci_aws_oidc/
│   │   ├── main.tf
│   │   └── variables.tf
│   └── github_provider/
│       ├── provider.tf
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
├── {backend_app_path}/
│   └── Dockerfile                                  # if ECS enabled
├── .gitignore
├── .env.example
├── docker-compose.yml                              # if ECS enabled
└── README.md
```

---

## Template Reference

### Terraform Templates

| Template | Output | Condition | Description |
|----------|--------|-----------|-------------|
| `main.tf.j2` | `terraform/main.tf` | Always | VPC, subnets, IGW, NAT, security groups, EC2, RDS, KMS, ECR, Lambda scheduler |
| `variables.tf.j2` | `terraform/variables.tf` | Always | All Terraform variables with config-derived defaults |
| `outputs.tf.j2` | `terraform/outputs.tf` | Always | Conditional outputs per enabled service |
| `backend.tf.j2` | `terraform/backend.tf` | Always | S3 backend stub with init instructions |
| `ecs.tf.j2` | `terraform/ecs.tf` | `include_ecs` | ECS cluster, task definition, service, ALB, auto scaling, DynamoDB cache, Route53 |
| `user_data.sh.j2` | `terraform/user_data.sh` | `include_ec2_bastion` | EC2 bootstrap script with optional PostgreSQL client |
| `lambda/scheduler.py.j2` | `terraform/lambda/scheduler.py` | `include_scheduler` | Lambda handler for start/stop EC2 + RDS |

**Sub-modules:**

| Directory | Files | Description |
|-----------|-------|-------------|
| `bootstrap_orchestration/` | `main.tf.j2`, `variables.tf.j2`, `outputs.tf.j2`, `backend.tf.j2`, `bootstrap_environments.tfvars.j2` | Orchestrates CI role + GitHub provider modules |
| `ci_aws_oidc/` | `main.tf.j2`, `variables.tf.j2` | GitHub OIDC IAM role with conditional policy statements |
| `github_provider/` | `provider.tf.j2`, `main.tf.j2`, `variables.tf.j2`, `outputs.tf.j2` | Creates GitHub environments and environment variables |

### Workflow Templates

| Template | Output | Condition | Description |
|----------|--------|-----------|-------------|
| `0.1-*.yml.j2` | `0.1-onetime-provision-terraform-backend.yml` | Always | One-time S3 + DynamoDB backend provisioning |
| `0.2-*.yml.j2` | `0.2-onetime-provision-github-oidc-secrets-variables.yml` | Always | One-time CI role + GitHub secrets/variables |
| `1-*.yml.j2` | `1-deploy-infra.yml` | Always | Terraform plan + apply with TF_VAR exports |
| `2-*.yml.j2` | `2-backend-build-and-push.yml` | `include_ecs` | Docker build → ECR push → ECS deploy |
| `3-*.yml.j2` | `3-frontend-deploy.yml` | `include_frontend` | Frontend build → S3 sync → CloudFront invalidation |
| `4-*.yml.j2` | `4-destroy-infra-keep-rds.yml` | Always | Destroy infra while preserving RDS, VPC, ECR, KMS |
| `5-*.yml.j2` | `5-recreate-infra.yml` | Always | Restore pre-destroy state snapshot and re-apply |

### Dockerfile Templates

| Template | Framework | Base images |
|----------|-----------|-------------|
| `Dockerfile.dotnet.j2` | .NET 10 | `mcr.microsoft.com/dotnet/sdk:10.0` → `aspnet:10.0` |
| `Dockerfile.nodejs.j2` | Node.js 22 | `node:22-alpine` (multi-stage) |
| `Dockerfile.python.j2` | Python 3.13 | `python:3.13-slim` (multi-stage) |
| `Dockerfile.go.j2` | Go 1.24 | `golang:1.24-alpine` → `alpine:3.21` |

### Miscellaneous Templates

| Template | Output | Description |
|----------|--------|-------------|
| `gitignore.j2` | `.gitignore` | Framework-aware ignore patterns |
| `env.example.j2` | `.env.example` | Environment variable template |
| `docker-compose.yml.j2` | `docker-compose.yml` | Local dev with optional PostgreSQL |
| `README.md.j2` | `README.md` | Generated project README with architecture table |

---

## Architecture

```
terraform_builder/
├── __init__.py              # Package metadata (version)
├── __main__.py              # `python -m terraform_builder` entry
├── cli.py                   # Click CLI: init, generate, list-services
├── models/
│   └── __init__.py          # Pydantic models (ProjectConfig + sub-configs)
├── wizard/
│   ├── __init__.py          # Public API: run_wizard()
│   ├── runner.py            # InquirerPy prompt orchestration
│   └── validators.py        # Input validation (CIDR, names, ports)
├── generator/
│   ├── __init__.py          # Public API: generate_all()
│   ├── base.py              # Jinja2 Environment, render_template, write_rendered
│   ├── engine.py            # Orchestrates all generators
│   ├── terraform_gen.py     # Terraform .tf file generation
│   ├── workflow_gen.py      # GitHub Actions .yml generation
│   ├── dockerfile_gen.py    # Framework-specific Dockerfile generation
│   └── misc_gen.py          # .gitignore, README, etc.
└── templates/
    ├── terraform/           # 16 Jinja2 templates (main + 3 sub-modules)
    ├── workflows/           # 7 Jinja2 workflow templates
    ├── dockerfiles/         # 4 framework-specific Dockerfiles
    └── misc/                # 4 scaffolding templates
```

**Data flow:**

```
CLI (click) → Wizard (InquirerPy) → ProjectConfig (Pydantic)
                                          │
                                    ┌─────┴─────┐
                                    │  to_yaml() │ ← saved to disk
                                    └─────┬─────┘
                                          │
                              Generator Engine (Jinja2)
                              ┌───────┬───────┬──────┐
                              │       │       │      │
                          terraform workflow docker  misc
                            _gen     _gen   _gen    _gen
                              │       │       │      │
                              └───────┴───────┴──────┘
                                          │
                                  Output directory
```

**Template rendering:**

All templates receive a single context variable `config` (the `ProjectConfig` instance). Conditional blocks use:

```jinja
{% if config.include_rds %}
resource "aws_db_instance" "main" { ... }
{% endif %}
```

Workflow templates escape GitHub Actions expressions with:

```jinja
{% raw %}${{ secrets.CI_AWS_ROLE_ARN }}{% endraw %}
```

---

## Examples

### Example 1: Full-Stack .NET with All Services

```yaml
# terraform-builder.yaml
project_name: portfolio
aws_region: us-east-1
environments: [staging, beta, prod]
default_environment: beta
backend_framework: dotnet
backend_app_path: APIs/Portfolio.Api
path_base_pattern: /{project}-{env}/content
include_frontend: true
frontend_framework: react
frontend_path: portfolio-frontend
include_rds: true
include_ecs: true
include_route53: true
include_cognito: true
include_dynamodb_cache: true
include_scheduler: true
include_ec2_bastion: true
```

```powershell
terraform-builder generate -c terraform-builder.yaml
```

Generates 37 files including all Terraform, all 7 workflows, .NET Dockerfile, and full scaffolding.

### Example 2: Minimal Python API

```yaml
project_name: data-api
aws_region: eu-west-1
environments: [dev, prod]
default_environment: dev
backend_framework: python
backend_app_path: api
path_base_pattern: /{project}-{env}/v1
include_frontend: false
include_rds: true
include_ecs: true
include_route53: false
include_cognito: false
include_dynamodb_cache: false
include_scheduler: false
include_ec2_bastion: false
```

Generates: Terraform (main, variables, outputs, backend, ecs), 5 workflows (no frontend), Python Dockerfile, and scaffolding.

### Example 3: Go Microservice (No Frontend)

```yaml
project_name: payment-svc
aws_region: us-west-2
environments: [staging, prod]
backend_framework: go
backend_app_path: cmd/server
path_base_pattern: /{project}-{env}/api
include_frontend: false
include_rds: false
include_ecs: true
include_route53: true
include_secrets_manager: true
include_ssm: true
```

No RDS, no frontend — just ECS Fargate + ALB + Route53 with a Go Dockerfile.

### Example 4: Node.js with Frontend

```yaml
project_name: webapp
aws_region: ap-southeast-1
environments: [staging, prod]
backend_framework: nodejs
backend_app_path: backend
include_frontend: true
frontend_framework: vue
frontend_path: client
include_rds: true
include_ecs: true
include_scheduler: true
```

Generates Node.js Dockerfile, Vue frontend workflow, and Lambda scheduler.

---

## Development

### Project Setup

```powershell
git clone https://github.com/healthdots-jzhu/terraform-builder.git
Set-Location terraform-builder
pip install -e ".[dev]"
```

### Running Tests

```powershell
# Run all 67 tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=terraform_builder --cov-report=term-missing

# Run specific test file
python -m pytest tests/test_models.py -v

# Run specific test class
python -m pytest tests/test_generator.py::TestRenderTemplate -v
```

### Adding a New Template

1. Create the Jinja2 template file in `terraform_builder/templates/<category>/`
2. Add rendering logic to the appropriate generator (`terraform_gen.py`, `workflow_gen.py`, etc.)
3. Add a render test in `tests/test_generator.py`
4. If conditional, add a service toggle to `ProjectConfig` and a condition check in the generator

### Adding a New Service Toggle

1. Add the `include_<service>: bool` field to `ProjectConfig` in `models/__init__.py`
2. Add dependency logic to `resolve_dependencies()` if needed
3. Add `{% if config.include_<service> %}` blocks to affected templates
4. Add the service to `_ask_services()` in `wizard/runner.py`
5. Add the service to the `list-services` table in `cli.py`
6. Add tests for the new toggle in `tests/test_models.py`

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: terraform_builder` | Run `pip install -e .` from repo root |
| `jinja2.exceptions.UndefinedError` | Template uses a `config.xxx` attribute that doesn't exist in the model. Check `models/__init__.py` field names match template references. |
| `Circular import` | Generator modules must import from `generator.base`, not `generator.engine`. See `base.py` for shared utilities. |
| Template renders empty | Check if the template's `{% if config.include_xxx %}` condition evaluates to `True` for your config |
| YAML config won't load | Ensure enum values are lowercase strings (`dotnet`, not `DOTNET`) |
| Workflow `${{ }}` rendered as empty | GitHub Actions expressions must be wrapped in `{% raw %}...{% endraw %}` in templates |

---

## License

MIT
