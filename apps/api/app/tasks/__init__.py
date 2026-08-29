"""Background tasks package."""

from app.tasks.document import (
    analyze_document_task,
    generate_report_task,
    process_document_task,
)

__all__ = [
    "analyze_document_task",
    "generate_report_task",
    "process_document_task",
]
