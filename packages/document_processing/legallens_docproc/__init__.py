"""LegalLens Document Processing - PDF/DOCX extraction and clause segmentation."""

from .clause_models import (
    Clause,
    ClauseRiskLevel,
    ClauseSegmentationResult,
    ClauseType,
)
from .clause_segmenter import segment_clauses, segment_clauses_async
from .models import (
    DocumentFormat,
    PageContent,
    ProcessedDocument,
    ProcessingResult,
    ProcessingStatus,
    TextBlock,
)
from .processor import process_document, process_document_async

__all__ = [
    "Clause",
    "ClauseRiskLevel",
    "ClauseSegmentationResult",
    "ClauseType",
    "DocumentFormat",
    "PageContent",
    "ProcessedDocument",
    "ProcessingResult",
    "ProcessingStatus",
    "TextBlock",
    "process_document",
    "process_document_async",
    "segment_clauses",
    "segment_clauses_async",
]
