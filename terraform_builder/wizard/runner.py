"""Wizard runner — orchestrates the full interactive wizard flow."""

from __future__ import annotations

from InquirerPy import inquirer
from InquirerPy.validator import EmptyInputValidator
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from terraform_builder.models import (
    BackendFramework,
    DnsConfig,
    Ec2Config,
    EcsConfig,
    FrontendFramework,
    ProjectConfig,
    RdsConfig,
    SchedulerConfig,
    VpcConfig,
)
from terraform_builder.wizard.validators import (
    AWS_REGIONS,
    validate_cidr,
    validate_port,
    validate_project_name,
)

console = Console()


def _ask_project() -> dict:
    """Collect project-level settings."""
    console.print(Panel("[bold cyan]Project Settings[/bold cyan]"))

    project_name = inquirer.text(
        message="Project name (lowercase, hyphens allowed):",
        default="myproject",
        validate=lambda _, v: validate_project_name(v) or "Must be lowercase alphanumeric with hyphens (3-50 chars)",
    ).execute()

    aws_region = inquirer.select(
        message="AWS region:",
        choices=AWS_REGIONS,
        default="us-east-1",
    ).execute()

    environments = inquirer.checkbox(
        message="Select environments to create:",
        choices=[
            {"name": "staging", "value": "staging", "enabled": True},
            {"name": "beta", "value": "beta", "enabled": True},
            {"name": "prod", "value": "prod", "enabled": True},
        ],
        validate=lambda result: len(result) >= 1 or "Select at least one environment",
    ).execute()

    default_env = inquirer.select(
        message="Default environment for workflows:",
        choices=environments,
        default=environments[0] if environments else "beta",
    ).execute()

    return {
        "project_name": project_name,
        "aws_region": aws_region,
        "environments": environments,
        "default_environment": default_env,
    }


def _ask_backend() -> dict:
    """Collect backend framework and configuration."""
    console.print(Panel("[bold cyan]Backend Configuration[/bold cyan]"))

    framework = inquirer.select(
        message="Backend framework:",
        choices=[
            {"name": ".NET (ASP.NET Core)", "value": "dotnet"},
            {"name": "Node.js (Express / Fastify)", "value": "nodejs"},
            {"name": "Python (FastAPI / Flask)", "value": "python"},
            {"name": "Go (Gin / Echo)", "value": "go"},
        ],
        default="dotnet",
    ).execute()

    app_path = inquirer.text(
        message="Backend application path (relative to repo root):",
        default="APIs/App" if framework == "dotnet" else "backend",
    ).execute()

    path_base = inquirer.text(
        message="API path base pattern ({project} and {env} will be substituted):",
        default="/{project}-{env}/api",
    ).execute()

    return {
        "backend_framework": framework,
        "backend_app_path": app_path,
        "path_base_pattern": path_base,
    }


def _ask_frontend() -> dict:
    """Collect frontend settings."""
    console.print(Panel("[bold cyan]Frontend Configuration[/bold cyan]"))

    include = inquirer.confirm(
        message="Include a frontend (S3 + CloudFront)?",
        default=False,
    ).execute()

    result: dict = {"include_frontend": include}
    if include:
        fw = inquirer.select(
            message="Frontend framework:",
            choices=[
                {"name": "React (Vite)", "value": "react"},
                {"name": "Vue", "value": "vue"},
                {"name": "Angular", "value": "angular"},
                {"name": "Plain static", "value": "plain"},
            ],
            default="react",
        ).execute()
        result["frontend_framework"] = fw
        result["frontend_path"] = inquirer.text(
            message="Frontend directory path:",
            default="frontend",
        ).execute()

    return result


def _ask_services(has_frontend: bool) -> dict:
    """Toggle AWS services."""
    console.print(Panel("[bold cyan]AWS Services[/bold cyan]"))

    services = inquirer.checkbox(
        message="Select optional AWS services to include:",
        choices=[
            {"name": "RDS PostgreSQL (database)", "value": "include_rds", "enabled": True},
            {"name": "ECS Fargate (container orchestration)", "value": "include_ecs", "enabled": True},
            {"name": "Route53 (DNS records)", "value": "include_route53", "enabled": False},
            {"name": "KMS (encryption keys)", "value": "include_kms", "enabled": True},
            {"name": "Secrets Manager", "value": "include_secrets_manager", "enabled": True},
            {"name": "SSM Parameter Store", "value": "include_ssm", "enabled": True},
            {"name": "Cognito (auth)", "value": "include_cognito", "enabled": False},
            {"name": "DynamoDB cache table", "value": "include_dynamodb_cache", "enabled": False},
            {"name": "Lambda scheduler (start/stop resources)", "value": "include_scheduler", "enabled": False},
            {"name": "EC2 bastion host (SSM access to RDS)", "value": "include_ec2_bastion", "enabled": False},
        ],
    ).execute()

    all_service_keys = [
        "include_rds", "include_ecs", "include_route53", "include_kms",
        "include_secrets_manager", "include_ssm", "include_cognito",
        "include_dynamodb_cache", "include_scheduler", "include_ec2_bastion",
    ]
    result = {k: (k in services) for k in all_service_keys}

    # Frontend-derived services
    result["include_s3_frontend"] = has_frontend
    result["include_cloudfront"] = has_frontend

    return result


def _ask_networking() -> VpcConfig:
    """VPC and subnet CIDRs."""
    console.print(Panel("[bold cyan]Networking (VPC)[/bold cyan]"))

    use_defaults = inquirer.confirm(
        message="Use default VPC/subnet CIDRs (10.0.0.0/16)?",
        default=True,
    ).execute()

    if use_defaults:
        return VpcConfig()

    vpc_cidr = inquirer.text(
        message="VPC CIDR:", default="10.0.0.0/16",
        validate=lambda _, v: validate_cidr(v) or "Invalid CIDR",
    ).execute()
    pub1 = inquirer.text(
        message="Public subnet 1a CIDR:", default="10.0.0.0/20",
        validate=lambda _, v: validate_cidr(v) or "Invalid CIDR",
    ).execute()
    pub2 = inquirer.text(
        message="Public subnet 1b CIDR:", default="10.0.16.0/24",
        validate=lambda _, v: validate_cidr(v) or "Invalid CIDR",
    ).execute()
    priv = inquirer.text(
        message="Private subnet CIDR:", default="10.0.128.0/20",
        validate=lambda _, v: validate_cidr(v) or "Invalid CIDR",
    ).execute()
    priv2a = inquirer.text(
        message="Private 2a CIDR:", default="10.0.144.0/20",
        validate=lambda _, v: validate_cidr(v) or "Invalid CIDR",
    ).execute()
    priv2b = inquirer.text(
        message="Private 2b CIDR:", default="10.0.160.0/20",
        validate=lambda _, v: validate_cidr(v) or "Invalid CIDR",
    ).execute()

    return VpcConfig(
        vpc_cidr=vpc_cidr,
        public_subnet_cidr=pub1,
        public_2b_cidr=pub2,
        private_subnet_cidr=priv,
        private_2a_cidr=priv2a,
        private_2b_cidr=priv2b,
    )


def _ask_database() -> RdsConfig:
    console.print(Panel("[bold cyan]Database (RDS PostgreSQL)[/bold cyan]"))

    use_defaults = inquirer.confirm(
        message="Use default RDS settings (db.t4g.micro, 20 GB, Postgres 16)?",
        default=True,
    ).execute()

    if use_defaults:
        return RdsConfig()

    return RdsConfig(
        instance_class=inquirer.text(message="Instance class:", default="db.t4g.micro").execute(),
        allocated_storage=int(inquirer.text(message="Allocated storage (GB):", default="20").execute()),
        postgres_version=inquirer.text(message="PostgreSQL version:", default="16").execute(),
        database_name=inquirer.text(
            message="Database name:", default="appdb",
            validate=EmptyInputValidator("Required"),
        ).execute(),
        username=inquirer.text(message="Master username:", default="postgres").execute(),
        multi_az=inquirer.confirm(message="Multi-AZ?", default=False).execute(),
    )


def _ask_ecs() -> EcsConfig:
    console.print(Panel("[bold cyan]ECS Fargate[/bold cyan]"))

    use_defaults = inquirer.confirm(
        message="Use default ECS settings (256 CPU, 512 MB, 1 task)?",
        default=True,
    ).execute()

    if use_defaults:
        return EcsConfig()

    return EcsConfig(
        task_cpu=inquirer.select(
            message="Task CPU units:", choices=["256", "512", "1024", "2048", "4096"],
            default="256",
        ).execute(),
        task_memory=inquirer.select(
            message="Task memory (MB):", choices=["512", "1024", "2048", "4096", "8192"],
            default="512",
        ).execute(),
        desired_count=int(inquirer.text(message="Desired task count:", default="1").execute()),
        container_port=int(inquirer.text(
            message="Container port:", default="80",
            validate=lambda _, v: validate_port(v) or "Invalid port",
        ).execute()),
        health_check_path=inquirer.text(message="Health check path:", default="/api/v1/health").execute(),
    )


def _ask_dns() -> DnsConfig:
    console.print(Panel("[bold cyan]DNS (Route53)[/bold cyan]"))
    zone = inquirer.text(
        message="Route53 hosted zone name (e.g., example.com):",
        validate=EmptyInputValidator("Required"),
    ).execute()
    subdomain = inquirer.text(message="API subdomain:", default="api").execute()
    return DnsConfig(route53_zone_name=zone, api_subdomain=subdomain)


def _ask_output_dir() -> str:
    return inquirer.text(
        message="Output directory for generated files:",
        default=".",
        validate=EmptyInputValidator("Required"),
    ).execute()


def _print_summary(config: ProjectConfig) -> None:
    """Display a summary table of selected options."""
    table = Table(title="Configuration Summary", show_lines=True)
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Project", config.project_name)
    table.add_row("Region", config.aws_region)
    table.add_row("Environments", ", ".join(config.environments))
    table.add_row("Backend", config.backend_framework.value)
    table.add_row("Frontend", config.frontend_framework.value if config.include_frontend else "none")

    services = []
    for attr in [
        "include_rds", "include_ecs", "include_alb", "include_ecr",
        "include_route53", "include_kms", "include_secrets_manager",
        "include_ssm", "include_cognito", "include_dynamodb_cache",
        "include_scheduler", "include_ec2_bastion", "include_s3_frontend",
        "include_cloudfront",
    ]:
        if getattr(config, attr):
            services.append(attr.replace("include_", "").replace("_", " ").upper())
    table.add_row("AWS Services", ", ".join(services))
    table.add_row("Output Dir", config.output_dir)

    console.print(table)


def run_wizard() -> ProjectConfig:
    """Run the full interactive wizard and return a ProjectConfig."""
    console.print(Panel.fit(
        "[bold green]Terraform Builder[/bold green]\n"
        "Generate production-ready Terraform + GitHub Actions for AWS",
        border_style="green",
    ))

    # Collect all sections
    project_data = _ask_project()
    backend_data = _ask_backend()
    frontend_data = _ask_frontend()
    services_data = _ask_services(frontend_data.get("include_frontend", False))

    # Conditional sub-configs
    vpc_config = _ask_networking()

    rds_config = _ask_database() if services_data.get("include_rds") else RdsConfig()
    ecs_config = _ask_ecs() if services_data.get("include_ecs") else EcsConfig()
    dns_config = _ask_dns() if services_data.get("include_route53") else DnsConfig()

    output_dir = _ask_output_dir()

    # Build config
    config = ProjectConfig(
        **project_data,
        **backend_data,
        **frontend_data,
        **services_data,
        vpc=vpc_config,
        rds=rds_config,
        ecs=ecs_config,
        dns=dns_config,
        output_dir=output_dir,
    )

    _print_summary(config)

    proceed = inquirer.confirm(message="Generate files with this configuration?", default=True).execute()
    if not proceed:
        console.print("[yellow]Aborted.[/yellow]")
        raise SystemExit(0)

    return config
