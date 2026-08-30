"""Search API endpoints for semantic search."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.models.document import Document, DocumentClause, DocumentPage
from app.schemas.search import (
    ClauseSearchRequest,
    ClauseSearchResponse,
    DocumentSearchRequest,
    DocumentSearchResponse,
    IndexDocumentRequest,
    IndexDocumentResponse,
    SearchHit,
    SearchStatsResponse,
    SemanticSearchRequest,
    SemanticSearchResponse,
)

if TYPE_CHECKING:
    from app.api.deps import CurrentUser

router = APIRouter(prefix="/search", tags=["search"])

DbSession = Annotated[AsyncSession, Depends(get_db)]
settings = get_settings()

# Global search service singleton
_search_service = None


def _get_search_service():
    """Get or create the semantic search service singleton."""
    global _search_service
    if _search_service is None:
        from legallens_docproc.embedding_service import get_embedding_provider
        from legallens_docproc.semantic_search import SemanticSearchService
        from legallens_docproc.vector_store import get_vector_store

        # Configure embedding provider
        provider_name = settings.EMBEDDING_PROVIDER
        api_key = settings.EMBEDDING_API_KEY or settings.LLM_API_KEY
        model = settings.EMBEDDING_MODEL

        if api_key and provider_name == "openai":
            embedding_provider = get_embedding_provider(
                "openai", api_key=api_key, model=model
            )
        else:
            embedding_provider = get_embedding_provider("mock")

        # Use in-memory vector store (single-server deployment)
        vector_store = get_vector_store("inmemory")

        _search_service = SemanticSearchService(
            embedding_provider=embedding_provider,
            vector_store=vector_store,
        )
    return _search_service


@router.post("/semantic", response_model=SemanticSearchResponse)
async def semantic_search(
    request: SemanticSearchRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> SemanticSearchResponse:
    """Semantic search across all documents.

    Find similar content using vector embeddings.
    """
    search_service = _get_search_service()

    try:
        result = asyncio.run(
            search_service.search(
                query=request.query,
                top_k=request.top_k,
                filters=request.filters,
            )
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {e!s}",
        ) from e

    hits = [
        SearchHit(
            id=r.document.id,
            content=r.document.content[:500],
            score=r.score,
            document_id=r.document.document_id,
            clause_id=r.document.clause_id,
            page_number=r.document.page_number,
            metadata=r.document.metadata,
        )
        for r in result.results
    ]

    return SemanticSearchResponse(
        query=request.query,
        hits=hits,
        total_hits=result.total_results,
        processing_time_ms=result.processing_time_ms or 0,
    )


@router.post("/clauses", response_model=ClauseSearchResponse)
async def search_clauses(
    request: ClauseSearchRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> ClauseSearchResponse:
    """Search for similar clauses.

    Find clauses similar to the query with optional type/risk filters.
    """
    search_service = _get_search_service()

    try:
        result = asyncio.run(
            search_service.search_clauses(
                query=request.query,
                top_k=request.top_k,
                risk_level=request.risk_level,
            )
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Clause search failed: {e!s}",
        ) from e

    hits = [
        SearchHit(
            id=r.document.id,
            content=r.document.content[:500],
            score=r.score,
            document_id=r.document.document_id,
            clause_id=r.document.clause_id,
            page_number=r.document.page_number,
            metadata=r.document.metadata,
        )
        for r in result.results
    ]

    return ClauseSearchResponse(
        query=request.query,
        hits=hits,
        total_hits=result.total_results,
        processing_time_ms=result.processing_time_ms or 0,
    )


@router.post("/documents", response_model=DocumentSearchResponse)
async def search_documents(
    request: DocumentSearchRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> DocumentSearchResponse:
    """Search across documents.

    Find documents matching the query.
    """
    search_service = _get_search_service()

    try:
        result = asyncio.run(
            search_service.search(
                query=request.query,
                top_k=request.top_k,
                filters={"type": "document"},
            )
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document search failed: {e!s}",
        ) from e

    hits = [
        SearchHit(
            id=r.document.id,
            content=r.document.content[:500],
            score=r.score,
            document_id=r.document.document_id,
            metadata=r.document.metadata,
        )
        for r in result.results
    ]

    return DocumentSearchResponse(
        query=request.query,
        hits=hits,
        total_hits=result.total_results,
        processing_time_ms=result.processing_time_ms or 0,
    )


@router.post("/index", response_model=IndexDocumentResponse)
async def index_document(
    request: IndexDocumentRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> IndexDocumentResponse:
    """Index a document for semantic search.

    Generate embeddings and store in vector database.
    """
    document_id = UUID(request.document_id)

    # Verify document exists
    doc_result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.deleted_at.is_(None),
        )
    )
    document = doc_result.scalar_one_or_none()

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Get document pages and clauses
    pages_result = await db.execute(
        select(DocumentPage)
        .where(DocumentPage.document_id == document_id)
        .order_by(DocumentPage.page_number)
    )
    pages = list(pages_result.scalars().all())

    clauses_result = await db.execute(
        select(DocumentClause).where(DocumentClause.document_id == document_id)
    )
    clauses = list(clauses_result.scalars().all())

    if not pages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document has no extracted content to index",
        )

    # Build ProcessedDocument and Clause objects
    from legallens_docproc.clause_models import Clause as DocProcClause
    from legallens_docproc.clause_models import ClauseRiskLevel, ClauseType
    from legallens_docproc.models import (
        DocumentFormat,
        PageContent,
        ProcessedDocument,
        ProcessingStatus,
    )

    doc_pages = [
        PageContent(
            page_number=p.page_number,
            text=p.text,
            char_count=p.char_count,
            word_count=p.word_count,
        )
        for p in pages
    ]

    processed_doc = ProcessedDocument(
        document_id=str(document_id),
        filename=document.original_filename,
        format=DocumentFormat.PDF if document.content_type == "application/pdf" else DocumentFormat.DOCX,
        status=ProcessingStatus.COMPLETED,
        pages=doc_pages,
    )

    docproc_clauses = []
    for c in clauses:
        try:
            clause_type = ClauseType(c.clause_type)
        except ValueError:
            clause_type = ClauseType.OTHER

        risk_level = None
        if c.risk_level:
            try:
                risk_level = ClauseRiskLevel(c.risk_level)
            except ValueError:
                risk_level = None

        docproc_clauses.append(
            DocProcClause(
                clause_id=c.clause_id,
                text=c.text,
                clause_type=clause_type,
                risk_level=risk_level,
                page_number=c.page_number,
                char_start=c.char_start,
                char_end=c.char_end,
                confidence=c.confidence,
            )
        )

    # Index using semantic search service
    search_service = _get_search_service()
    try:
        indexed_count = asyncio.run(
            search_service.index_document(processed_doc, docproc_clauses)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Indexing failed: {e!s}",
        ) from e

    return IndexDocumentResponse(
        document_id=request.document_id,
        indexed=True,
        items_indexed=indexed_count,
        message="Document indexed successfully",
    )


@router.get("/stats", response_model=SearchStatsResponse)
async def get_search_stats(
    current_user: CurrentUser,
    db: DbSession,
) -> SearchStatsResponse:
    """Get search index statistics."""
    search_service = _get_search_service()

    try:
        stats = asyncio.run(search_service.get_stats())
    except Exception:
        stats = {"total_documents": 0, "total_embeddings": 0}

    # Get actual document/clause counts from DB
    doc_count_result = await db.execute(
        select(func.count(Document.id)).where(Document.deleted_at.is_(None))
    )
    total_documents = doc_count_result.scalar() or 0

    clause_count_result = await db.execute(
        select(func.count(DocumentClause.id))
    )
    total_clauses = clause_count_result.scalar() or 0

    return SearchStatsResponse(
        total_documents=total_documents,
        total_clauses=total_clauses,
        total_embeddings=stats.get("total_embeddings", 0),
        last_updated="",
    )
