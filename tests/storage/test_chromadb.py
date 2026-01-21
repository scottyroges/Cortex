"""
Tests for ChromaDB storage (src/storage/chromadb.py).
"""

import pytest

from src.storage import get_collection_stats, get_or_create_collection


class TestChromaDB:
    """Tests for ChromaDB functionality."""

    def test_create_collection(self, temp_chroma_client):
        """Test collection creation."""
        collection = get_or_create_collection(temp_chroma_client, "test_collection")
        assert collection is not None
        assert collection.name == "test_collection"

    def test_collection_stats_empty(self, temp_chroma_client):
        """Test stats for empty collection."""
        collection = get_or_create_collection(temp_chroma_client, "test_empty")
        stats = get_collection_stats(collection)
        assert stats["document_count"] == 0

    def test_collection_stats_with_docs(self, temp_chroma_client):
        """Test stats for collection with documents."""
        collection = get_or_create_collection(temp_chroma_client, "test_with_docs")
        collection.add(
            documents=["doc1", "doc2", "doc3"],
            ids=["1", "2", "3"],
            metadatas=[{"type": "test"}] * 3,
        )
        stats = get_collection_stats(collection)
        assert stats["document_count"] == 3
