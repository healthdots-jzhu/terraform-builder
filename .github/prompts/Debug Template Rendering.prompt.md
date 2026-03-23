---
agent: agent
---

# Debug Template Rendering

Use this prompt when a Jinja2 template fails to render or produces incorrect output.

## Common Errors and Fixes

### `jinja2.exceptions.UndefinedError: 'X' is undefined`
**Cause:** Template references an attribute that doesn't exist on `ProjectConfig` or a sub-config.
**Fix:**
1. Check the exact attribute name in `terraform_builder/models/__init__.py`.
2. In the template, verify the path: `config.<field>` for top-level, `config.<sub>.<field>` for sub-configs.
3. Sub-configs: `config.vpc`, `config.rds`, `config.ecs`, `config.dns`, `config.ec2`, `config.scheduler`.

### Template renders but output is wrong (extra whitespace, missing lines)
**Cause:** Jinja2 block control whitespace.
**Fix:**
- The environment uses `trim_blocks=True` and `lstrip_blocks=True` — block tags on their own line won't produce blank lines.
- For inline conditionals, use `{%- ... -%}` to strip surrounding whitespace.
- Check `keep_trailing_newline=True` ensures files end with newline.

### GitHub Actions `${{ }}` appears literally in output
**Cause:** Jinja2 is interpreting `${{ }}` as its own expression syntax.
**Fix:** Escape with: `${{ "{{" }} expression {{ "}}" }}`

### Template not being generated
**Cause:** Missing generator wiring or service toggle is off.
**Debug steps:**
1. Check if the service toggle is enabled: `config.include_<service>` must be `True`.
2. Check if the `render_template()` + `write_rendered()` call exists in the appropriate `*_gen.py`.
3. Check if the generator function is called in `engine.py`'s `generate_all()`.
4. Check the template path string matches the actual file path under `templates/`.

## Diagnostic Commands
```powershell
# Render all templates and check for errors
python -m pytest tests/test_generator.py -v -k "test_generate"

# Check a specific template attribute manually
python -c "from terraform_builder.models import ProjectConfig; c = ProjectConfig(project_name='test'); print(c.model_fields_set)"

# List all template files
Get-ChildItem -Recurse terraform_builder/templates -Filter *.j2 | Select-Object FullName
```
