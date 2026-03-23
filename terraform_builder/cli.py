"""CLI entry point for terraform-builder."""

from __future__ import annotations

import pathlib
import sys

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from terraform_builder.models import ProjectConfig

console = Console()


@click.group()
@click.version_option(package_name="terraform-builder")
def main() -> None:
    """Terraform Builder — generate AWS infrastructure from templates."""


@main.command()
@click.option(
    "--output", "-o", "output_dir",
    default=".",
    help="Output directory for generated files.",
)
@click.option(
    "--config-out", "config_out",
    default="terraform-builder.yaml",
    help="Path to save the configuration YAML for later re-generation.",
)
def init(output_dir: str, config_out: str) -> None:
    """Run the interactive wizard and generate Terraform + workflow files."""
    from terraform_builder.wizard import run_wizard
    from terraform_builder.generator import generate_all

    config = run_wizard()
    if output_dir != ".":
        config.output_dir = output_dir

    # Save config for reproducibility
    cfg_path = pathlib.Path(config_out)
    cfg_path.write_text(config.to_yaml(), encoding="utf-8")
    console.print(f"[dim]Configuration saved to {cfg_path}[/dim]")

    generate_all(config)
    console.print("[bold green]Done! Files generated successfully.[/bold green]")


@main.command()
@click.option(
    "--config", "-c", "config_path",
    required=True,
    type=click.Path(exists=True),
    help="Path to terraform-builder.yaml config.",
)
def generate(config_path: str) -> None:
    """Re-generate files from a saved configuration (skip wizard)."""
    from terraform_builder.generator import generate_all

    text = pathlib.Path(config_path).read_text(encoding="utf-8")
    config = ProjectConfig.from_yaml(text)
    generate_all(config)
    console.print("[bold green]Done! Files re-generated successfully.[/bold green]")


@main.command("list-services")
def list_services() -> None:
    """Show all available AWS service modules."""
    table = Table(title="Available AWS Service Modules")
    table.add_column("Service", style="cyan")
    table.add_column("Description")
    table.add_column("Default", style="green")

    rows = [
        ("VPC", "Virtual Private Cloud with public/private subnets", "Always on"),
        ("RDS PostgreSQL", "Managed PostgreSQL database with KMS encryption", "On"),
        ("ECS Fargate", "Container orchestration (auto-enables ECR + ALB)", "On"),
        ("ALB", "Application Load Balancer with HTTPS", "Auto (ECS)"),
        ("ECR", "Elastic Container Registry for Docker images", "Auto (ECS)"),
        ("Route53", "DNS records for API subdomain", "Off"),
        ("KMS", "Customer-managed encryption keys", "On"),
        ("Secrets Manager", "Store database credentials and API tokens", "On"),
        ("SSM Parameter Store", "Store configuration parameters (SecureString)", "On"),
        ("Cognito", "User authentication and authorization", "Off"),
        ("DynamoDB Cache", "Pay-per-request cache table with TTL", "Off"),
        ("Lambda Scheduler", "Start/stop EC2 + RDS on schedule (cost savings)", "Off"),
        ("EC2 Bastion", "SSM-managed bastion host for RDS access", "Off"),
        ("S3 Frontend", "S3 bucket for static frontend assets", "Auto (frontend)"),
        ("CloudFront", "CDN distribution for frontend", "Auto (frontend)"),
    ]
    for name, desc, default in rows:
        table.add_row(name, desc, default)

    console.print(table)


if __name__ == "__main__":
    main()
