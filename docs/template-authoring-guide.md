# Template Authoring Guide

This guide explains how to create, modify, and maintain Jinja2 templates in terraform-builder.

## Template Basics

All templates are Jinja2 files (`.j2` extension) that receive a single context variable: `config` — an instance of `ProjectConfig`. The Jinja2 environment is configured with:

```python
Environment(
    keep_trailing_newline=True,  # preserve trailing newlines
    trim_blocks=True,            # remove first newline after a block tag
    lstrip_blocks=True,          # strip leading whitespace before block tags
    undefined=StrictUndefined,   # fail loudly on undefined variables
)
```

## Template Locations

```
terraform_builder/templates/
├── terraform/                # Terraform .tf files
│   ├── main.tf.j2
│   ├── variables.tf.j2
│   ├── outputs.tf.j2
│   ├── backend.tf.j2
│   ├── ecs.tf.j2
│   ├── user_data.sh.j2
│   ├── lambda/scheduler.py.j2
│   ├── bootstrap_orchestration/
│   ├── ci_aws_oidc/
│   └── github_provider/
├── workflows/                # GitHub Actions .yml files
├── dockerfiles/              # Framework-specific Dockerfiles
└── misc/                     # .gitignore, README, etc.
```

## Conditional Blocks

Use `{% if config.include_xxx %}` to conditionally include resources:

```hcl
{% if config.include_rds %}
resource "aws_db_instance" "main" {
  identifier     = "${var.project_name}-${var.environment}-db"
  engine         = "postgres"
  engine_version = var.postgres_version
  # ...
}
{% endif %}
```

### Nesting Conditions

```hcl
{% if config.include_ecs %}
resource "aws_ecs_cluster" "main" {
  name = "${local.name_prefix}-cluster"
}

{% if config.include_dynamodb_cache %}
resource "aws_dynamodb_table" "cache" {
  name = "${local.name_prefix}-cache"
  # ...
}
{% endif %}
{% endif %}
```

## Config Variable Reference

Access any field from `ProjectConfig`:

```jinja
{{ config.project_name }}                    → "my-app"
{{ config.aws_region }}                      → "us-west-2"
{{ config.backend_framework.value }}         → "dotnet"
{{ config.environments }}                    → ["staging", "prod"]
{{ config.ecs.container_port }}              → 80
{{ config.rds.database_name }}               → "appdb"
{{ config.vpc.vpc_cidr }}                    → "10.0.0.0/16"
{{ config.dns.api_subdomain }}               → "api"
{{ config.dns.route53_zone_name }}           → "example.com"
{{ config.rds.postgres_version }}            → "16"
{{ config.rds.username }}                    → "postgres"
{{ config.rds.backup_retention_period }}     → 7
{{ config.frontend_framework.value }}        → "react" (or None if no frontend)
```

### Boolean Toggles

```
config.include_vpc                → True (always)
config.include_rds                → True/False
config.include_ecs                → True/False
config.include_ecr                → True/False (auto-enabled by ECS)
config.include_alb                → True/False (auto-enabled by ECS)
config.include_route53            → True/False
config.include_kms                → True/False (auto-enabled by RDS)
config.include_secrets_manager    → True/False
config.include_ssm                → True/False
config.include_cognito            → True/False
config.include_dynamodb_cache     → True/False
config.include_scheduler          → True/False
config.include_ec2_bastion        → True/False
config.include_frontend           → True/False
config.include_s3_frontend        → True/False (auto-enabled by frontend)
config.include_cloudfront         → True/False (auto-enabled by frontend)
```

## Jinja2 Filters

Standard Jinja2 filters work:

```jinja
{{ config.rds.skip_final_snapshot | lower }}   → "true" / "false"
{{ config.dns.api_subdomain | default('api') }}
{{ config.environments | length }}
{{ config.environments | join(', ') }}
```

## Loops

Iterate over environments:

```jinja
{% for env in config.environments %}
  {{ env }} = {
    tf_state_key = "{{ config.project_name }}/{{ env }}.tfstate"
  }
{% endfor %}
```

## Escaping GitHub Actions Expressions

**Critical:** Workflow templates must escape `${{ }}` to prevent Jinja2 from interpreting them:

```yaml
# WRONG — Jinja2 will try to evaluate this
role-to-assume: ${{ secrets.CI_AWS_ROLE_ARN }}

# CORRECT — escaped from Jinja2
role-to-assume: {% raw %}${{ secrets.CI_AWS_ROLE_ARN }}{% endraw %}
```

Every `${{ }}` expression in a workflow template MUST be wrapped in `{% raw %}...{% endraw %}`.

## Adding a New Terraform Template

### Step 1: Create the template

```
terraform_builder/templates/terraform/my_new_resource.tf.j2
```

```hcl
{% if config.include_my_service %}
resource "aws_my_resource" "main" {
  name = "${var.project_name}-${var.environment}"
  # ...
}
{% endif %}
```

### Step 2: Register in the generator

Edit `terraform_builder/generator/terraform_gen.py`:

```python
# Option A: Add to _MAIN_TEMPLATES if it's always generated
_MAIN_TEMPLATES = [
    "main.tf.j2",
    "variables.tf.j2",
    "outputs.tf.j2",
    "backend.tf.j2",
    "my_new_resource.tf.j2",  # ← add here
]

# Option B: Add conditional logic in generate_terraform()
if config.include_my_service:
    content = render_template("terraform", "my_new_resource.tf.j2", config)
    write_rendered(tf_dir / "my_new_resource.tf", content)
```

### Step 3: Add a render test

In `tests/test_generator.py`:

```python
def test_my_new_resource_renders(self, full_config):
    result = render_template("terraform", "my_new_resource.tf.j2", full_config)
    assert "aws_my_resource" in result
```

## Adding a New Workflow Template

### Step 1: Create the template

```yaml
# terraform_builder/templates/workflows/6-my-workflow.yml.j2
name: 'My Workflow'

on:
  workflow_dispatch:
    inputs:
      environment:
        required: true
        default: '{{ config.default_environment }}'
        type: choice
        options:
{% for env in config.environments %}
          - {{ env }}
{% endfor %}

jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6.0.2
      - uses: aws-actions/configure-aws-credentials@v5.1.1
        with:
          role-to-assume: {% raw %}${{ secrets.CI_AWS_ROLE_ARN }}{% endraw %}
          aws-region: {% raw %}${{ vars.AWS_REGION }}{% endraw %}
```

### Step 2: Register in workflow_gen.py

```python
_CONDITIONAL_WORKFLOWS = [
    # ... existing entries ...
    ("6-my-workflow.yml.j2", lambda c: c.include_my_service),
]
```

### Step 3: Add a render test

```python
def test_my_workflow_renders(self, full_config):
    result = render_template("workflows", "6-my-workflow.yml.j2", full_config)
    assert "name:" in result
```

## Common Patterns

### Resource naming convention

```hcl
"${var.project_name}-${var.environment}-<resource>"
```

Or using locals:

```hcl
"${local.name_prefix}-<resource>"
```

### IAM policy conditional statements

```hcl
{% if config.include_secrets_manager %}
    statement {
      effect = "Allow"
      actions = ["secretsmanager:GetSecretValue"]
      resources = ["arn:aws:secretsmanager:*:*:secret:${var.project_name}-*"]
    }
{% endif %}
```

### Terraform lifecycle protection

```hcl
  lifecycle {
    prevent_destroy = true
  }
```

## Testing Templates

```powershell
# Test all templates render without errors
python -m pytest tests/test_generator.py::TestRenderTemplate -v

# Test full generation pipeline
python -m pytest tests/test_generator.py::TestGenerateAll -v

# Quick manual test with a config
python -c "
from terraform_builder.models import ProjectConfig
from terraform_builder.generator.base import render_template
cfg = ProjectConfig(include_rds=True, include_ecs=True)
print(render_template('terraform', 'main.tf.j2', cfg))
"
```

## Troubleshooting Template Issues

| Error | Cause | Fix |
|-------|-------|-----|
| `UndefinedError: 'X' has no attribute 'Y'` | Template uses wrong attribute name | Check `models/__init__.py` for correct field name |
| `UndefinedError: 'config' is undefined` | Template doesn't receive context | Ensure generator passes `config=config` to `render_template()` |
| Empty output | All conditional blocks evaluate to `False` | Check service toggle values in your config |
| `${{ }}` renders empty in workflow | Missing `{% raw %}` wrapper | Wrap ALL `${{ }}` in `{% raw %}...{% endraw %}` |
| `TemplateSyntaxError` | Malformed Jinja2 syntax | Check for unclosed `{% if %}`, missing `{% endif %}`, or unmatched braces |
