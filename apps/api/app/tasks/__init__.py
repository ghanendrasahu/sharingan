"""Background tasks package."""

from app.tasks.analysis import analyze_document_task
from app.tasks.document import (
    generate_report_task,
    process_document_task,
)

__all__ = [
    "analyze_document_task",
    "generate_report_task",
    "process_document_task",
]
