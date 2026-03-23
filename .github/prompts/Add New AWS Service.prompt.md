---
agent: agent
---

# Add New AWS Service Toggle

When adding a new toggleable AWS service to terraform-builder, follow these steps in order:

## Step 1: Add the model field
In `terraform_builder/models/__init__.py`:
- Add `include_<service>: bool = False` to `ProjectConfig`.
- If the service needs configuration, create a new sub-config class (e.g., `<Service>Config`) and add a field with `default_factory`.
- If the service depends on other services, add auto-enable logic in `resolve_dependencies()`.

## Step 2: Create the Terraform template
In `terraform_builder/templates/terraform/<service>.tf.j2`:
- Start with `{% if config.include_<service> %}` guard.
- Use `{{ config.project_name }}`, `{{ config.environment }}`, and sub-config fields.
- Follow naming convention: `"${var.project_name}-${var.environment}-<resource>"`.

## Step 3: Wire the generator
In `terraform_builder/generator/terraform_gen.py`:
- Add a conditional render/write block:
  ```python
  if config.include_<service>:
      content = render_template(env, "terraform/<service>.tf.j2", {"config": config})
      write_rendered(content, output_dir, "terraform", "<service>.tf")
  ```

## Step 4: Add to the wizard
In `terraform_builder/wizard/runner.py`:
- Add a checkbox option in the service selection section.

## Step 5: Update CLI list-services
In `terraform_builder/cli.py`:
- Add the service to the `list_services` command output table.

## Step 6: Add tests
- `tests/test_models.py`: Test default value, dependency resolution, YAML round-trip.
- `tests/test_generator.py`: Test file is generated when enabled, not generated when disabled.

## Step 7: Update documentation
- Add to README.md service table.
- Add to `docs/configuration-reference.md`.
- Update CLAUDE.md AWS Services list.

## Verification
```powershell
python -m pytest tests/ -v
```
