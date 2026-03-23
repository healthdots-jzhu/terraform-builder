---
agent: agent
---

# Add New Template

When adding a new Jinja2 template to terraform-builder, follow this procedure:

## 1. Determine the template category

| Category      | Directory                                  | Generator module       |
|---------------|--------------------------------------------|------------------------|
| Terraform     | `terraform_builder/templates/terraform/`   | `terraform_gen.py`     |
| Workflows     | `terraform_builder/templates/workflows/`   | `workflow_gen.py`      |
| Dockerfiles   | `terraform_builder/templates/dockerfiles/` | `dockerfile_gen.py`    |
| Miscellaneous | `terraform_builder/templates/misc/`        | `misc_gen.py`          |

## 2. Create the template file

- File extension: `.j2`
- Naming: `<descriptive-name>.<output-extension>.j2` (e.g., `elasticache.tf.j2`, `deploy-cache.yml.j2`)
- Template receives context: `{"config": <ProjectConfig>}`

## 3. Template content rules

- Wrap entire content in `{% if config.include_<service> %}...{% endif %}` if service-conditional.
- Access config: `{{ config.project_name }}`, `{{ config.rds.instance_class }}`.
- For GitHub Actions: escape expressions with `${{ "{{" }} ... {{ "}}" }}`.
- Use `{% for item in list %}...{% endfor %}` for iteration.
- Use `{{ value | default("fallback") }}` for optional values.

## 4. Wire into the generator

In the appropriate `*_gen.py` module:
```python
if config.include_<service>:  # only if conditional
    content = render_template(env, "<category>/<template>.j2", {"config": config})
    write_rendered(content, output_dir, "<output-subdir>", "<output-filename>")
```

## 5. Add a test

In `tests/test_generator.py`:
```python
def test_generates_<template_name>(sample_config, tmp_output_dir):
    generate_all(sample_config, str(tmp_output_dir))
    output_file = tmp_output_dir / "<output-subdir>" / "<output-filename>"
    assert output_file.exists()
    content = output_file.read_text()
    assert "<expected_content>" in content
```

## 6. Verify
```powershell
python -m pytest tests/test_generator.py -v
```
