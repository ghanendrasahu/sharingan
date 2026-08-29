"""Task monitoring and status service."""

from __future__ import annotations

from typing import Any

from app.core.celery_config import celery_app
from app.models.task import TaskInfo, TaskStatus, TaskType


class TaskMonitor:
    """Monitor and manage background tasks."""

    @staticmethod
    async def get_task_status(task_id: str) -> TaskInfo | None:
        """Get status of a task by ID."""
        try:
            result = celery_app.AsyncResult(task_id)

            if result.state == "PENDING":
                return TaskInfo(
                    task_id=task_id,
                    task_type=TaskType.DOCUMENT_PROCESSING,
                    status=TaskStatus.PENDING,
                    message="Task is pending",
                )
            elif result.state == "STARTED":
                meta = result.info or {}
                return TaskInfo(
                    task_id=task_id,
                    task_type=meta.get("task_type", TaskType.DOCUMENT_PROCESSING),
                    status=TaskStatus.STARTED,
                    message=meta.get("message", "Task started"),
                    progress=meta.get("progress", 0.0),
                )
            elif result.state == "SUCCESS":
                meta = result.info or {}
                return TaskInfo(
                    task_id=task_id,
                    task_type=meta.get("task_type", TaskType.DOCUMENT_PROCESSING),
                    status=TaskStatus.COMPLETED,
                    message="Task completed",
                    progress=1.0,
                    result=meta.get("result"),
                )
            elif result.state == "FAILURE":
                meta = result.info or {}
                return TaskInfo(
                    task_id=task_id,
                    task_type=TaskType.DOCUMENT_PROCESSING,
                    status=TaskStatus.FAILED,
                    error=str(meta.get("error", "Unknown error")),
                )
            else:
                return TaskInfo(
                    task_id=task_id,
                    task_type=TaskType.DOCUMENT_PROCESSING,
                    status=TaskStatus.PENDING,
                    message=f"State: {result.state}",
                )
        except Exception:
            return None

    @staticmethod
    async def cancel_task(task_id: str) -> bool:
        """Cancel a running task."""
        try:
            celery_app.control.revoke(task_id, terminate=True)
            return True
        except Exception:
            return False

    @staticmethod
    async def get_queue_stats() -> dict[str, Any]:
        """Get statistics for all queues."""
        try:
            inspect = celery_app.control.inspect()
            active = inspect.active() or {}
            scheduled = inspect.scheduled() or {}
            reserved = inspect.reserved() or {}

            return {
                "active_tasks": sum(len(tasks) for tasks in active.values()),
                "scheduled_tasks": sum(len(tasks) for tasks in scheduled.values()),
                "reserved_tasks": sum(len(tasks) for tasks in reserved.values()),
                "workers": list(active.keys()),
            }
        except Exception:
            return {
                "active_tasks": 0,
                "scheduled_tasks": 0,
                "reserved_tasks": 0,
                "workers": [],
            }

    @staticmethod
    async def get_worker_stats() -> dict[str, Any]:
        """Get worker statistics."""
        try:
            inspect = celery_app.control.inspect()
            stats = inspect.stats() or {}

            return {
                "workers": {
                    name: {
                        "status": "online",
                        "pool": stat.get("pool", {}).get("implementation", "unknown"),
                        "processed": stat.get("total", 0),
                    }
                    for name, stat in stats.items()
                }
            }
        except Exception:
            return {"workers": {}}
