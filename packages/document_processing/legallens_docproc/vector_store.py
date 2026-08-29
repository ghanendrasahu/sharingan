"""Vector storage service for semantic search."""

from __future__ import annotations

import time
import uuid
from typing import Any

from legallens_docproc.embedding_models import (
    SearchResult,
    VectorDocument,
    VectorSearchResult,
)


class VectorStoreError(Exception):
    """Error in vector store operations."""

    def __init__(self, message: str, code: str = "VECTOR_STORE_ERROR") -> None:
        super().__init__(message)
        self.code = code
        self.detail = {"error": message, "code": code}


class VectorStore:
    """Abstract base class for vector storage."""

    async def add_document(self, document: VectorDocument) -> str:
        """Add a document to the vector store."""
        raise NotImplementedError

    async def add_documents(self, documents: list[VectorDocument]) -> list[str]:
        """Add multiple documents to the vector store."""
        raise NotImplementedError

    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> VectorSearchResult:
        """Search for similar documents."""
        raise NotImplementedError

    async def delete_document(self, document_id: str) -> bool:
        """Delete a document from the vector store."""
        raise NotImplementedError

    async def get_document(self, document_id: str) -> VectorDocument | None:
        """Get a document by ID."""
        raise NotImplementedError

    async def get_stats(self) -> dict[str, Any]:
        """Get vector store statistics."""
        raise NotImplementedError


class InMemoryVectorStore(VectorStore):
    """In-memory vector store for testing and development."""

    def __init__(self) -> None:
        self._documents: dict[str, VectorDocument] = {}

    async def add_document(self, document: VectorDocument) -> str:
        """Add a document to the in-memory store."""
        if not document.id:
            document.id = str(uuid.uuid4())
        self._documents[document.id] = document
        return document.id

    async def add_documents(self, documents: list[VectorDocument]) -> list[str]:
        """Add multiple documents to the in-memory store."""
        ids = []
        for doc in documents:
            doc_id = await self.add_document(doc)
            ids.append(doc_id)
        return ids

    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> VectorSearchResult:
        """Search for similar documents using cosine similarity."""
        start_time = time.time()
        results = []

        for doc in self._documents.values():
            # Apply filters
            if filters:
                skip = False
                for key, value in filters.items():
                    if doc.metadata.get(key) != value:
                        skip = True
                        break
                if skip:
                    continue

            # Calculate cosine similarity
            if doc.embedding and query_embedding:
                similarity = self._cosine_similarity(query_embedding, doc.embedding)
                results.append(
                    SearchResult(
                        document=doc,
                        score=similarity,
                        distance=1 - similarity,
                    )
                )

        # Sort by similarity score (descending)
        results.sort(key=lambda x: x.score, reverse=True)

        # Take top_k results
        results = results[:top_k]

        processing_time = (time.time() - start_time) * 1000

        return VectorSearchResult(
            query="",
            results=results,
            processing_time_ms=processing_time,
        )

    async def delete_document(self, document_id: str) -> bool:
        """Delete a document from the in-memory store."""
        if document_id in self._documents:
            del self._documents[document_id]
            return True
        return False

    async def get_document(self, document_id: str) -> VectorDocument | None:
        """Get a document by ID."""
        return self._documents.get(document_id)

    async def get_stats(self) -> dict[str, Any]:
        """Get in-memory store statistics."""
        return {
            "total_documents": len(self._documents),
            "total_embeddings": sum(1 for d in self._documents.values() if d.embedding),
        }

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if len(a) != len(b):
            return 0.0

        dot_product = sum(x * y for x, y in zip(a, b, strict=False))
        norm_a = sum(x**2 for x in a) ** 0.5
        norm_b = sum(x**2 for x in b) ** 0.5

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)


class PGVectorStore(VectorStore):
    """PostgreSQL pgvector store for production."""

    def __init__(
        self,
        connection_string: str,
        table_name: str = "document_embeddings",
        dimensions: int = 1536,
    ) -> None:
        self.connection_string = connection_string
        self.table_name = table_name
        self.dimensions = dimensions
        self._pool = None

    async def _get_pool(self):
        """Get or create connection pool."""
        if self._pool is None:
            try:
                import asyncpg

                self._pool = await asyncpg.create_pool(
                    self.connection_string,
                    min_size=5,
                    max_size=20,
                )

                # Create table if not exists
                async with self._pool.acquire() as conn:
                    await conn.execute(
                        f"""
                        CREATE TABLE IF NOT EXISTS {self.table_name} (
                            id UUID PRIMARY KEY,
                            content TEXT NOT NULL,
                            embedding vector({self.dimensions}),
                            metadata JSONB,
                            document_id UUID,
                            clause_id VARCHAR(255),
                            page_number INTEGER,
                            created_at TIMESTAMP DEFAULT NOW()
                        )
                    """
                    )

                    # Create index for vector search
                    await conn.execute(
                        f"""
                        CREATE INDEX IF NOT EXISTS idx_{self.table_name}_embedding
                        ON {self.table_name}
                        USING ivfflat (embedding vector_cosine_ops)
                        WITH (lists = 100)
                    """
                    )
            except ImportError as err:
                raise VectorStoreError(
                    "asyncpg not installed. Install with: pip install asyncpg",
                    code="DEPENDENCY_ERROR",
                ) from err
        return self._pool

    async def add_document(self, document: VectorDocument) -> str:
        """Add a document to pgvector."""
        pool = await self._get_pool()

        if not document.id:
            document.id = str(uuid.uuid4())

        async with pool.acquire() as conn:
            await conn.execute(
                f"""
                INSERT INTO {self.table_name} (id, content, embedding, metadata, document_id, clause_id, page_number)
                VALUES ($1, $2, $3::vector, $4, $5, $6, $7)
                ON CONFLICT (id) DO UPDATE SET
                    content = EXCLUDED.content,
                    embedding = EXCLUDED.embedding,
                    metadata = EXCLUDED.metadata
            """,
                document.id,
                document.content,
                str(document.embedding),
                document.metadata,
                document.document_id,
                document.clause_id,
                document.page_number,
            )

        return document.id

    async def add_documents(self, documents: list[VectorDocument]) -> list[str]:
        """Add multiple documents to pgvector."""
        ids = []
        for doc in documents:
            doc_id = await self.add_document(doc)
            ids.append(doc_id)
        return ids

    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> VectorSearchResult:
        """Search for similar documents in pgvector."""
        start_time = time.time()
        pool = await self._get_pool()

        # Build query
        query = f"""
            SELECT id, content, embedding, metadata, document_id, clause_id, page_number,
                   1 - (embedding <=> $1::vector) as similarity
            FROM {self.table_name}
        """

        params = [str(query_embedding)]

        if filters:
            conditions = []
            for key, value in filters.items():
                conditions.append(f"metadata->>'{key}' = ${len(params) + 1}")
                params.append(str(value))

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

        query += f" ORDER BY similarity DESC LIMIT ${len(params) + 1}"
        params.append(str(top_k))

        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *params)

        results = []
        for row in rows:
            doc = VectorDocument(
                id=row["id"],
                content=row["content"],
                embedding=list(row["embedding"]) if row["embedding"] else [],
                metadata=row["metadata"] or {},
                document_id=row["document_id"],
                clause_id=row["clause_id"],
                page_number=row["page_number"],
            )
            results.append(
                SearchResult(
                    document=doc,
                    score=row["similarity"],
                    distance=1 - row["similarity"],
                )
            )

        processing_time = (time.time() - start_time) * 1000

        return VectorSearchResult(
            query="",
            results=results,
            processing_time_ms=processing_time,
        )

    async def delete_document(self, document_id: str) -> bool:
        """Delete a document from pgvector."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            result = await conn.execute(
                f"DELETE FROM {self.table_name} WHERE id = $1",
                document_id,
            )
            return result.endswith("1")

    async def get_document(self, document_id: str) -> VectorDocument | None:
        """Get a document by ID."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                f"SELECT * FROM {self.table_name} WHERE id = $1",
                document_id,
            )
            if row:
                return VectorDocument(
                    id=row["id"],
                    content=row["content"],
                    embedding=list(row["embedding"]) if row["embedding"] else [],
                    metadata=row["metadata"] or {},
                    document_id=row["document_id"],
                    clause_id=row["clause_id"],
                    page_number=row["page_number"],
                )
        return None

    async def get_stats(self) -> dict[str, Any]:
        """Get pgvector store statistics."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            count = await conn.fetchval(f"SELECT COUNT(*) FROM {self.table_name}")
            return {
                "total_documents": count,
                "total_embeddings": count,
            }


def get_vector_store(
    store_type: str = "inmemory",
    connection_string: str = "",
    table_name: str = "document_embeddings",
    dimensions: int = 1536,
) -> VectorStore:
    """Get vector store by type."""
    stores = {
        "inmemory": InMemoryVectorStore,
        "pgvector": lambda: PGVectorStore(
            connection_string=connection_string,
            table_name=table_name,
            dimensions=dimensions,
        ),
    }

    store_factory = stores.get(store_type)
    if store_factory is None:
        raise VectorStoreError(
            f"Unknown vector store type: {store_type}. Available: {list(stores.keys())}",
            code="INVALID_STORE_TYPE",
        )

    return store_factory()
