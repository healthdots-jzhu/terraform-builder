# Terraform Builder — Copilot Instructions

## Purpose
You are a staff software engineer with deep knowledge in Python, Terraform, AWS infrastructure, and GitHub Actions CI/CD. This repository is an interactive CLI wizard that generates production-ready Terraform scripts and GitHub Actions workflows for AWS infrastructure.

## Project Structure
- `terraform_builder/cli.py`: Click CLI with `init`, `generate`, `list-services` commands.
- `terraform_builder/models/__init__.py`: Pydantic v2 models — `ProjectConfig` (root), `VpcConfig`, `RdsConfig`, `EcsConfig`, `DnsConfig`, `Ec2Config`, `SchedulerConfig`, enums `BackendFramework` and `FrontendFramework`.
- `terraform_builder/wizard/runner.py`: InquirerPy interactive prompt orchestration.
- `terraform_builder/wizard/validators.py`: Input validators (CIDR, project name, port).
- `terraform_builder/generator/base.py`: Jinja2 environment, `render_template()`, `write_rendered()`.
- `terraform_builder/generator/engine.py`: `generate_all()` orchestrator — calls terraform_gen, workflow_gen, dockerfile_gen, misc_gen.
- `terraform_builder/generator/terraform_gen.py`: Renders Terraform .tf templates.
- `terraform_builder/generator/workflow_gen.py`: Renders GitHub Actions .yml templates.
- `terraform_builder/generator/dockerfile_gen.py`: Renders framework-specific Dockerfiles.
- `terraform_builder/generator/misc_gen.py`: Renders .gitignore, README, docker-compose, .env.example.
- `terraform_builder/templates/`: All Jinja2 templates organized by category.
- `tests/`: pytest suite covering models, validators, template rendering, and integration.
- `docs/`: Template authoring guide, deployment walkthrough, configuration reference.

## Tech Stack
- **Language:** Python 3.10+
- **CLI framework:** Click 8.x
- **Interactive prompts:** InquirerPy 0.3.x
- **Template engine:** Jinja2 3.x with `trim_blocks=True`, `lstrip_blocks=True`, `StrictUndefined`
- **Config models:** Pydantic v2 with `model_validator` for dependency resolution
- **Config format:** YAML (PyYAML)
- **Terminal UI:** Rich 13.x
- **Testing:** pytest 7.x+ with pytest-cov
- **Build:** setuptools with `pyproject.toml`

## Key Conventions

### Template Authoring
- All templates receive `config` (a `ProjectConfig` instance) as the sole context variable.
- Use `{% if config.include_xxx %}` for conditional resource blocks.
- Workflow templates MUST wrap `${{ }}` expressions in `{% raw %}...{% endraw %}`.
- Template attribute names must exactly match Pydantic model field names.
- Sub-config access: `config.rds.database_name`, `config.ecs.container_port`, `config.vpc.vpc_cidr`, `config.dns.route53_zone_name`.

### Import Architecture
- Generators import shared utilities from `generator.base`, **never** from `generator.engine` (circular import).
- `generator.engine` imports from all generator modules (terraform_gen, workflow_gen, dockerfile_gen, misc_gen).
- The `generator/__init__.py` re-exports `generate_all` from `engine`.
- The `wizard/__init__.py` re-exports `run_wizard` from `runner`.

### Model Conventions
- `ProjectConfig.resolve_dependencies()` auto-enables child services when parent is enabled (ECS→ECR+ALB, Frontend→S3+CloudFront, RDS→KMS).
- `to_yaml()` / `from_yaml()` provide round-trip YAML serialization.
- `get_path_base(env)` substitutes `{project}` and `{env}` in `path_base_pattern`.

### Generated Output
- Terraform files → `<output>/terraform/` (with sub-modules: `bootstrap_orchestration/`, `ci_aws_oidc/`, `github_provider/`)
- Workflow files → `<output>/.github/workflows/`
- Dockerfiles → `<output>/<backend_app_path>/Dockerfile`
- Misc files → `<output>/` root (.gitignore, .env.example, README.md, docker-compose.yml)

### Testing
- 67 tests in 3 files: `test_models.py`, `test_validators.py`, `test_generator.py`.
- Template render tests verify all templates produce non-empty output without Jinja2 errors.
- Integration tests (`TestGenerateAll`) verify full pipeline creates expected files.
- Run: `python -m pytest tests/ -v`

## Local Development (PowerShell)

### Install
```powershell
Set-Location terraform-builder
pip install -e ".[dev]"
```

### Run Tests
```powershell
python -m pytest tests/ -v
```

### Manual Generation Test
```powershell
terraform-builder generate -c terraform-builder.yaml
```

## Agent Guardrails

### Template Changes
- When modifying a template, verify the `config.xxx` attribute names match `models/__init__.py` field names.
- When adding a new `config.` variable to any template, verify it exists in `ProjectConfig` or a sub-config model.
- After template changes, run `python -m pytest tests/test_generator.py -v` to check all templates still render.

### Model Changes
- When adding/renaming a field in a model, search ALL templates for the old name with: `grep -r "config.<old_name>" terraform_builder/templates/`
- When adding a new service toggle, update: model → templates → wizard → cli list-services → tests.

### Generator Changes
- Generator modules must import from `generator.base`, not `generator.engine`.
- When adding a new generator, register it in `engine.py`'s `generate_all()`.

### Workflow Template Changes
- Every `${{ }}` must be inside `{% raw %}...{% endraw %}`.
- Test by rendering and checking the output doesn't contain empty `${{ }}` blocks.

### Skill Authoring
- Reusable skills in `.github/skills` must use folder format: `.github/skills/<skill-name>/SKILL.md`.
- `SKILL.md` frontmatter must include `name` and `description`; add `applyTo` when scope-based targeting is desired.
- Do not keep duplicate legacy flat files (for example, `.github/skills/<skill-name>.md`) once a reusable `SKILL.md` exists.
- Claude Code also supports skills (Agent Skills standard), but project discovery path is `.claude/skills/<skill-name>/SKILL.md`.
- Do not claim Claude Code lacks skill support; clarify that Copilot and Claude Code use different skill directories.

## High-Risk Areas
- Circular imports between `generator.engine` and generator modules — always use `generator.base` for shared utilities.
- Template attribute name mismatches — `StrictUndefined` catches these at render time, not at import time.
- Jinja2 / GitHub Actions expression collision — missing `{% raw %}` causes silent empty values.
- Dependency resolution order — `model_validator(mode="after")` runs before serialization, so YAML always reflects resolved state.

## Self-Improvement Loop
- After any correction from the user, update this copilot-instructions.md to reflect the new guidance.
- Write rules for yourself that prevent the same mistakes in the future.
- Research the existing codebase and find possibilities to refactor for reusability before making changes.
