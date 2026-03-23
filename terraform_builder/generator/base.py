"""Shared Jinja2 rendering utilities used by all generators."""

from __future__ import annotations

import pathlib

import jinja2

from terraform_builder.models import ProjectConfig

TEMPLATES_DIR = pathlib.Path(__file__).resolve().parent.parent / "templates"


def _create_jinja_env(template_subdir: str) -> jinja2.Environment:
    """Create a Jinja2 environment rooted at a template subdirectory."""
    loader = jinja2.FileSystemLoader(str(TEMPLATES_DIR / template_subdir))
    return jinja2.Environment(
        loader=loader,
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
        undefined=jinja2.StrictUndefined,
    )


def render_template(template_subdir: str, template_name: str, config: ProjectConfig) -> str:
    """Render a single Jinja2 template and return the result string."""
    env = _create_jinja_env(template_subdir)
    tmpl = env.get_template(template_name)
    return tmpl.render(config=config)


def write_rendered(output_path: pathlib.Path, content: str) -> None:
    """Write rendered content to a file, creating parent dirs as needed."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
