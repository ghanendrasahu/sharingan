"""Background tasks for document processing."""

from __future__ import annotations

import base64
import traceback
import uuid
from typing import Any

from celery import shared_task
from legallens_docproc.clause_segmenter import segment_clauses
from legallens_docproc.processor import process_document

from app.core.database import get_sync_session
from app.models.document import Document, DocumentClause, DocumentPage, DocumentStatus
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
    """Process an uploaded document through extraction and clause segmentation.

    Steps:
    1. Validate file
    2. Extract text using legallens_docproc
    3. Segment clauses
    4. Store results in database
    5. Update document status
    """
    task_info = TaskInfo(
        task_id=self.request.id,
        task_type=TaskType.DOCUMENT_PROCESSING,
        document_id=document_id,
        user_id=user_id,
        organization_id=organization_id,
    )

    try:
        # Step 1: Decode and validate file
        task_info.update_progress(0.05, "Validating file...")
        _update_task_state(self, task_info)

        file_content = base64.b64decode(file_content_b64)
        if not file_content:
            raise ValueError("Empty file content")

        # Step 2: Extract text using real processor
        task_info.update_progress(0.1, "Extracting text...")
        _update_task_state(self, task_info)

        processing_result = process_document(
            document_id=document_id,
            filename=filename,
            content=file_content,
        )

        if not processing_result.success:
            raise ValueError(f"Document processing failed: {processing_result.error}")

        processed_doc = processing_result.document
        if processed_doc is None:
            raise ValueError("No document data returned from processor")

        # Step 3: Segment clauses
        task_info.update_progress(0.5, "Segmenting clauses...")
        _update_task_state(self, task_info)

        clause_result = segment_clauses(processed_doc)

        # Step 4: Store results in database
        task_info.update_progress(0.7, "Storing results...")
        _update_task_state(self, task_info)

        session = get_sync_session()
        try:
            # Update document status
            document = session.query(Document).filter(Document.id == document_id).first()
            if document is None:
                raise ValueError(f"Document {document_id} not found in database")

            document.status = DocumentStatus.PROCESSED
            document.page_count = processed_doc.total_pages
            session.commit()

            # Store extracted pages
            for page in processed_doc.pages:
                db_page = DocumentPage(
                    document_id=document_id,
                    page_number=page.page_number,
                    text=page.text,
                    char_count=page.char_count,
                    word_count=page.word_count,
                    has_images=page.has_images,
                    is_scanned=page.is_scanned,
                )
                session.add(db_page)

            # Store segmented clauses
            for clause in clause_result.clauses:
                db_clause = DocumentClause(
                    document_id=document_id,
                    clause_id=clause.clause_id,
                    text=clause.text,
                    clause_type=clause.clause_type.value,
                    risk_level=clause.risk_level.value if clause.risk_level else None,
                    page_number=clause.page_number,
                    char_start=clause.char_start,
                    char_end=clause.char_end,
                    confidence=clause.confidence,
                )
                session.add(db_clause)

            session.commit()
        finally:
            session.close()

        # Step 5: Complete
        task_info.update_progress(1.0, "Processing complete")
        task_info.complete(
            result={
                "document_id": document_id,
                "pages_processed": processed_doc.total_pages,
                "clauses_found": clause_result.total_clauses,
                "total_chars": processed_doc.total_chars,
                "total_words": processed_doc.total_words,
                "processing_time_ms": processed_doc.processing_time_ms or 0,
            }
        )

        return task_info.to_dict()

    except Exception as e:
        # Mark document as failed
        try:
            session = get_sync_session()
            try:
                document = session.query(Document).filter(Document.id == document_id).first()
                if document is not None:
                    document.status = DocumentStatus.FAILED
                    document.processing_error = str(e)
                    session.commit()
            finally:
                session.close()
        except Exception:
            pass  # Don't mask original error

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
        task_info.complete(
            result={
                "report_id": f"report_{uuid.uuid4().hex[:8]}",
                "format": report_format,
                "size_bytes": 0,
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
