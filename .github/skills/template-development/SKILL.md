---
name: template-development
description: Guidance for authoring Jinja2 templates for Terraform, workflows, Dockerfiles, and scaffold files in terraform-builder.
applyTo: "terraform_builder/templates/**/*.j2"
---

# Template Development Skill

You are working on Jinja2 templates for terraform-builder. These templates generate Terraform HCL, GitHub Actions YAML, Dockerfiles, and project scaffolding.

## Context Variable

All templates receive a single context variable: `config` - an instance of `ProjectConfig` (defined in `terraform_builder/models/__init__.py`).

## Attribute Reference

### Project-level
- `config.project_name` (str)
- `config.aws_region` (str)
- `config.environments` (list[str])
- `config.default_environment` (str)
- `config.backend_framework` (BackendFramework enum - `.value` for string)
- `config.backend_app_path` (str)
- `config.path_base_pattern` (str)
- `config.include_frontend` (bool)
- `config.frontend_framework` (FrontendFramework enum or None)
- `config.frontend_path` (str)
- `config.output_dir` (str)

### Service toggles (all bool)
- `config.include_vpc`, `config.include_rds`, `config.include_ecs`
- `config.include_ecr`, `config.include_alb`, `config.include_route53`
- `config.include_kms`, `config.include_secrets_manager`, `config.include_ssm`
- `config.include_cognito`, `config.include_dynamodb_cache`
- `config.include_scheduler`, `config.include_ec2_bastion`
- `config.include_s3_frontend`, `config.include_cloudfront`

### Sub-configs
- `config.vpc.vpc_cidr`, `config.vpc.public_subnet_cidr`, `config.vpc.public_2b_cidr`, `config.vpc.private_subnet_cidr`, `config.vpc.private_2a_cidr`, `config.vpc.private_2b_cidr`
- `config.rds.instance_class`, `config.rds.allocated_storage`, `config.rds.postgres_version`, `config.rds.database_name`, `config.rds.username`, `config.rds.storage_type`, `config.rds.skip_final_snapshot`, `config.rds.backup_retention_period`, `config.rds.multi_az`
- `config.ecs.task_cpu`, `config.ecs.task_memory`, `config.ecs.desired_count`, `config.ecs.container_port`, `config.ecs.health_check_path`
- `config.dns.route53_zone_name`, `config.dns.api_subdomain`
- `config.ec2.instance_type`
- `config.scheduler.stop_cron`, `config.scheduler.start_cron`

## Rules

1. **Conditional blocks:** Use `{% if config.include_xxx %}...{% endif %}` for optional resources.
2. **GitHub Actions escaping:** In workflow templates (`.yml.j2`), ALWAYS wrap `${{ }}` in `{% raw %}...{% endraw %}`.
3. **Attribute matching:** Template attribute names MUST match Pydantic model field names exactly. `StrictUndefined` will raise errors on mismatches.
4. **Loops:** Use `{% for env in config.environments %}` for multi-environment iteration.
5. **Filters:** Use `| lower` for boolean-to-string, `| default('fallback')` for optional values.
6. **Resource naming:** Follow `${var.project_name}-${var.environment}-<resource>` or `${local.name_prefix}-<resource>` conventions.
7. **After changes:** Run `python -m pytest tests/test_generator.py -v` to verify all templates render.
