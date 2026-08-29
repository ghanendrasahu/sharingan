"""Celery configuration for background task processing."""

from __future__ import annotations

from celery import Celery
from celery.signals import task_postrun, task_prerun

from app.core.config import get_settings

settings = get_settings()

# Create Celery app
celery_app = Celery(
    "legallens",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

# Configure Celery
celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    # Timeouts
    task_soft_time_limit=300,  # 5 minutes soft limit
    task_time_limit=600,  # 10 minutes hard limit
    # Retries
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    # Concurrency
    worker_concurrency=4,
    worker_prefetch_multiplier=1,
    # Results
    result_expires=3600,  # 1 hour
    # Security
    task_always_eager=False,  # Set True for testing
    # Rate limiting
    task_default_rate_limit="10/m",
    # Routing
    task_routes={
        "app.tasks.document.*": {"queue": "document_processing"},
        "app.tasks.analysis.*": {"queue": "ai_analysis"},
        "app.tasks.notification.*": {"queue": "notifications"},
    },
    # Queues
    task_queues={
        "document_processing": {
            "exchange": "document_processing",
            "routing_key": "document",
        },
        "ai_analysis": {
            "exchange": "ai_analysis",
            "routing_key": "analysis",
        },
        "notifications": {
            "exchange": "notifications",
            "routing_key": "notification",
        },
        "default": {
            "exchange": "default",
            "routing_key": "default",
        },
    },
    # Discovery
    include=["app.tasks.document", "app.tasks.analysis"],
)


@task_prerun.connect
def task_prerun_handler(sender, **kwargs):
    """Handle task start."""
    print(f"Task {sender.name} starting...")


@task_postrun.connect
def task_postrun_handler(sender, **kwargs):
    """Handle task completion."""
    print(f"Task {sender.name} completed.")
