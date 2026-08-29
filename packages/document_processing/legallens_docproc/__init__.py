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
from .embedding_models import (
    EmbeddingBatchResult,
    EmbeddingResult,
    SearchResult,
    VectorDocument,
    VectorSearchResult,
)
from .embedding_service import get_embedding_provider
from .models import (
    DocumentFormat,
    PageContent,
    ProcessedDocument,
    ProcessingResult,
    ProcessingStatus,
    TextBlock,
)
from .processor import process_document, process_document_async
from .report_generator import (
    generate_analysis_report,
    report_to_html,
    report_to_json,
    report_to_markdown,
)
from .report_models import (
    AnalysisReport,
    DocumentInfo,
    ReportFormat,
    ReportSection,
    ReportType,
    RiskSummary,
)
from .semantic_search import SemanticSearchService
from .vector_store import get_vector_store

__all__ = [
    "AIAnalysisResult",
    "AnalysisReport",
    "AnalysisType",
    "Clause",
    "ClauseAnalysis",
    "ClauseRiskLevel",
    "ClauseSegmentationResult",
    "ClauseType",
    "DocumentFormat",
    "DocumentInfo",
    "DocumentSummary",
    "EmbeddingBatchResult",
    "EmbeddingResult",
    "KeyTerm",
    "PageContent",
    "ProcessedDocument",
    "ProcessingResult",
    "ProcessingStatus",
    "ReportFormat",
    "ReportSection",
    "ReportType",
    "RiskFinding",
    "RiskSeverity",
    "RiskSummary",
    "SearchResult",
    "SemanticSearchService",
    "TextBlock",
    "VectorDocument",
    "VectorSearchResult",
    "analyze_document_full",
    "generate_analysis_report",
    "get_embedding_provider",
    "get_llm_provider",
    "get_vector_store",
    "process_document",
    "process_document_async",
    "report_to_html",
    "report_to_json",
    "report_to_markdown",
    "segment_clauses",
    "segment_clauses_async",
]
