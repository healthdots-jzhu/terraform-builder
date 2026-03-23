"""Tests for the Jinja2 template rendering engine and generators."""

import pathlib
import tempfile

import pytest

from terraform_builder.models import (
    BackendFramework,
    FrontendFramework,
    ProjectConfig,
)
from terraform_builder.generator.base import render_template, TEMPLATES_DIR


class TestRenderTemplate:
    """Test that templates render without Jinja2 errors."""

    @pytest.fixture
    def default_config(self):
        return ProjectConfig()

    @pytest.fixture
    def full_config(self):
        return ProjectConfig(
            project_name="fulltest",
            aws_region="us-west-2",
            environments=["dev", "staging", "prod"],
            backend_framework=BackendFramework.DOTNET,
            include_frontend=True,
            frontend_framework=FrontendFramework.REACT,
            include_rds=True,
            include_ecs=True,
            include_route53=True,
            include_cognito=True,
            include_dynamodb_cache=True,
            include_ec2_bastion=True,
            include_scheduler=True,
        )

    @pytest.fixture
    def minimal_config(self):
        return ProjectConfig(
            project_name="minimal",
            include_rds=False,
            include_ecs=False,
            include_ecr=False,
            include_alb=False,
            include_ec2_bastion=False,
            include_scheduler=False,
            include_dynamodb_cache=False,
            include_cognito=False,
            include_route53=False,
        )

    # --- Terraform templates ---
    @pytest.mark.parametrize("template", [
        "main.tf.j2",
        "variables.tf.j2",
        "outputs.tf.j2",
        "backend.tf.j2",
    ])
    def test_main_terraform_templates_render(self, full_config, template):
        result = render_template("terraform", template, full_config)
        assert len(result) > 0
        assert "terraform" in result.lower() or "variable" in result.lower() or "output" in result.lower()

    def test_ecs_template_renders(self, full_config):
        result = render_template("terraform", "ecs.tf.j2", full_config)
        assert "aws_ecs_cluster" in result
        assert "aws_lb" in result

    def test_main_tf_minimal_no_ecs(self, minimal_config):
        result = render_template("terraform", "main.tf.j2", minimal_config)
        assert "aws_vpc" in result
        # Should NOT contain ECS resources (those are in ecs.tf)
        assert "aws_ecs_cluster" not in result

    def test_user_data_renders(self, full_config):
        result = render_template("terraform", "user_data.sh.j2", full_config)
        assert "#!/bin/bash" in result

    def test_lambda_scheduler_renders(self, full_config):
        result = render_template("terraform/lambda", "scheduler.py.j2", full_config)
        assert "def handler" in result

    # --- Bootstrap orchestration templates ---
    @pytest.mark.parametrize("template", [
        "main.tf.j2",
        "variables.tf.j2",
        "outputs.tf.j2",
        "backend.tf.j2",
        "bootstrap_environments.tfvars.j2",
    ])
    def test_bootstrap_templates_render(self, full_config, template):
        result = render_template("terraform/bootstrap_orchestration", template, full_config)
        assert len(result) > 0

    # --- CI OIDC templates ---
    @pytest.mark.parametrize("template", ["main.tf.j2", "variables.tf.j2"])
    def test_ci_oidc_templates_render(self, full_config, template):
        result = render_template("terraform/ci_aws_oidc", template, full_config)
        assert len(result) > 0

    # --- GitHub provider templates ---
    @pytest.mark.parametrize("template", [
        "provider.tf.j2", "main.tf.j2", "variables.tf.j2", "outputs.tf.j2",
    ])
    def test_github_provider_templates_render(self, full_config, template):
        result = render_template("terraform/github_provider", template, full_config)
        assert len(result) > 0

    # --- Workflow templates ---
    @pytest.mark.parametrize("template", [
        "0.1-onetime-provision-terraform-backend.yml.j2",
        "0.2-onetime-provision-github-oidc-secrets-variables.yml.j2",
        "1-deploy-infra.yml.j2",
        "2-backend-build-and-push.yml.j2",
        "4-destroy-infra-keep-rds.yml.j2",
        "5-recreate-infra.yml.j2",
    ])
    def test_workflow_templates_render(self, full_config, template):
        result = render_template("workflows", template, full_config)
        assert "name:" in result
        assert "on:" in result or "workflow_dispatch" in result

    def test_frontend_workflow_renders(self, full_config):
        result = render_template("workflows", "3-frontend-deploy.yml.j2", full_config)
        assert "name:" in result

    # --- Dockerfile templates ---
    @pytest.mark.parametrize("framework,template", [
        (BackendFramework.DOTNET, "Dockerfile.dotnet.j2"),
        (BackendFramework.NODEJS, "Dockerfile.nodejs.j2"),
        (BackendFramework.PYTHON, "Dockerfile.python.j2"),
        (BackendFramework.GO, "Dockerfile.go.j2"),
    ])
    def test_dockerfile_renders(self, framework, template):
        cfg = ProjectConfig(backend_framework=framework)
        result = render_template("dockerfiles", template, cfg)
        assert "FROM" in result
        assert "EXPOSE" in result

    # --- Misc templates ---
    @pytest.mark.parametrize("template", [
        "gitignore.j2",
        "env.example.j2",
        "docker-compose.yml.j2",
        "README.md.j2",
    ])
    def test_misc_templates_render(self, full_config, template):
        result = render_template("misc", template, full_config)
        assert len(result) > 0

    # --- Minimal config still renders without errors ---
    @pytest.mark.parametrize("template", [
        "main.tf.j2",
        "variables.tf.j2",
        "outputs.tf.j2",
        "backend.tf.j2",
    ])
    def test_minimal_config_renders(self, minimal_config, template):
        result = render_template("terraform", template, minimal_config)
        assert len(result) > 0


class TestGenerateAll:
    """Integration test: generate_all writes expected directory structure."""

    def test_generate_all_creates_files(self):
        from terraform_builder.generator import generate_all

        config = ProjectConfig(
            project_name="integ-test",
            environments=["dev"],
            include_ecs=True,
            include_rds=True,
            include_ec2_bastion=True,
            include_scheduler=True,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = tmpdir
            generate_all(config)

            base = pathlib.Path(tmpdir)

            # Terraform files
            assert (base / "terraform" / "main.tf").exists()
            assert (base / "terraform" / "variables.tf").exists()
            assert (base / "terraform" / "outputs.tf").exists()
            assert (base / "terraform" / "backend.tf").exists()
            assert (base / "terraform" / "ecs.tf").exists()
            assert (base / "terraform" / "user_data.sh").exists()
            assert (base / "terraform" / "lambda" / "scheduler.py").exists()

            # Sub-modules
            assert (base / "terraform" / "bootstrap_orchestration" / "main.tf").exists()
            assert (base / "terraform" / "ci_aws_oidc" / "main.tf").exists()
            assert (base / "terraform" / "github_provider" / "main.tf").exists()

            # Workflows
            assert (base / ".github" / "workflows" / "1-deploy-infra.yml").exists()
            assert (base / ".github" / "workflows" / "2-backend-build-and-push.yml").exists()

            # Misc
            assert (base / ".gitignore").exists()
            assert (base / ".env.example").exists()
            assert (base / "docker-compose.yml").exists()
            assert (base / "README.md").exists()

            # Dockerfile
            assert (base / "APIs" / "App" / "Dockerfile").exists()

    def test_generate_minimal_no_ecs(self):
        from terraform_builder.generator import generate_all

        config = ProjectConfig(
            project_name="minimal-test",
            environments=["dev"],
            include_ecs=False,
            include_ecr=False,
            include_alb=False,
            include_rds=False,
            include_kms=False,
            include_ec2_bastion=False,
            include_scheduler=False,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = tmpdir
            generate_all(config)

            base = pathlib.Path(tmpdir)

            # Core Terraform should always exist
            assert (base / "terraform" / "main.tf").exists()

            # ECS-specific files should NOT exist
            assert not (base / "terraform" / "ecs.tf").exists()
            assert not (base / "terraform" / "user_data.sh").exists()
            assert not (base / "terraform" / "lambda" / "scheduler.py").exists()

            # No Dockerfile without ECS
            assert not (base / "APIs" / "App" / "Dockerfile").exists()

            # No docker-compose without ECS
            assert not (base / "docker-compose.yml").exists()
