"""LegalLens Document Processing - PDF/DOCX extraction and clause segmentation."""

from .ai_analyzer import analyze_document_full, get_llm_provider
from .analysis_models import (
    AIAnalysisResult,
    AnalysisType,
    ClauseAnalysis,
    DocumentSummary,
    KeyTerm,
    RiskFinding,
    RiskSeverity,
)
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
    "AIAnalysisResult",
    "AnalysisType",
    "Clause",
    "ClauseAnalysis",
    "ClauseRiskLevel",
    "ClauseSegmentationResult",
    "ClauseType",
    "DocumentFormat",
    "DocumentSummary",
    "KeyTerm",
    "PageContent",
    "ProcessedDocument",
    "ProcessingResult",
    "ProcessingStatus",
    "RiskFinding",
    "RiskSeverity",
    "TextBlock",
    "analyze_document_full",
    "get_llm_provider",
    "process_document",
    "process_document_async",
    "segment_clauses",
    "segment_clauses_async",
]
