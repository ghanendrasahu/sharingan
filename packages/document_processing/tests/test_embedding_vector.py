"""Unit tests for embedding and vector search services."""

import pytest
from legallens_docproc.embedding_models import (
    EmbeddingBatchResult,
    EmbeddingResult,
    SearchResult,
    VectorDocument,
    VectorSearchResult,
)
from legallens_docproc.embedding_service import (
    MockEmbeddingProvider,
    get_embedding_provider,
)
from legallens_docproc.semantic_search import SemanticSearchService
from legallens_docproc.vector_store import InMemoryVectorStore, get_vector_store


def test_embedding_result_creation():
    """Test embedding result model creation."""
    result = EmbeddingResult(
        embedding=[0.1, 0.2, 0.3],
        model="test-model",
        dimensions=3,
    )
    assert len(result.embedding) == 3
    assert result.dimensions == 3


def test_embedding_batch_result():
    """Test batch embedding result."""
    results = [
        EmbeddingResult(embedding=[0.1, 0.2], model="m", dimensions=2),
        EmbeddingResult(embedding=[0.3, 0.4], model="m", dimensions=2),
    ]
    batch = EmbeddingBatchResult(embeddings=results, total_tokens=100)
    assert batch.count == 2


def test_vector_document_creation():
    """Test vector document model creation."""
    doc = VectorDocument(
        id="doc-1",
        content="Test content",
        embedding=[0.1, 0.2, 0.3],
        metadata={"type": "clause"},
    )
    assert doc.id == "doc-1"
    assert len(doc.embedding) == 3


def test_search_result_creation():
    """Test search result model creation."""
    doc = VectorDocument(id="1", content="test", embedding=[0.1])
    result = SearchResult(document=doc, score=0.95, distance=0.05)
    assert result.score == 0.95


def test_vector_search_result():
    """Test vector search result."""
    doc = VectorDocument(id="1", content="test", embedding=[0.1])
    results = [SearchResult(document=doc, score=0.9)]
    search_result = VectorSearchResult(query="test", results=results)
    assert search_result.total_results == 1


def test_mock_embedding_provider():
    """Test mock embedding provider."""
    provider = MockEmbeddingProvider(dimensions=384)
    assert provider.is_available() is True


@pytest.mark.asyncio
async def test_mock_embed_text():
    """Test mock text embedding."""
    provider = MockEmbeddingProvider(dimensions=384)
    result = await provider.embed_text("Hello world")

    assert isinstance(result, EmbeddingResult)
    assert len(result.embedding) == 384
    assert result.dimensions == 384


@pytest.mark.asyncio
async def test_mock_embed_texts():
    """Test mock batch embedding."""
    provider = MockEmbeddingProvider(dimensions=384)
    result = await provider.embed_texts(["Hello", "World"])

    assert isinstance(result, EmbeddingBatchResult)
    assert result.count == 2


def test_get_embedding_provider_mock():
    """Test getting mock embedding provider."""
    provider = get_embedding_provider(provider="mock", dimensions=384)
    assert isinstance(provider, MockEmbeddingProvider)


def test_get_embedding_provider_invalid():
    """Test getting invalid embedding provider."""
    with pytest.raises(Exception) as exc_info:
        get_embedding_provider(provider="invalid")
    assert "Unknown embedding provider" in str(exc_info.value)


def test_inmemory_vector_store():
    """Test in-memory vector store creation."""
    store = InMemoryVectorStore()
    assert store is not None


@pytest.mark.asyncio
async def test_inmemory_add_document():
    """Test adding document to in-memory store."""
    store = InMemoryVectorStore()
    doc = VectorDocument(
        id="doc-1",
        content="Test",
        embedding=[0.1, 0.2, 0.3],
    )

    doc_id = await store.add_document(doc)
    assert doc_id == "doc-1"


@pytest.mark.asyncio
async def test_inmemory_search():
    """Test searching in-memory store."""
    store = InMemoryVectorStore()

    # Add documents
    docs = [
        VectorDocument(id="1", content="Legal contract", embedding=[0.1, 0.2, 0.3]),
        VectorDocument(id="2", content="Non-disclosure", embedding=[0.4, 0.5, 0.6]),
    ]
    await store.add_documents(docs)

    # Search
    result = await store.search(query_embedding=[0.1, 0.2, 0.3], top_k=2)
    assert result.total_results == 2


@pytest.mark.asyncio
async def test_inmemory_delete_document():
    """Test deleting from in-memory store."""
    store = InMemoryVectorStore()
    doc = VectorDocument(id="doc-1", content="Test", embedding=[0.1])
    await store.add_document(doc)

    deleted = await store.delete_document("doc-1")
    assert deleted is True

    deleted = await store.delete_document("nonexistent")
    assert deleted is False


@pytest.mark.asyncio
async def test_inmemory_get_document():
    """Test getting document from in-memory store."""
    store = InMemoryVectorStore()
    doc = VectorDocument(id="doc-1", content="Test", embedding=[0.1])
    await store.add_document(doc)

    retrieved = await store.get_document("doc-1")
    assert retrieved is not None
    assert retrieved.id == "doc-1"


@pytest.mark.asyncio
async def test_inmemory_stats():
    """Test in-memory store statistics."""
    store = InMemoryVectorStore()
    doc = VectorDocument(id="doc-1", content="Test", embedding=[0.1])
    await store.add_document(doc)

    stats = await store.get_stats()
    assert stats["total_documents"] == 1


def test_get_vector_store_inmemory():
    """Test getting in-memory vector store."""
    store = get_vector_store(store_type="inmemory")
    assert isinstance(store, InMemoryVectorStore)


def test_get_vector_store_invalid():
    """Test getting invalid vector store."""
    with pytest.raises(Exception) as exc_info:
        get_vector_store(store_type="invalid")
    assert "Unknown vector store type" in str(exc_info.value)


@pytest.mark.asyncio
async def test_cosine_similarity():
    """Test cosine similarity calculation."""
    a = [1.0, 0.0, 0.0]
    b = [1.0, 0.0, 0.0]
    assert InMemoryVectorStore._cosine_similarity(a, b) == 1.0

    a = [1.0, 0.0]
    b = [0.0, 1.0]
    assert InMemoryVectorStore._cosine_similarity(a, b) == 0.0


@pytest.mark.asyncio
async def test_semantic_search_service():
    """Test semantic search service."""
    service = SemanticSearchService()
    assert service is not None


@pytest.mark.asyncio
async def test_semantic_search_basic():
    """Test basic semantic search."""
    service = SemanticSearchService()
    result = await service.search("test query", top_k=5)
    assert isinstance(result, VectorSearchResult)
