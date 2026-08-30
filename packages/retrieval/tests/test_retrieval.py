"""Tests for LegalLens Retrieval package."""

from legallens_retrieval.embeddings import EmbeddingService
from legallens_retrieval.hybrid import BM25, HybridSearchEngine
from legallens_retrieval.reranker import CrossEncoderReranker, MMRSelector
from legallens_retrieval.vector_store import VectorStore


def test_embedding_service():
    svc = EmbeddingService()
    emb = svc.embed("test text")
    assert len(emb) == svc.dimension
    assert isinstance(emb[0], float)


def test_embedding_batch():
    svc = EmbeddingService()
    embs = svc.embed_batch(["text1", "text2"])
    assert len(embs) == 2
    assert len(embs[0]) == svc.dimension


def test_hash_embedding_deterministic():
    svc = EmbeddingService()
    emb1 = svc._hash_embedding("hello world")
    emb2 = svc._hash_embedding("hello world")
    assert emb1 == emb2


def test_vector_store_add_and_search():
    store = VectorStore(dimension=3)
    store.add("doc1", [1.0, 0.0, 0.0], "text1")
    store.add("doc2", [0.0, 1.0, 0.0], "text2")
    store.add("doc3", [0.0, 0.0, 1.0], "text3")

    results = store.search([1.0, 0.0, 0.0], top_k=2)
    assert len(results) == 2
    assert results[0].doc_id == "doc1"
    assert results[0].score > 0.9


def test_vector_store_batch():
    store = VectorStore(dimension=3)
    store.add_batch(
        ["d1", "d2"],
        [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
        ["t1", "t2"],
    )
    assert store.size == 2


def test_bm25_search():
    bm25 = BM25()
    bm25.index([
        ("doc1", "the cat sat on the mat"),
        ("doc2", "the dog sat on the log"),
        ("doc3", "the bird flew over the tree"),
    ])
    results = bm25.search("cat sat", top_k=2)
    assert len(results) == 2
    assert results[0].doc_id == "doc1"


def test_hybrid_search():
    store = VectorStore(dimension=3)
    engine = HybridSearchEngine(store)

    engine.index_documents(
        doc_ids=["d1", "d2", "d3"],
        texts=["legal clause about indemnity", "termination clause", "payment terms"],
        embeddings=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
    )

    results = engine.search(
        query="indemnity",
        query_embedding=[1.0, 0.0, 0.0],
        top_k=2,
    )
    assert len(results) > 0
    assert results[0].doc_id == "d1"


def test_reranker_fallback():
    reranker = CrossEncoderReranker()
    results = [
        {"text": "indemnity clause", "score": 0.5},
        {"text": "payment terms", "score": 0.3},
    ]
    reranked = reranker.rerank("indemnity", results, top_k=2)
    assert len(reranked) == 2
    assert all("rerank_score" in r for r in reranked)


def test_mmr_selection():
    selector = MMRSelector()
    results = [
        {"text": "a", "score": 0.9},
        {"text": "b", "score": 0.8},
        {"text": "c", "score": 0.7},
    ]
    embeddings = [[1.0, 0.0, 0.0], [0.9, 0.1, 0.0], [0.0, 0.0, 1.0]]

    selected = selector.select(results, embeddings, top_k=2)
    assert len(selected) == 2
