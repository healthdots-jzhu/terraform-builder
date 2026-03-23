"""Generate GitHub Actions workflow YAML files from Jinja2 templates."""

from __future__ import annotations

import pathlib

from rich.console import Console

from terraform_builder.models import ProjectConfig
from terraform_builder.generator.base import render_template, write_rendered

console = Console()

# Workflow templates in rendering order — all are always generated
_ALWAYS_WORKFLOWS = [
    "0.1-onetime-provision-terraform-backend.yml.j2",
    "0.2-onetime-provision-github-oidc-secrets-variables.yml.j2",
    "1-deploy-infra.yml.j2",
]

# Workflows conditional on specific service flags
_CONDITIONAL_WORKFLOWS = [
    # (template_name, condition_fn)
    ("2-backend-build-and-push.yml.j2", lambda c: c.include_ecs),
    ("3-frontend-deploy.yml.j2", lambda c: c.include_frontend),
    ("4-destroy-infra-keep-rds.yml.j2", lambda c: True),  # always useful
    ("5-recreate-infra.yml.j2", lambda c: True),
]


def _output_name(template_name: str) -> str:
    if template_name.endswith(".j2"):
        return template_name[:-3]
    return template_name


def generate_workflows(config: ProjectConfig, output_root: pathlib.Path) -> None:
    """Render workflow templates into .github/workflows/."""
    wf_dir = output_root / ".github" / "workflows"
    console.print("[cyan]  GitHub Actions workflows...[/cyan]")

    for tmpl in _ALWAYS_WORKFLOWS:
        content = render_template("workflows", tmpl, config)
        write_rendered(wf_dir / _output_name(tmpl), content)

    for tmpl, condition in _CONDITIONAL_WORKFLOWS:
        if condition(config):
            content = render_template("workflows", tmpl, config)
            write_rendered(wf_dir / _output_name(tmpl), content)

    console.print("    [green]✓[/green] Workflow files generated")
