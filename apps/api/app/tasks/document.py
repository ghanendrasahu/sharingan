"""Background tasks for document processing."""

from __future__ import annotations

import time
import traceback
import uuid
from typing import Any

from celery import shared_task

from app.models.task import TaskInfo, TaskType


@shared_task(
    name="app.tasks.document.process_document_task",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    queue="document_processing",
)
def process_document_task(
    self,
    document_id: str,
    filename: str,
    file_content_b64: str,
    user_id: str | None = None,
    organization_id: str | None = None,
) -> dict[str, Any]:
    """Process an uploaded document.

    Steps:
    1. Validate file
    2. Extract text
    3. Segment clauses
    4. Generate embeddings
    5. Store results
    """
    import base64

    task_info = TaskInfo(
        task_id=self.request.id,
        task_type=TaskType.DOCUMENT_PROCESSING,
        document_id=document_id,
        user_id=user_id,
        organization_id=organization_id,
    )

    try:
        # Decode file content (validation step)
        _ = base64.b64decode(file_content_b64)

        # Step 1: Validate file
        task_info.update_progress(0.1, "Validating file...")
        _update_task_state(self, task_info)

        # Step 2: Extract text
        task_info.update_progress(0.3, "Extracting text...")
        _update_task_state(self, task_info)
        time.sleep(0.5)  # Simulate processing

        # Step 3: Segment clauses
        task_info.update_progress(0.5, "Segmenting clauses...")
        _update_task_state(self, task_info)
        time.sleep(0.5)  # Simulate processing

        # Step 4: Generate embeddings
        task_info.update_progress(0.7, "Generating embeddings...")
        _update_task_state(self, task_info)
        time.sleep(0.5)  # Simulate processing

        # Step 5: Store results
        task_info.update_progress(0.9, "Storing results...")
        _update_task_state(self, task_info)
        time.sleep(0.5)  # Simulate processing

        # Complete
        task_info.complete(
            result={
                "document_id": document_id,
                "pages_processed": 1,
                "clauses_found": 5,
                "embeddings_generated": 6,
            }
        )

        return task_info.to_dict()

    except Exception as e:
        task_info.fail(error=str(e), traceback=traceback.format_exc())
        raise self.retry(exc=e)  # noqa: B904


@shared_task(
    name="app.tasks.document.analyze_document_task",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    queue="ai_analysis",
)
def analyze_document_task(
    self,
    document_id: str,
    document_text: str,
    analysis_type: str = "full_analysis",
    user_id: str | None = None,
    organization_id: str | None = None,
) -> dict[str, Any]:
    """Analyze a document using AI.

    Steps:
    1. Prepare analysis
    2. Run AI analysis
    3. Generate report
    4. Store results
    """
    task_info = TaskInfo(
        task_id=self.request.id,
        task_type=TaskType.AI_ANALYSIS,
        document_id=document_id,
        user_id=user_id,
        organization_id=organization_id,
    )

    try:
        # Step 1: Prepare analysis
        task_info.update_progress(0.1, "Preparing analysis...")
        _update_task_state(self, task_info)

        # Step 2: Run AI analysis
        task_info.update_progress(0.3, "Running AI analysis...")
        _update_task_state(self, task_info)
        time.sleep(1.0)  # Simulate AI processing

        # Step 3: Generate report
        task_info.update_progress(0.7, "Generating report...")
        _update_task_state(self, task_info)
        time.sleep(0.5)  # Simulate report generation

        # Step 4: Store results
        task_info.update_progress(0.9, "Storing results...")
        _update_task_state(self, task_info)

        # Complete
        task_info.complete(
            result={
                "analysis_id": f"analysis_{uuid.uuid4().hex[:8]}",
                "document_id": document_id,
                "analysis_type": analysis_type,
                "risk_score": 0.65,
                "risks_found": 8,
            }
        )

        return task_info.to_dict()

    except Exception as e:
        task_info.fail(error=str(e), traceback=traceback.format_exc())
        raise self.retry(exc=e)  # noqa: B904


@shared_task(
    name="app.tasks.document.generate_report_task",
    bind=True,
    max_retries=2,
    queue="document_processing",
)
def generate_report_task(
    self,
    document_id: str,
    analysis_result: dict[str, Any],
    report_format: str = "json",
    user_id: str | None = None,
) -> dict[str, Any]:
    """Generate analysis report."""
    task_info = TaskInfo(
        task_id=self.request.id,
        task_type=TaskType.REPORT_GENERATION,
        document_id=document_id,
        user_id=user_id,
    )

    try:
        task_info.update_progress(0.5, "Generating report...")
        _update_task_state(self, task_info)

        # Generate report
        time.sleep(0.5)  # Simulate report generation

        task_info.complete(
            result={
                "report_id": f"report_{uuid.uuid4().hex[:8]}",
                "format": report_format,
                "size_bytes": 1024,
            }
        )

        return task_info.to_dict()

    except Exception as e:
        task_info.fail(error=str(e), traceback=traceback.format_exc())
        raise self.retry(exc=e)  # noqa: B904


def _update_task_state(task, task_info: TaskInfo) -> None:
    """Update task state for monitoring."""
    task.update_state(
        state=task_info.status,
        meta=task_info.to_dict(),
    )
