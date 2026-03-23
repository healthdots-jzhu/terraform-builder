"""Pydantic configuration models for terraform-builder."""

from __future__ import annotations

from enum import Enum
from typing import Optional

import yaml
from pydantic import BaseModel, Field, model_validator


class BackendFramework(str, Enum):
    DOTNET = "dotnet"
    NODEJS = "nodejs"
    PYTHON = "python"
    GO = "go"


class FrontendFramework(str, Enum):
    REACT = "react"
    VUE = "vue"
    ANGULAR = "angular"
    PLAIN = "plain"


class VpcConfig(BaseModel):
    vpc_cidr: str = "10.0.0.0/16"
    public_subnet_cidr: str = "10.0.0.0/20"
    public_2b_cidr: str = "10.0.16.0/24"
    private_subnet_cidr: str = "10.0.128.0/20"
    private_2a_cidr: str = "10.0.144.0/20"
    private_2b_cidr: str = "10.0.160.0/20"


class RdsConfig(BaseModel):
    instance_class: str = "db.t4g.micro"
    allocated_storage: int = 20
    postgres_version: str = "16"
    database_name: str = "appdb"
    username: str = "postgres"
    storage_type: str = "gp2"
    skip_final_snapshot: bool = True
    backup_retention_period: int = 7
    multi_az: bool = False


class EcsConfig(BaseModel):
    task_cpu: str = "256"
    task_memory: str = "512"
    desired_count: int = 1
    container_port: int = 80
    health_check_path: str = "/api/v1/health"


class DnsConfig(BaseModel):
    route53_zone_name: str = ""
    api_subdomain: str = "api"


class Ec2Config(BaseModel):
    instance_type: str = "t4g.micro"


class SchedulerConfig(BaseModel):
    stop_cron: str = "cron(0 5 * * ? *)"
    start_cron: str = "cron(0 14 ? * MON-FRI *)"


class ProjectConfig(BaseModel):
    """Root configuration model capturing all wizard responses."""

    # Project basics
    project_name: str = "myproject"
    aws_region: str = "us-east-1"
    environments: list[str] = Field(default_factory=lambda: ["staging", "beta", "prod"])
    default_environment: str = "beta"

    # Backend
    backend_framework: BackendFramework = BackendFramework.DOTNET
    backend_app_path: str = "APIs/App"
    path_base_pattern: str = "/{project}-{env}/api"

    # Frontend
    include_frontend: bool = False
    frontend_framework: Optional[FrontendFramework] = None
    frontend_path: str = "frontend"

    # --- AWS service toggles ---
    include_vpc: bool = True  # always on
    include_rds: bool = True
    include_ecs: bool = True
    include_alb: bool = True
    include_route53: bool = False
    include_ecr: bool = True
    include_s3_frontend: bool = False
    include_cloudfront: bool = False
    include_kms: bool = True
    include_secrets_manager: bool = True
    include_ssm: bool = True
    include_cognito: bool = False
    include_dynamodb_cache: bool = False
    include_scheduler: bool = False
    include_ec2_bastion: bool = False

    # Sub-configs
    vpc: VpcConfig = Field(default_factory=VpcConfig)
    rds: RdsConfig = Field(default_factory=RdsConfig)
    ecs: EcsConfig = Field(default_factory=EcsConfig)
    dns: DnsConfig = Field(default_factory=DnsConfig)
    ec2: Ec2Config = Field(default_factory=Ec2Config)
    scheduler: SchedulerConfig = Field(default_factory=SchedulerConfig)

    # Output
    output_dir: str = "."

    @model_validator(mode="after")
    def resolve_dependencies(self) -> "ProjectConfig":
        """Auto-enable services implied by other selections."""
        if self.include_ecs:
            self.include_ecr = True
            self.include_alb = True
        if self.include_frontend:
            self.include_s3_frontend = True
            self.include_cloudfront = True
        if self.include_rds:
            self.include_kms = True
        if self.include_route53:
            self.include_alb = True
        if self.include_scheduler and (self.include_ec2_bastion or self.include_rds):
            pass  # scheduler makes sense with compute resources
        return self

    def get_path_base(self, env: str) -> str:
        return self.path_base_pattern.replace("{project}", self.project_name).replace("{env}", env)

    def to_yaml(self) -> str:
        return yaml.dump(self.model_dump(mode="json"), default_flow_style=False, sort_keys=False)

    @classmethod
    def from_yaml(cls, text: str) -> "ProjectConfig":
        data = yaml.safe_load(text)
        return cls.model_validate(data)
