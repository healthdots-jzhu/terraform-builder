---
name: generator-engine
description: Guidance for modifying Terraform Builder generator modules and orchestration without introducing circular imports.
applyTo: "terraform_builder/generator/**"
---

# Generator Engine Skill

You are working on the code generation engine for terraform-builder. Generators live in `terraform_builder/generator/`.

## Module Layout

| Module | Responsibility |
| --- | --- |
| `base.py` | Jinja2 env setup, `render_template()`, `write_rendered()` |
| `engine.py` | `generate_all()` orchestrator, output directory creation |
| `terraform_gen.py` | `generate_terraform_files()` - `.tf` files |
| `workflow_gen.py` | `generate_workflow_files()` - `.github/workflows` `*.yml` |
| `dockerfile_gen.py` | `generate_dockerfile_files()` - Dockerfile, `.dockerignore`, compose |
| `misc_gen.py` | `generate_misc_files()` - `.env.example`, `.gitignore`, README |

## Jinja2 Environment Configuration (in `base.py`)

```python
Environment(
    loader=FileSystemLoader(template_dir),
    trim_blocks=True,
    lstrip_blocks=True,
    keep_trailing_newline=True,
    undefined=StrictUndefined  # fails fast on missing variables
)
```

## Import Rules (CRITICAL)

Circular import prevention architecture:
- `base.py` imports NOTHING from other generator modules or the models package at module level.
- `engine.py` imports from `base.py` AND all `*_gen.py` modules.
- `*_gen.py` modules import ONLY from `base.py`.
- Config objects are passed as function arguments, never imported at module level.

```
engine.py --imports--> base.py
engine.py --imports--> terraform_gen.py --imports--> base.py
engine.py --imports--> workflow_gen.py  --imports--> base.py
engine.py --imports--> dockerfile_gen.py--imports--> base.py
engine.py --imports--> misc_gen.py     --imports--> base.py
```

## Template Context

Every template receives `{"config": <ProjectConfig instance>}`.
Access in templates: `{{ config.project_name }}`, `{% if config.include_rds %}`, `{{ config.rds.instance_class }}`.

## Rules When Modifying Generators

1. **New template file:** Add a `render_template()` + `write_rendered()` call in the appropriate `*_gen.py`, then add the call in `engine.py` if it is a new generator function.
2. **Conditional generation:** Wrap the render/write call with `if config.include_<service>:`.
3. **Never import models at module level** in any generator file - always receive config via parameters.
4. **Template path:** First argument to `render_template()` must match exactly the relative path under `templates/` (for example, `"terraform/ecs.tf.j2"`).
5. **Output path:** Use `os.path.join(output_dir, ...)` - never hardcode path separators.
6. **After changes:** Run `python -m pytest tests/test_generator.py -v`.
