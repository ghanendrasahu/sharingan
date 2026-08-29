"""Search API request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SemanticSearchRequest(BaseModel):
    """Semantic search request."""

    query: str = Field(..., min_length=1, max_length=1000, description="Search query")
    top_k: int = Field(default=10, ge=1, le=100, description="Number of results")
    filters: dict[str, str] | None = Field(default=None, description="Search filters")
    include_metadata: bool = Field(default=True, description="Include metadata in results")


class ClauseSearchRequest(BaseModel):
    """Clause-specific search request."""

    query: str = Field(..., min_length=1, max_length=1000, description="Search query")
    top_k: int = Field(default=10, ge=1, le=50, description="Number of results")
    clause_type: str | None = Field(default=None, description="Filter by clause type")
    risk_level: str | None = Field(default=None, description="Filter by risk level")


class DocumentSearchRequest(BaseModel):
    """Document-level search request."""

    query: str = Field(..., min_length=1, max_length=1000, description="Search query")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of results")
    document_ids: list[str] | None = Field(default=None, description="Limit to specific documents")


class SearchHit(BaseModel):
    """Single search hit."""

    id: str
    content: str
    score: float = Field(..., ge=0.0, le=1.0, description="Similarity score")
    document_id: str | None = None
    clause_id: str | None = None
    page_number: int | None = None
    metadata: dict[str, str] = Field(default_factory=dict)
    highlights: list[str] = Field(default_factory=list)


class SemanticSearchResponse(BaseModel):
    """Semantic search response."""

    query: str
    hits: list[SearchHit] = Field(default_factory=list)
    total_hits: int = 0
    processing_time_ms: float | None = None


class ClauseSearchResponse(BaseModel):
    """Clause search response."""

    query: str
    hits: list[SearchHit] = Field(default_factory=list)
    total_hits: int = 0
    processing_time_ms: float | None = None


class DocumentSearchResponse(BaseModel):
    """Document search response."""

    query: str
    hits: list[SearchHit] = Field(default_factory=list)
    total_hits: int = 0
    processing_time_ms: float | None = None


class IndexDocumentRequest(BaseModel):
    """Request to index a document for search."""

    document_id: str = Field(..., description="Document ID to index")
    index_clauses: bool = Field(default=True, description="Index individual clauses")


class IndexDocumentResponse(BaseModel):
    """Response after indexing a document."""

    document_id: str
    indexed: bool = True
    items_indexed: int = 0
    message: str = ""


class SearchStatsResponse(BaseModel):
    """Search index statistics."""

    total_documents: int = 0
    total_clauses: int = 0
    total_embeddings: int = 0
    last_updated: str | None = None
