"""Unit tests for CI/CD configuration."""

import yaml


def test_ci_workflow_exists():
    """Test that CI workflow file exists."""
    with open(".github/workflows/ci.yml") as f:
        workflow = yaml.safe_load(f)
    assert "jobs" in workflow
    assert "lint" in workflow["jobs"]
    assert "test" in workflow["jobs"]
    assert "security" in workflow["jobs"]
    assert "evaluation" in workflow["jobs"]
    assert "docker" in workflow["jobs"]


def test_deploy_workflow_exists():
    """Test that deploy workflow file exists."""
    with open(".github/workflows/deploy.yml") as f:
        workflow = yaml.safe_load(f)
    assert "jobs" in workflow
    assert "deploy-staging" in workflow["jobs"]
    assert "deploy-production" in workflow["jobs"]


def test_ci_lint_job():
    """Test CI lint job configuration."""
    with open(".github/workflows/ci.yml") as f:
        workflow = yaml.safe_load(f)
    lint_job = workflow["jobs"]["lint"]
    assert lint_job["runs-on"] == "ubuntu-latest"
    steps = [step["name"] for step in lint_job["steps"] if "name" in step]
    assert "Run Ruff check" in steps


def test_ci_test_job():
    """Test CI test job configuration."""
    with open(".github/workflows/ci.yml") as f:
        workflow = yaml.safe_load(f)
    test_job = workflow["jobs"]["test"]
    assert test_job["runs-on"] == "ubuntu-latest"
    assert test_job["needs"] == "lint"


def test_ci_security_job():
    """Test CI security job configuration."""
    with open(".github/workflows/ci.yml") as f:
        workflow = yaml.safe_load(f)
    security_job = workflow["jobs"]["security"]
    assert security_job["runs-on"] == "ubuntu-latest"
    steps = [step["name"] for step in security_job["steps"] if "name" in step]
    assert "Run Bandit (SAST)" in steps


def test_ci_docker_job():
    """Test CI Docker job configuration."""
    with open(".github/workflows/ci.yml") as f:
        workflow = yaml.safe_load(f)
    docker_job = workflow["jobs"]["docker"]
    assert docker_job["runs-on"] == "ubuntu-latest"
    assert docker_job["needs"] == ["test", "security"]


def test_deploy_staging_job():
    """Test deploy staging job configuration."""
    with open(".github/workflows/deploy.yml") as f:
        workflow = yaml.safe_load(f)
    staging_job = workflow["jobs"]["deploy-staging"]
    assert staging_job["runs-on"] == "ubuntu-latest"
    assert "environment" in staging_job


def test_deploy_production_job():
    """Test deploy production job configuration."""
    with open(".github/workflows/deploy.yml") as f:
        workflow = yaml.safe_load(f)
    prod_job = workflow["jobs"]["deploy-production"]
    assert prod_job["runs-on"] == "ubuntu-latest"
    assert prod_job["needs"] == "deploy-staging"


def test_ci_triggers():
    """Test CI workflow triggers."""
    with open(".github/workflows/ci.yml") as f:
        workflow = yaml.safe_load(f)
    # YAML treats 'on' as True boolean
    triggers = workflow.get(True, workflow.get("on", {}))
    assert "push" in triggers
    assert "pull_request" in triggers
    assert "main" in triggers["push"]["branches"]


def test_deploy_triggers():
    """Test deploy workflow triggers."""
    with open(".github/workflows/deploy.yml") as f:
        workflow = yaml.safe_load(f)
    # YAML treats 'on' as True boolean
    triggers = workflow.get(True, workflow.get("on", {}))
    assert "push" in triggers
    assert "workflow_dispatch" in triggers
