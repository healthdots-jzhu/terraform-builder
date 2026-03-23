"""Core generation engine — orchestrates all generators."""

from __future__ import annotations

import pathlib

from rich.console import Console

from terraform_builder.models import ProjectConfig
from terraform_builder.generator.terraform_gen import generate_terraform
from terraform_builder.generator.workflow_gen import generate_workflows
from terraform_builder.generator.dockerfile_gen import generate_dockerfiles
from terraform_builder.generator.misc_gen import generate_misc

console = Console()


def generate_all(config: ProjectConfig) -> None:
    """Run all generators and produce the full output tree."""
    out = pathlib.Path(config.output_dir).resolve()
    console.print(f"\n[bold]Generating files in [cyan]{out}[/cyan]...[/bold]\n")

    generate_terraform(config, out)
    generate_workflows(config, out)
    generate_dockerfiles(config, out)
    generate_misc(config, out)

    console.print(f"\n[bold green]All files written to {out}[/bold green]")
