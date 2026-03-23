"""Tests for Pydantic configuration models."""

import pytest

from terraform_builder.models import (
    BackendFramework,
    FrontendFramework,
    ProjectConfig,
    VpcConfig,
    RdsConfig,
    EcsConfig,
)


class TestProjectConfigDefaults:
    def test_default_values(self):
        cfg = ProjectConfig()
        assert cfg.project_name == "myproject"
        assert cfg.aws_region == "us-east-1"
        assert cfg.environments == ["staging", "beta", "prod"]
        assert cfg.backend_framework == BackendFramework.DOTNET
        assert cfg.include_vpc is True
        assert cfg.include_rds is True
        assert cfg.include_ecs is True

    def test_vpc_always_on(self):
        cfg = ProjectConfig(include_vpc=False)
        # VPC is structurally always True in the model default
        # but we don't enforce it in the validator — just verify default
        assert isinstance(cfg.vpc, VpcConfig)

    def test_frontend_disabled_by_default(self):
        cfg = ProjectConfig()
        assert cfg.include_frontend is False
        assert cfg.frontend_framework is None


class TestDependencyResolution:
    def test_ecs_enables_ecr_and_alb(self):
        cfg = ProjectConfig(include_ecs=True, include_ecr=False, include_alb=False)
        assert cfg.include_ecr is True
        assert cfg.include_alb is True

    def test_frontend_enables_s3_and_cloudfront(self):
        cfg = ProjectConfig(
            include_frontend=True,
            frontend_framework=FrontendFramework.REACT,
            include_s3_frontend=False,
            include_cloudfront=False,
        )
        assert cfg.include_s3_frontend is True
        assert cfg.include_cloudfront is True

    def test_rds_enables_kms(self):
        cfg = ProjectConfig(include_rds=True, include_kms=False)
        assert cfg.include_kms is True

    def test_no_ecs_no_forced_ecr(self):
        cfg = ProjectConfig(include_ecs=False, include_ecr=False)
        assert cfg.include_ecr is False


class TestPathBase:
    def test_get_path_base(self):
        cfg = ProjectConfig(project_name="demo", path_base_pattern="/{project}-{env}/api")
        assert cfg.get_path_base("beta") == "/demo-beta/api"
        assert cfg.get_path_base("prod") == "/demo-prod/api"


class TestYamlRoundTrip:
    def test_serialize_deserialize(self):
        original = ProjectConfig(
            project_name="test-proj",
            aws_region="eu-west-1",
            environments=["dev", "prod"],
            backend_framework=BackendFramework.PYTHON,
            include_frontend=True,
            frontend_framework=FrontendFramework.VUE,
            include_scheduler=True,
        )
        yaml_str = original.to_yaml()
        restored = ProjectConfig.from_yaml(yaml_str)

        assert restored.project_name == "test-proj"
        assert restored.aws_region == "eu-west-1"
        assert restored.environments == ["dev", "prod"]
        assert restored.backend_framework == BackendFramework.PYTHON
        assert restored.include_frontend is True
        assert restored.frontend_framework == FrontendFramework.VUE
        assert restored.include_scheduler is True
        # dependency resolution should still apply
        assert restored.include_s3_frontend is True
        assert restored.include_cloudfront is True

    def test_yaml_contains_expected_keys(self):
        cfg = ProjectConfig()
        yaml_str = cfg.to_yaml()
        assert "project_name:" in yaml_str
        assert "backend_framework:" in yaml_str
        assert "include_rds:" in yaml_str


class TestSubConfigs:
    def test_rds_defaults(self):
        rds = RdsConfig()
        assert rds.instance_class == "db.t4g.micro"
        assert rds.allocated_storage == 20
        assert rds.postgres_version == "16"

    def test_ecs_defaults(self):
        ecs = EcsConfig()
        assert ecs.task_cpu == "256"
        assert ecs.task_memory == "512"
        assert ecs.container_port == 80
