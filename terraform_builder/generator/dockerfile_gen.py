"""Generate framework-specific Dockerfiles from Jinja2 templates."""

from __future__ import annotations

import pathlib

from rich.console import Console

from terraform_builder.models import BackendFramework, ProjectConfig
from terraform_builder.generator.base import render_template, write_rendered

console = Console()

_FRAMEWORK_TEMPLATE = {
    BackendFramework.DOTNET: "Dockerfile.dotnet.j2",
    BackendFramework.NODEJS: "Dockerfile.nodejs.j2",
    BackendFramework.PYTHON: "Dockerfile.python.j2",
    BackendFramework.GO: "Dockerfile.go.j2",
}


def generate_dockerfiles(config: ProjectConfig, output_root: pathlib.Path) -> None:
    """Render the appropriate Dockerfile for the chosen backend framework."""
    if not config.include_ecs:
        return  # no container deployment → no Dockerfile needed

    console.print("[cyan]  Dockerfile...[/cyan]")
    tmpl_name = _FRAMEWORK_TEMPLATE[config.backend_framework]
    content = render_template("dockerfiles", tmpl_name, config)

    # Write to the backend app directory
    write_rendered(output_root / config.backend_app_path / "Dockerfile", content)
    console.print("    [green]✓[/green] Dockerfile generated")
