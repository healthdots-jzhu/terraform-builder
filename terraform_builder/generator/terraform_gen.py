"""Generate Terraform HCL files from Jinja2 templates."""

from __future__ import annotations

import pathlib

from rich.console import Console

from terraform_builder.models import ProjectConfig
from terraform_builder.generator.base import render_template, write_rendered

console = Console()

# Main terraform files
_MAIN_TEMPLATES = [
    "main.tf.j2",
    "variables.tf.j2",
    "outputs.tf.j2",
    "backend.tf.j2",
]

# Sub-module directories with their template files
_SUBMODULES: dict[str, list[str]] = {
    "bootstrap_orchestration": [
        "main.tf.j2",
        "variables.tf.j2",
        "outputs.tf.j2",
        "backend.tf.j2",
        "bootstrap_environments.tfvars.j2",
    ],
    "ci_aws_oidc": [
        "main.tf.j2",
        "variables.tf.j2",
    ],
    "github_provider": [
        "provider.tf.j2",
        "main.tf.j2",
        "variables.tf.j2",
        "outputs.tf.j2",
    ],
}


def _output_name(template_name: str) -> str:
    """Strip .j2 extension to get the output filename."""
    if template_name.endswith(".j2"):
        return template_name[:-3]
    return template_name


def generate_terraform(config: ProjectConfig, output_root: pathlib.Path) -> None:
    """Render all Terraform templates into the output tree."""
    tf_dir = output_root / "terraform"
    console.print("[cyan]  Terraform files...[/cyan]")

    # --- Main .tf files ---
    for tmpl in _MAIN_TEMPLATES:
        content = render_template("terraform", tmpl, config)
        write_rendered(tf_dir / _output_name(tmpl), content)

    # --- ECS (conditional) ---
    if config.include_ecs:
        content = render_template("terraform", "ecs.tf.j2", config)
        write_rendered(tf_dir / "ecs.tf", content)

    # --- Sub-modules ---
    for submod, templates in _SUBMODULES.items():
        submod_dir = tf_dir / submod
        for tmpl in templates:
            content = render_template(f"terraform/{submod}", tmpl, config)
            write_rendered(submod_dir / _output_name(tmpl), content)

    # --- user_data.sh (conditional on EC2 bastion) ---
    if config.include_ec2_bastion:
        content = render_template("terraform", "user_data.sh.j2", config)
        write_rendered(tf_dir / "user_data.sh", content)

    # --- Lambda scheduler (conditional) ---
    if config.include_scheduler:
        content = render_template("terraform/lambda", "scheduler.py.j2", config)
        write_rendered(tf_dir / "lambda" / "scheduler.py", content)

    console.print("    [green]✓[/green] Terraform files generated")
