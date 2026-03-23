---
name: config-models
description: Guidance for editing Pydantic v2 configuration models and dependency behavior in terraform-builder.
applyTo: "terraform_builder/models/**"
---

# Configuration Model Skill

You are working on Pydantic v2 configuration models for terraform-builder. Models are defined in `terraform_builder/models/__init__.py`.

## Model Hierarchy

```
ProjectConfig (root)
├── VpcConfig          -> config.vpc
├── RdsConfig          -> config.rds
├── EcsConfig          -> config.ecs
├── DnsConfig          -> config.dns
├── Ec2Config          -> config.ec2
└── SchedulerConfig    -> config.scheduler
```

## Enums
- `BackendFramework`: `dotnet`, `nodejs`, `python`, `go`
- `FrontendFramework`: `react`, `vue`, `angular`, `plain`

## Key Behaviors

### Dependency Resolution
`ProjectConfig` has a `@model_validator(mode="after")` named `resolve_dependencies()` that auto-enables child services:
- `include_ecs` -> forces `include_ecr=True`, `include_alb=True`
- `include_frontend` -> forces `include_s3_frontend=True`, `include_cloudfront=True`
- `include_rds` -> forces `include_kms=True`

### YAML Serialization
- `to_yaml()` -> serializes via `model_dump(mode="json")` + PyYAML
- `from_yaml(text)` -> deserializes via `yaml.safe_load()` + `model_validate()`
- Round-trip safe: dependency resolution re-runs on deserialization

### Path Base
- `get_path_base(env)` substitutes `{project}` and `{env}` in `path_base_pattern`

## Rules When Modifying Models

1. **Field rename:** Search ALL templates for `config.<old_name>`:
   ```powershell
   Select-String -Path "terraform_builder/templates/**/*.j2" -Pattern "config\.<old_name>" -Recurse
   ```
2. **New toggle:** Update 5 locations: model -> templates -> wizard (`runner.py`) -> CLI (`cli.py` list-services) -> tests.
3. **New sub-config:** Add both the config class AND a Field on ProjectConfig with `default_factory`.
4. **Dependency chain:** If adding a new auto-enable rule, add it to `resolve_dependencies()` and document in README.
5. **After changes:** Run `python -m pytest tests/test_models.py tests/test_generator.py -v`.
