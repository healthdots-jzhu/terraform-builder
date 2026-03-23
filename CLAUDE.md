# CLAUDE.md

## Purpose
Interactive Python CLI wizard that generates production-ready Terraform scripts and GitHub Actions workflows for AWS infrastructure. Modeled after the HealthDots Portfolio platform architecture.

## Project Structure
- `terraform_builder/cli.py`: Click CLI — `init`, `generate`, `list-services` commands.
- `terraform_builder/models/__init__.py`: Pydantic v2 configuration models with 15 AWS service toggles and automatic dependency resolution.
- `terraform_builder/wizard/runner.py`: InquirerPy interactive prompt flow (7 sections).
- `terraform_builder/wizard/validators.py`: CIDR, project name, and port validators.
- `terraform_builder/generator/base.py`: Jinja2 environment setup, `render_template()`, `write_rendered()`.
- `terraform_builder/generator/engine.py`: `generate_all()` orchestrator.
- `terraform_builder/generator/terraform_gen.py`: Renders 16 Terraform templates.
- `terraform_builder/generator/workflow_gen.py`: Renders 7 GitHub Actions workflow templates.
- `terraform_builder/generator/dockerfile_gen.py`: Renders framework-specific Dockerfiles (dotnet, nodejs, python, go).
- `terraform_builder/generator/misc_gen.py`: Renders scaffolding (.gitignore, README, docker-compose, .env.example).
- `terraform_builder/templates/`: 31 Jinja2 templates organized in `terraform/`, `workflows/`, `dockerfiles/`, `misc/`.
- `tests/`: 67 pytest tests covering models, validators, template rendering, and integration.
- `docs/`: Template authoring guide, deployment walkthrough, configuration reference.

## Tech Stack
- Python 3.10+, Click, InquirerPy, Jinja2 (StrictUndefined), Pydantic v2, PyYAML, Rich
- Testing: pytest + pytest-cov
- Build: setuptools via pyproject.toml

## Local Development (PowerShell)

```powershell
# Install
Set-Location terraform-builder
pip install -e ".[dev]"

# Run tests
python -m pytest tests/ -v

# Interactive wizard
terraform-builder init

# Regenerate from config
terraform-builder generate -c terraform-builder.yaml
```

## Key Conventions
- Templates receive `config` (ProjectConfig instance) as sole Jinja2 context variable.
- Conditional blocks: `{% if config.include_xxx %}`.
- Workflow templates: `${{ }}` must be wrapped in `{% raw %}...{% endraw %}`.
- Template attribute names must match Pydantic model field names exactly.
- Generators import from `generator.base`, never from `generator.engine` (circular import prevention).
- `ProjectConfig.resolve_dependencies()` auto-enables: ECS→ECR+ALB, Frontend→S3+CloudFront, RDS→KMS.

## Generated Output
- `terraform/` — HCL files with sub-modules (bootstrap_orchestration, ci_aws_oidc, github_provider)
- `.github/workflows/` — Numbered CI/CD workflows (0.1, 0.2, 1-5)
- `{backend_app_path}/Dockerfile` — Framework-specific containerization
- Root scaffolding: .gitignore, .env.example, README.md, docker-compose.yml

## AWS Services (15 toggleable)
VPC (always on), RDS PostgreSQL, ECS Fargate, ALB, ECR, Route53, KMS, Secrets Manager, SSM Parameter Store, Cognito, DynamoDB Cache, Lambda Scheduler, EC2 Bastion, S3 Frontend, CloudFront.

## High-Risk Areas
- Circular imports: `generator.engine` ↔ generator modules — use `generator.base` for shared code.
- Template attribute mismatches: `StrictUndefined` catches at render time.
- Jinja2/GitHub Actions expression collision: missing `{% raw %}` causes empty values.
- Dependency resolution runs in `model_validator(mode="after")` — YAML reflects resolved state.

## Agent Guardrails
- Keep changes scoped; avoid broad refactors unless requested.
- When modifying templates, verify attribute names match model field names.
- When changing models, search all templates for impacted references.
- After any change, run `python -m pytest tests/ -v` to validate.
- Use PowerShell command style in documentation.
