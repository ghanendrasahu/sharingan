"""Task status models for background processing."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum


class TaskStatus(StrEnum):
    """Task execution status."""

    PENDING = "pending"
    STARTED = "started"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRY = "retry"


class TaskType(StrEnum):
    """Types of background tasks."""

    DOCUMENT_PROCESSING = "document_processing"
    AI_ANALYSIS = "ai_analysis"
    EMBEDDING_GENERATION = "embedding_generation"
    REPORT_GENERATION = "report_generation"
    NOTIFICATION = "notification"


@dataclass
class TaskInfo:
    """Information about a background task."""

    task_id: str
    task_type: TaskType
    status: TaskStatus = TaskStatus.PENDING
    message: str = ""
    progress: float = 0.0  # 0.0 to 1.0

    # Timestamps
    created_at: str = ""
    started_at: str | None = None
    completed_at: str | None = None

    # Results
    result: dict[str, str | int | float] | None = None
    error: str | None = None
    traceback: str | None = None

    # Metadata
    document_id: str | None = None
    user_id: str | None = None
    organization_id: str | None = None

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(tz=UTC).isoformat()

    @property
    def duration_ms(self) -> float | None:
        """Calculate task duration in milliseconds."""
        if not self.started_at:
            return None

        start = datetime.fromisoformat(self.started_at)
        end = (
            datetime.fromisoformat(self.completed_at) if self.completed_at else datetime.now(tz=UTC)
        )

        return (end - start).total_seconds() * 1000

    @property
    def is_complete(self) -> bool:
        """Check if task is complete."""
        return self.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED)

    def start(self) -> None:
        """Mark task as started."""
        self.status = TaskStatus.STARTED
        self.started_at = datetime.now(tz=UTC).isoformat()

    def complete(self, result: dict[str, str | int | float] | None = None) -> None:
        """Mark task as completed."""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now(tz=UTC).isoformat()
        self.progress = 1.0
        self.result = result

    def fail(self, error: str, traceback: str | None = None) -> None:
        """Mark task as failed."""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.now(tz=UTC).isoformat()
        self.error = error
        self.traceback = traceback

    def cancel(self) -> None:
        """Mark task as cancelled."""
        self.status = TaskStatus.CANCELLED
        self.completed_at = datetime.now(tz=UTC).isoformat()

    def update_progress(self, progress: float, message: str = "") -> None:
        """Update task progress."""
        self.progress = min(max(progress, 0.0), 1.0)
        if message:
            self.message = message

    def to_dict(self) -> dict[str, str | float | dict[str, str | int | float] | None]:
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "status": self.status,
            "message": self.message,
            "progress": self.progress,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_ms": self.duration_ms,
            "result": self.result,
            "error": self.error,
            "document_id": self.document_id,
            "user_id": self.user_id,
            "organization_id": self.organization_id,
        }
