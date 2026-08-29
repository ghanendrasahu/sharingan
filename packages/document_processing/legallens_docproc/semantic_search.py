"""Semantic search service combining embeddings and vector storage."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from legallens_docproc.embedding_models import (
    VectorDocument,
    VectorSearchResult,
)
from legallens_docproc.embedding_service import EmbeddingProviderABC, get_embedding_provider
from legallens_docproc.vector_store import VectorStore, get_vector_store

if TYPE_CHECKING:
    from legallens_docproc.clause_models import Clause
    from legallens_docproc.models import ProcessedDocument


class SemanticSearchError(Exception):
    """Error during semantic search."""

    def __init__(self, message: str, code: str = "SEARCH_ERROR") -> None:
        super().__init__(message)
        self.code = code
        self.detail = {"error": message, "code": code}


class SemanticSearchService:
    """Service for semantic search over legal documents."""

    def __init__(
        self,
        embedding_provider: EmbeddingProviderABC | None = None,
        vector_store: VectorStore | None = None,
    ) -> None:
        self.embedding_provider = embedding_provider or get_embedding_provider("mock")
        self.vector_store = vector_store or get_vector_store("inmemory")

    async def index_document(
        self,
        document: ProcessedDocument,
        clauses: list[Clause] | None = None,
    ) -> int:
        """Index a document and its clauses for semantic search.

        Returns the number of items indexed.
        """
        indexed_count = 0
        documents_to_index = []

        # Index full document text
        if document.full_text:
            embedding_result = await self.embedding_provider.embed_text(
                document.full_text[:8000]  # Limit text length
            )

            if embedding_result.error:
                raise SemanticSearchError(
                    f"Embedding failed: {embedding_result.error}",
                    code="EMBEDDING_ERROR",
                )

            doc = VectorDocument(
                id=f"{document.document_id}_full",
                content=document.full_text[:2000],  # Store truncated content
                embedding=embedding_result.embedding,
                metadata={
                    "type": "document",
                    "filename": document.filename,
                    "format": document.format,
                },
                document_id=document.document_id,
            )
            documents_to_index.append(doc)
            indexed_count += 1

        # Index individual clauses
        if clauses:
            clause_texts = [c.text for c in clauses if c.text]
            if clause_texts:
                batch_result = await self.embedding_provider.embed_texts(
                    [t[:2000] for t in clause_texts]  # Limit text length
                )

                if batch_result.error:
                    raise SemanticSearchError(
                        f"Batch embedding failed: {batch_result.error}",
                        code="EMBEDDING_ERROR",
                    )

                for i, (clause, embedding_result) in enumerate(
                    zip(clauses, batch_result.embeddings, strict=False)
                ):
                    if clause.text:
                        doc = VectorDocument(
                            id=f"{document.document_id}_clause_{i}",
                            content=clause.text[:2000],
                            embedding=embedding_result.embedding,
                            metadata={
                                "type": "clause",
                                "clause_type": clause.clause_type,
                                "risk_level": clause.risk_level or "unknown",
                            },
                            document_id=document.document_id,
                            clause_id=clause.clause_id,
                            page_number=clause.page_number,
                        )
                        documents_to_index.append(doc)
                        indexed_count += 1

        # Add to vector store
        if documents_to_index:
            await self.vector_store.add_documents(documents_to_index)

        return indexed_count

    async def search(
        self,
        query: str,
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> VectorSearchResult:
        """Perform semantic search."""
        start_time = time.time()

        # Generate query embedding
        embedding_result = await self.embedding_provider.embed_text(query)

        if embedding_result.error:
            raise SemanticSearchError(
                f"Query embedding failed: {embedding_result.error}",
                code="EMBEDDING_ERROR",
            )

        # Search vector store
        search_result = await self.vector_store.search(
            query_embedding=embedding_result.embedding,
            top_k=top_k,
            filters=filters,
        )

        search_result.query = query
        search_result.processing_time_ms = (time.time() - start_time) * 1000

        return search_result

    async def search_clauses(
        self,
        query: str,
        top_k: int = 10,
        risk_level: str | None = None,
    ) -> VectorSearchResult:
        """Search for similar clauses."""
        filters = {"type": "clause"}
        if risk_level:
            filters["risk_level"] = risk_level

        return await self.search(query, top_k=top_k, filters=filters)

    async def find_similar_clauses(
        self,
        clause: Clause,
        top_k: int = 5,
    ) -> VectorSearchResult:
        """Find clauses similar to a given clause."""
        return await self.search_clauses(clause.text, top_k=top_k)

    async def get_document_context(
        self,
        query: str,
        document_id: str,
        top_k: int = 5,
    ) -> VectorSearchResult:
        """Get relevant context from a specific document."""
        filters = {"type": "clause"}
        # Note: document_id filter would need to be added to metadata

        return await self.search(query, top_k=top_k, filters=filters)

    async def clear_index(self) -> None:
        """Clear all indexed documents."""
        # This would need implementation in the vector store
        pass

    async def get_stats(self) -> dict[str, Any]:
        """Get search index statistics."""
        return await self.vector_store.get_stats()
