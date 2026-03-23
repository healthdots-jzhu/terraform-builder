# Configuration Reference

Complete reference for all `terraform-builder.yaml` fields with examples and validation rules.

## Full Default Configuration

```yaml
project_name: myproject
aws_region: us-east-1
environments:
  - staging
  - beta
  - prod
default_environment: beta

backend_framework: dotnet
backend_app_path: APIs/App
path_base_pattern: /{project}-{env}/api

include_frontend: false
frontend_framework: null
frontend_path: frontend

include_vpc: true
include_rds: true
include_ecs: true
include_alb: true
include_route53: false
include_ecr: true
include_s3_frontend: false
include_cloudfront: false
include_kms: true
include_secrets_manager: true
include_ssm: true
include_cognito: false
include_dynamodb_cache: false
include_scheduler: false
include_ec2_bastion: false

vpc:
  vpc_cidr: 10.0.0.0/16
  public_subnet_cidr: 10.0.0.0/20
  public_2b_cidr: 10.0.16.0/24
  private_subnet_cidr: 10.0.128.0/20
  private_2a_cidr: 10.0.144.0/20
  private_2b_cidr: 10.0.160.0/20

rds:
  instance_class: db.t4g.micro
  allocated_storage: 20
  postgres_version: '16'
  database_name: appdb
  username: postgres
  storage_type: gp2
  skip_final_snapshot: true
  backup_retention_period: 7
  multi_az: false

ecs:
  task_cpu: '256'
  task_memory: '512'
  desired_count: 1
  container_port: 80
  health_check_path: /api/v1/health

dns:
  route53_zone_name: ''
  api_subdomain: api

ec2:
  instance_type: t4g.micro

scheduler:
  stop_cron: cron(0 5 * * ? *)
  start_cron: cron(0 14 ? * MON-FRI *)

output_dir: .
```

## Field Details

### `project_name`

- **Type:** string
- **Validation:** 3-50 chars, lowercase, alphanumeric with hyphens, must start with letter
- **Used in:** All AWS resource names, Terraform state keys, path base

```yaml
project_name: my-saas-app     # ✓ valid
project_name: MyApp            # ✗ uppercase not allowed
project_name: ab               # ✗ too short
```

### `aws_region`

- **Type:** string (AWS region code)
- **Supported:** `us-east-1`, `us-east-2`, `us-west-1`, `us-west-2`, `ca-central-1`, `eu-west-1`, `eu-west-2`, `eu-central-1`, `ap-southeast-1`, `ap-southeast-2`, `ap-northeast-1`

### `environments`

- **Type:** list of strings
- **Minimum:** 1 environment
- **Each entry** becomes a GitHub environment and a selectable target in `workflow_dispatch`

```yaml
# Common patterns:
environments: [dev, staging, prod]        # three-tier
environments: [staging, prod]             # two-tier
environments: [dev]                       # single
environments: [staging, beta, prod]       # default
```

### `backend_framework`

- **Type:** enum
- **Values:** `dotnet`, `nodejs`, `python`, `go`
- **Affects:** Dockerfile template selection, .gitignore patterns, docker-compose configuration

### `path_base_pattern`

- **Type:** string with `{project}` and `{env}` placeholders
- **Purpose:** ALB listener rule path pattern and application path base

```yaml
path_base_pattern: /{project}-{env}/api
# For project "demo" in "beta" → /demo-beta/api

path_base_pattern: /{project}-{env}/content
# For project "portfolio" in "prod" → /portfolio-prod/content
```

### `include_frontend`

When set to `true`, automatically enables `include_s3_frontend` and `include_cloudfront`.

Requires `frontend_framework` to be set:

```yaml
include_frontend: true
frontend_framework: react    # required when include_frontend is true
frontend_path: client        # optional, defaults to "frontend"
```

### `frontend_framework`

- **Type:** enum or null
- **Values:** `react`, `vue`, `angular`, `plain`
- **Required when:** `include_frontend: true`

### Service Toggle Dependencies

```
include_ecs: true
  → forces include_ecr: true
  → forces include_alb: true

include_frontend: true
  → forces include_s3_frontend: true
  → forces include_cloudfront: true

include_rds: true
  → forces include_kms: true

include_route53: true
  → forces include_alb: true
```

You can explicitly set auto-forced toggles to `false` in YAML, but the model validator will override them if their parent is enabled.

### VPC CIDR Blocks

Plan your CIDRs carefully if integrating with existing VPCs or peering:

```yaml
vpc:
  vpc_cidr: 10.0.0.0/16                 # /16 = 65,536 IPs
  public_subnet_cidr: 10.0.0.0/20       # /20 = 4,096 IPs (AZ a)
  public_2b_cidr: 10.0.16.0/24          # /24 = 256 IPs (AZ b)
  private_subnet_cidr: 10.0.128.0/20    # /20 = 4,096 IPs (RDS, AZ a)
  private_2a_cidr: 10.0.144.0/20        # /20 = 4,096 IPs (private AZ 2a)
  private_2b_cidr: 10.0.160.0/20        # /20 = 4,096 IPs (private AZ 2b)
```

### RDS Configuration

| Field | Description | Production Recommended |
|-------|-------------|----------------------|
| `instance_class` | Compute size | `db.t4g.small` or higher |
| `allocated_storage` | GB | `50+` |
| `postgres_version` | Engine version | `16` (latest stable) |
| `skip_final_snapshot` | Skip snapshot on delete | `false` |
| `backup_retention_period` | Backup days | `14+` |
| `multi_az` | Multi-AZ deployment | `true` |

### ECS Configuration

| Field | Description | CPU/Memory Combos |
|-------|-------------|-------------------|
| `task_cpu` | vCPU units | `256`, `512`, `1024`, `2048`, `4096` |
| `task_memory` | MB | `512`, `1024`, `2048`, `4096`, `8192` |
| `desired_count` | Running tasks | `1` (dev), `2+` (prod) |
| `container_port` | App port | Match your app's listening port |
| `health_check_path` | ALB health check | Must return 200 OK |

**Valid CPU/Memory combinations (Fargate):**

| CPU | Memory Options |
|-----|---------------|
| 256 | 512, 1024, 2048 |
| 512 | 1024, 2048, 3072, 4096 |
| 1024 | 2048, 3072, 4096, 5120, 6144, 7168, 8192 |
| 2048 | Between 4096 and 16384 in 1024 increments |
| 4096 | Between 8192 and 30720 in 1024 increments |

### Scheduler Configuration

EventBridge cron expressions (UTC):

```yaml
scheduler:
  stop_cron: "cron(0 5 * * ? *)"           # 5:00 AM UTC daily
  start_cron: "cron(0 14 ? * MON-FRI *)"   # 2:00 PM UTC Mon-Fri
```

## Programmatic Usage

```python
from terraform_builder.models import ProjectConfig, BackendFramework

# Create config programmatically
config = ProjectConfig(
    project_name="my-api",
    aws_region="eu-west-1",
    backend_framework=BackendFramework.PYTHON,
    include_ecs=True,
    include_rds=True,
)

# Serialize to YAML
yaml_str = config.to_yaml()

# Deserialize from YAML
config = ProjectConfig.from_yaml(yaml_str)

# Get path base for an environment
path = config.get_path_base("prod")  # → /my-api-prod/api

# Generate all files
from terraform_builder.generator import generate_all
config.output_dir = "/path/to/output"
generate_all(config)
```
