"""
Cortex Storage Layer

ChromaDB client management and garbage collection.
"""

from src.storage.chromadb import (
    get_chroma_client,
    get_collection_stats,
    get_or_create_collection,
)
from src.storage.gc import delete_file_chunks

__all__ = [
    "get_chroma_client",
    "get_or_create_collection",
    "get_collection_stats",
    "delete_file_chunks",
]
