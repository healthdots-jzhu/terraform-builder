"""Generate miscellaneous project files (README, .gitignore, docker-compose, .env.example)."""

from __future__ import annotations

import pathlib

from rich.console import Console

from terraform_builder.models import ProjectConfig
from terraform_builder.generator.base import render_template, write_rendered

console = Console()


def generate_misc(config: ProjectConfig, output_root: pathlib.Path) -> None:
    """Render miscellaneous project scaffolding files."""
    console.print("[cyan]  Miscellaneous files...[/cyan]")

    # .gitignore
    content = render_template("misc", "gitignore.j2", config)
    write_rendered(output_root / ".gitignore", content)

    # .env.example
    content = render_template("misc", "env.example.j2", config)
    write_rendered(output_root / ".env.example", content)

    # docker-compose.yml (only if ECS/containers are used)
    if config.include_ecs:
        content = render_template("misc", "docker-compose.yml.j2", config)
        write_rendered(output_root / "docker-compose.yml", content)

    # README.md
    content = render_template("misc", "README.md.j2", config)
    write_rendered(output_root / "README.md", content)

    console.print("    [green]✓[/green] Miscellaneous files generated")
