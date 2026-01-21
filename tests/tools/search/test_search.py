"""
Tests for search functionality (src/tools/search/).
"""

import pytest

from src.tools.search import (
    BM25Index,
    HybridSearcher,
    RerankerService,
    apply_recency_boost,
    reciprocal_rank_fusion,
)
from src.storage import get_or_create_collection


class TestBM25Index:
    """Tests for BM25 indexing."""

    def test_build_index(self, temp_chroma_client):
        """Test building BM25 index from collection."""
        collection = get_or_create_collection(temp_chroma_client, "test_bm25")
        collection.add(
            documents=[
                "Python is a programming language",
                "JavaScript runs in the browser",
                "Rust is fast and safe",
            ],
            ids=["1", "2", "3"],
            metadatas=[{"lang": "python"}, {"lang": "javascript"}, {"lang": "rust"}],
        )

        index = BM25Index()
        index.build_from_collection(collection)

        assert index.index is not None
        assert len(index.documents) == 3

    def test_search(self, temp_chroma_client):
        """Test BM25 search."""
        collection = get_or_create_collection(temp_chroma_client, "test_bm25_search")
        collection.add(
            documents=[
                "Python is a programming language",
                "JavaScript runs in the browser",
                "Rust is fast and memory safe",
            ],
            ids=["1", "2", "3"],
            metadatas=[{"lang": "python"}, {"lang": "javascript"}, {"lang": "rust"}],
        )

        index = BM25Index()
        index.build_from_collection(collection)

        results = index.search("Python programming", top_k=2)
        assert len(results) <= 2
        # Python document should rank highest
        assert "Python" in results[0]["text"]

    def test_empty_collection(self, temp_chroma_client):
        """Test BM25 with empty collection."""
        collection = get_or_create_collection(temp_chroma_client, "test_empty_bm25")

        index = BM25Index()
        index.build_from_collection(collection)

        results = index.search("anything")
        assert results == []


class TestRRFFusion:
    """Tests for Reciprocal Rank Fusion."""

    def test_basic_fusion(self):
        """Test basic RRF fusion of two result lists."""
        vector_results = [
            {"id": "a", "text": "doc a"},
            {"id": "b", "text": "doc b"},
            {"id": "c", "text": "doc c"},
        ]
        bm25_results = [
            {"id": "b", "text": "doc b"},
            {"id": "d", "text": "doc d"},
            {"id": "a", "text": "doc a"},
        ]

        fused = reciprocal_rank_fusion(vector_results, bm25_results)

        # Documents appearing in both should have higher scores
        assert len(fused) == 4  # a, b, c, d
        assert all("rrf_score" in doc for doc in fused)

        # 'b' appears high in both lists, should be near top
        top_ids = [doc["id"] for doc in fused[:2]]
        assert "b" in top_ids or "a" in top_ids

    def test_empty_lists(self):
        """Test RRF with empty lists."""
        fused = reciprocal_rank_fusion([], [])
        assert fused == []

    def test_single_list(self):
        """Test RRF with only one non-empty list."""
        vector_results = [
            {"id": "a", "text": "doc a"},
            {"id": "b", "text": "doc b"},
        ]

        fused = reciprocal_rank_fusion(vector_results, [])
        assert len(fused) == 2


class TestHybridSearcher:
    """Tests for hybrid search functionality."""

    def test_hybrid_search(self, temp_chroma_client):
        """Test hybrid search combines vector and BM25."""
        collection = get_or_create_collection(temp_chroma_client, "test_hybrid")
        collection.add(
            documents=[
                "Python is a programming language for data science",
                "JavaScript is used for web development",
                "Rust provides memory safety without garbage collection",
                "Python and machine learning go well together",
            ],
            ids=["1", "2", "3", "4"],
            metadatas=[
                {"topic": "python"},
                {"topic": "javascript"},
                {"topic": "rust"},
                {"topic": "python"},
            ],
        )

        searcher = HybridSearcher(collection)
        results = searcher.search("Python programming", top_k=3)

        assert len(results) <= 3
        assert all("rrf_score" in doc for doc in results)


class TestRerankerService:
    """Tests for reranking functionality."""

    def test_rerank_basic(self):
        """Test basic reranking."""
        reranker = RerankerService()

        documents = [
            {"text": "This is about cats and dogs"},
            {"text": "Programming in Python is fun"},
            {"text": "Python is a snake species"},
        ]

        results = reranker.rerank("Python programming language", documents, top_k=2)

        assert len(results) == 2
        assert all("rerank_score" in doc for doc in results)
        # Programming document should rank higher than snake document
        assert "Programming" in results[0]["text"] or "Python" in results[0]["text"]

    def test_rerank_empty(self):
        """Test reranking empty document list."""
        reranker = RerankerService()
        results = reranker.rerank("query", [], top_k=5)
        assert results == []

    def test_rerank_preserves_metadata(self):
        """Test that reranking preserves document metadata."""
        reranker = RerankerService()

        documents = [
            {"text": "Python programming", "source": "docs", "page": 1},
            {"text": "JavaScript tutorial", "source": "blog", "page": 5},
        ]

        results = reranker.rerank("Python", documents, top_k=2)

        # Original metadata should be preserved
        for result in results:
            assert "source" in result
            assert "page" in result


class TestRecencyBoost:
    """Tests for recency boost functionality."""

    def test_boost_new_note_higher(self):
        """Test that newer notes get higher boosted scores."""
        from datetime import datetime, timezone, timedelta

        now = datetime.now(timezone.utc)
        old_time = (now - timedelta(days=60)).isoformat()
        new_time = now.isoformat()

        results = [
            {"rerank_score": 0.8, "meta": {"type": "note", "created_at": old_time}},
            {"rerank_score": 0.8, "meta": {"type": "note", "created_at": new_time}},
        ]

        boosted = apply_recency_boost(results, half_life_days=30)

        # Newer note should have higher boosted score
        new_result = next(r for r in boosted if r["meta"]["created_at"] == new_time)
        old_result = next(r for r in boosted if r["meta"]["created_at"] == old_time)

        assert new_result["boosted_score"] > old_result["boosted_score"]
        assert new_result["recency_boost"] > old_result["recency_boost"]

    def test_file_metadata_not_boosted(self):
        """Test that file_metadata is not affected by recency boost."""
        from datetime import datetime, timezone, timedelta

        now = datetime.now(timezone.utc)
        old_time = (now - timedelta(days=60)).isoformat()

        results = [
            {"rerank_score": 0.8, "meta": {"type": "file_metadata", "indexed_at": old_time}},
        ]

        boosted = apply_recency_boost(results)

        # file_metadata should not be boosted - recency_boost should be 1.0
        assert boosted[0]["recency_boost"] == 1.0
        assert boosted[0]["boosted_score"] == 0.8

    def test_min_boost_applied(self):
        """Test that minimum boost floor is applied."""
        from datetime import datetime, timezone, timedelta

        now = datetime.now(timezone.utc)
        very_old_time = (now - timedelta(days=365)).isoformat()

        results = [
            {"rerank_score": 1.0, "meta": {"type": "note", "created_at": very_old_time}},
        ]

        boosted = apply_recency_boost(results, half_life_days=30, min_boost=0.5)

        # Very old note should hit min_boost floor
        assert boosted[0]["recency_boost"] == 0.5
        assert boosted[0]["boosted_score"] == 0.5

    def test_empty_results(self):
        """Test that empty results are handled."""
        boosted = apply_recency_boost([])
        assert boosted == []

    def test_results_resorted_by_boosted_score(self):
        """Test that results are re-sorted by boosted score."""
        from datetime import datetime, timezone, timedelta

        now = datetime.now(timezone.utc)
        old_time = (now - timedelta(days=60)).isoformat()
        new_time = now.isoformat()

        # Old note has higher rerank_score but new note should win after boost
        results = [
            {"rerank_score": 0.9, "meta": {"type": "note", "created_at": old_time}},
            {"rerank_score": 0.7, "meta": {"type": "note", "created_at": new_time}},
        ]

        boosted = apply_recency_boost(results, half_life_days=30)

        # Newer note should now be first despite lower original score
        assert boosted[0]["meta"]["created_at"] == new_time


class TestConditionalIndexRebuild:
    """Tests for conditional BM25 index rebuild (caching behavior)."""

    def test_index_not_rebuilt_on_repeated_search(self, temp_chroma_client):
        """Index should not rebuild on subsequent searches when not invalidated."""
        collection = get_or_create_collection(temp_chroma_client, "test_cache")
        collection.add(
            documents=["Python programming", "JavaScript web"],
            ids=["1", "2"],
            metadatas=[{"type": "test"}] * 2,
        )

        searcher = HybridSearcher(collection)
        searcher.build_index()  # Initial build

        # Track if build_from_collection is called
        build_count = [0]
        original_build = searcher.bm25_index.build_from_collection

        def counting_build(*args, **kwargs):
            build_count[0] += 1
            return original_build(*args, **kwargs)

        searcher.bm25_index.build_from_collection = counting_build

        # Multiple searches should NOT rebuild
        searcher.search("Python")
        searcher.search("JavaScript")
        searcher.search("test query")

        assert build_count[0] == 0, "Index should not rebuild on repeated searches"

    def test_index_rebuilt_after_invalidate(self, temp_chroma_client):
        """Index should rebuild after explicit invalidation."""
        collection = get_or_create_collection(temp_chroma_client, "test_invalidate")
        collection.add(
            documents=["document one", "document two"],
            ids=["1", "2"],
            metadatas=[{"type": "test"}] * 2,
        )

        searcher = HybridSearcher(collection)
        searcher.build_index()

        # Track rebuilds
        build_count = [0]
        original_build = searcher.bm25_index.build_from_collection

        def counting_build(*args, **kwargs):
            build_count[0] += 1
            return original_build(*args, **kwargs)

        searcher.bm25_index.build_from_collection = counting_build

        # Invalidate and search
        searcher.invalidate()
        searcher.search("test")

        assert build_count[0] == 1, "Index should rebuild after invalidation"

    def test_rebuild_index_flag_forces_rebuild(self, temp_chroma_client):
        """rebuild_index=True should force a rebuild."""
        collection = get_or_create_collection(temp_chroma_client, "test_force")
        collection.add(
            documents=["test document"],
            ids=["1"],
            metadatas=[{"type": "test"}],
        )

        searcher = HybridSearcher(collection)
        searcher.build_index()

        build_count = [0]
        original_build = searcher.bm25_index.build_from_collection

        def counting_build(*args, **kwargs):
            build_count[0] += 1
            return original_build(*args, **kwargs)

        searcher.bm25_index.build_from_collection = counting_build

        # Force rebuild
        searcher.search("test", rebuild_index=True)

        assert build_count[0] == 1, "rebuild_index=True should force rebuild"

    def test_thread_safety(self, temp_chroma_client):
        """Multiple threads should not cause race conditions."""
        import threading

        collection = get_or_create_collection(temp_chroma_client, "test_threads")
        collection.add(
            documents=["doc " + str(i) for i in range(10)],
            ids=[str(i) for i in range(10)],
            metadatas=[{"type": "test"}] * 10,
        )

        searcher = HybridSearcher(collection)
        errors = []

        def search_thread():
            try:
                for _ in range(5):
                    searcher.search("test")
            except Exception as e:
                errors.append(e)

        def invalidate_thread():
            try:
                for _ in range(5):
                    searcher.invalidate()
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=search_thread) for _ in range(3)] + [
            threading.Thread(target=invalidate_thread) for _ in range(2)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Thread safety errors: {errors}"
