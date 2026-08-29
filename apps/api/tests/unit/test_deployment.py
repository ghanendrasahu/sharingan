"""Unit tests for production deployment configuration."""

import yaml


def test_prod_compose_exists():
    """Test that production compose file exists."""
    with open("docker-compose.prod.yml") as f:
        compose = yaml.safe_load(f)
    assert "services" in compose
    assert "api" in compose["services"]
    assert "web" in compose["services"]
    assert "db" in compose["services"]
    assert "redis" in compose["services"]
    assert "worker" in compose["services"]


def test_api_dockerfile():
    """Test API production Dockerfile."""
    with open("apps/api/Dockerfile") as f:
        content = f.read()
    assert "python:3.11-slim" in content
    assert "HEALTHCHECK" in content
    assert "EXPOSE 8000" in content


def test_web_dockerfile():
    """Test Web production Dockerfile."""
    with open("apps/web/Dockerfile") as f:
        content = f.read()
    assert "node:22-alpine" in content
    assert "HEALTHCHECK" in content
    assert "EXPOSE 80" in content


def test_nginx_config():
    """Test nginx configuration."""
    with open("apps/web/nginx.conf") as f:
        content = f.read()
    assert "listen 80" in content
    assert "X-Frame-Options" in content
    assert "gzip on" in content


def test_prod_compose_services():
    """Test production compose services."""
    with open("docker-compose.prod.yml") as f:
        compose = yaml.safe_load(f)
    services = compose["services"]

    assert "api" in services
    assert "web" in services
    assert "worker" in services
    assert "db" in services
    assert "redis" in services
    assert "minio" in services


def test_prod_compose_volumes():
    """Test production compose volumes."""
    with open("docker-compose.prod.yml") as f:
        compose = yaml.safe_load(f)
    volumes = compose.get("volumes", {})

    assert "postgres_data" in volumes
    assert "redis_data" in volumes
    assert "minio_data" in volumes


def test_prod_compose_healthchecks():
    """Test production compose healthchecks."""
    with open("docker-compose.prod.yml") as f:
        compose = yaml.safe_load(f)

    for service_name in ["api", "web", "db", "redis", "minio"]:
        service = compose["services"][service_name]
        assert "healthcheck" in service, f"Missing healthcheck for {service_name}"


def test_env_example_exists():
    """Test that .env.example exists."""
    with open(".env.example") as f:
        content = f.read()
    assert "POSTGRES_PASSWORD" in content
    assert "SECRET_KEY" in content
    assert "OPENAI_API_KEY" in content


def test_backup_script_exists():
    """Test that backup script exists."""
    with open("scripts/backup.sh") as f:
        content = f.read()
    assert "pg_dump" in content
    assert "BACKUP_DIR" in content
