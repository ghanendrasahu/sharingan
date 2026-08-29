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
from .semantic_search import SemanticSearchService
from .vector_store import get_vector_store

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
    "EmbeddingBatchResult",
    "EmbeddingResult",
    "KeyTerm",
    "PageContent",
    "ProcessedDocument",
    "ProcessingResult",
    "ProcessingStatus",
    "RiskFinding",
    "RiskSeverity",
    "SearchResult",
    "SemanticSearchService",
    "TextBlock",
    "VectorDocument",
    "VectorSearchResult",
    "analyze_document_full",
    "get_embedding_provider",
    "get_llm_provider",
    "get_vector_store",
    "process_document",
    "process_document_async",
    "segment_clauses",
    "segment_clauses_async",
]
