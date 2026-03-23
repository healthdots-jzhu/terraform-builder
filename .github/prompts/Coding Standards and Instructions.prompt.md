---
agent: agent
---

# Coding Standards and Instructions

Follow these rules when working on the terraform-builder project:

1. Python 3.10+ — use type hints, f-strings, and pathlib where practical.
2. Pydantic v2 — use `model_validator`, `field_validator`, `Field()` with defaults; avoid Pydantic v1 patterns.
3. Jinja2 templates use `StrictUndefined` — every `{{ config.xyz }}` must map to a real model attribute. Verify by rendering.
4. Imports in `terraform_builder/generator/` must never create circular dependencies. Generator modules import only from `base.py`; `engine.py` orchestrates them all.
5. All user-facing CLI output uses Rich for formatting. Plain `print()` is not used.
6. Tests use pytest with `@pytest.mark.parametrize` for validator tests and fixtures for generator tests.
7. Template files live under `terraform_builder/templates/<category>/` with `.j2` extension. Category is one of: `terraform`, `workflows`, `dockerfiles`, `misc`.
8. Config serialization uses PyYAML via `to_yaml()` / `from_yaml()` — never `json.dumps` for config persistence.
9. GitHub Actions expressions in workflow templates must be escaped: `${{ "{{" }} github.ref {{ "}}" }}` to avoid Jinja2 collision.
