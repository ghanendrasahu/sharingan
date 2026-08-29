"""Unit tests for background task processing."""

from app.models.task import TaskInfo, TaskStatus, TaskType


def test_task_status_enum():
    """Test task status enum values."""
    assert TaskStatus.PENDING == "pending"
    assert TaskStatus.COMPLETED == "completed"
    assert TaskStatus.FAILED == "failed"


def test_task_type_enum():
    """Test task type enum values."""
    assert TaskType.DOCUMENT_PROCESSING == "document_processing"
    assert TaskType.AI_ANALYSIS == "ai_analysis"


def test_task_info_creation():
    """Test task info model creation."""
    task = TaskInfo(
        task_id="task-123",
        task_type=TaskType.DOCUMENT_PROCESSING,
    )
    assert task.task_id == "task-123"
    assert task.status == TaskStatus.PENDING
    assert task.created_at != ""


def test_task_info_start():
    """Test starting a task."""
    task = TaskInfo(
        task_id="task-123",
        task_type=TaskType.DOCUMENT_PROCESSING,
    )
    task.start()
    assert task.status == TaskStatus.STARTED
    assert task.started_at is not None


def test_task_info_complete():
    """Test completing a task."""
    task = TaskInfo(
        task_id="task-123",
        task_type=TaskType.DOCUMENT_PROCESSING,
    )
    task.start()
    task.complete(result={"pages": 5})
    assert task.status == TaskStatus.COMPLETED
    assert task.completed_at is not None
    assert task.progress == 1.0
    assert task.result == {"pages": 5}


def test_task_info_fail():
    """Test failing a task."""
    task = TaskInfo(
        task_id="task-123",
        task_type=TaskType.DOCUMENT_PROCESSING,
    )
    task.start()
    task.fail(error="Processing failed")
    assert task.status == TaskStatus.FAILED
    assert task.error == "Processing failed"


def test_task_info_cancel():
    """Test cancelling a task."""
    task = TaskInfo(
        task_id="task-123",
        task_type=TaskType.DOCUMENT_PROCESSING,
    )
    task.start()
    task.cancel()
    assert task.status == TaskStatus.CANCELLED


def test_task_info_progress():
    """Test updating task progress."""
    task = TaskInfo(
        task_id="task-123",
        task_type=TaskType.DOCUMENT_PROCESSING,
    )
    task.update_progress(0.5, "Halfway done")
    assert task.progress == 0.5
    assert task.message == "Halfway done"


def test_task_info_progress_bounds():
    """Test progress bounds enforcement."""
    task = TaskInfo(
        task_id="task-123",
        task_type=TaskType.DOCUMENT_PROCESSING,
    )
    task.update_progress(1.5)
    assert task.progress == 1.0

    task.update_progress(-0.5)
    assert task.progress == 0.0


def test_task_info_duration():
    """Test task duration calculation."""
    task = TaskInfo(
        task_id="task-123",
        task_type=TaskType.DOCUMENT_PROCESSING,
    )
    assert task.duration_ms is None

    task.start()
    assert task.duration_ms is not None


def test_task_info_is_complete():
    """Test is_complete property."""
    task = TaskInfo(
        task_id="task-123",
        task_type=TaskType.DOCUMENT_PROCESSING,
    )
    assert task.is_complete is False

    task.complete()
    assert task.is_complete is True


def test_task_info_to_dict():
    """Test converting task to dictionary."""
    task = TaskInfo(
        task_id="task-123",
        task_type=TaskType.DOCUMENT_PROCESSING,
        document_id="doc-456",
    )
    task_dict = task.to_dict()
    assert task_dict["task_id"] == "task-123"
    assert task_dict["document_id"] == "doc-456"


def test_task_info_document_context():
    """Test task info with document context."""
    task = TaskInfo(
        task_id="task-123",
        task_type=TaskType.DOCUMENT_PROCESSING,
        document_id="doc-456",
        user_id="user-789",
        organization_id="org-012",
    )
    assert task.document_id == "doc-456"
    assert task.user_id == "user-789"
    assert task.organization_id == "org-012"
