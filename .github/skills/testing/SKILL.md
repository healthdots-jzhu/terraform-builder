---
name: testing
description: Guidance for writing and maintaining pytest coverage for models, validators, and generation flow in terraform-builder.
applyTo: "tests/**"
---

# Testing Skill

You are working on tests for the terraform-builder project. Tests live in `tests/` using pytest.

## Test Files

| File | Covers |
| --- | --- |
| `test_models.py` | ProjectConfig, sub-configs, enums, YAML round-trip, dependency resolution, validation |
| `test_validators.py` | CIDR, project name, port number validators |
| `test_generator.py` | Template rendering, file generation, conditional inclusion |

## Common Fixtures (in `test_generator.py`)

- `sample_config` - Full `ProjectConfig` fixture with all services enabled
- `tmp_output_dir` - `tmp_path` based output directory

## Test Patterns

### Model Tests
```python
def test_dependency_resolution():
    config = ProjectConfig(project_name="test", include_ecs=True)
    assert config.include_ecr is True   # auto-enabled
    assert config.include_alb is True   # auto-enabled
```

### Validator Tests
```python
@pytest.mark.parametrize("value,expected", [
    ("10.0.0.0/16", True),
    ("invalid", False),
])
def test_cidr_validator(value, expected):
    assert is_valid_cidr(value) == expected
```

### Generator Tests
```python
def test_generates_main_tf(sample_config, tmp_output_dir):
    generate_all(sample_config, str(tmp_output_dir))
    main_tf = tmp_output_dir / "terraform" / "main.tf"
    assert main_tf.exists()
    content = main_tf.read_text()
    assert sample_config.project_name in content
```

### Template Attribute Tests
```python
def test_template_uses_valid_attributes(sample_config, tmp_output_dir):
    """Render all templates - StrictUndefined will raise on missing attributes."""
    generate_all(sample_config, str(tmp_output_dir))
    # If no UndefinedError is raised, all template attributes are valid
```

## Rules

1. **Every new model field** needs a test in `test_models.py` covering default value, YAML round-trip, and dependency impact.
2. **Every new template** needs a generator test verifying the file is created and contains expected content.
3. **Use `@pytest.mark.parametrize`** for validators and enum-based tests.
4. **Template rendering tests** implicitly validate attribute names via `StrictUndefined`.
5. **Run tests:** `python -m pytest tests/ -v` (all) or `python -m pytest tests/test_<module>.py -v` (focused).
6. **Coverage:** `python -m pytest tests/ --cov=terraform_builder --cov-report=term-missing`.
