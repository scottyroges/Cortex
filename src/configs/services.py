"""
Shared Services

Lazy-initialized services shared across all tools.
"""

import os
from typing import TYPE_CHECKING, Any, Optional

import chromadb
from anthropic import Anthropic

from src.configs.config import get_full_config
from src.external.git import is_git_repo
from src.storage import get_chroma_client, get_or_create_collection

# Use TYPE_CHECKING to avoid circular imports at runtime
# These imports are only used for type hints
if TYPE_CHECKING:
    from src.tools.search.hybrid import HybridSearcher
    from src.tools.search.reranker import RerankerService


def get_repo_path() -> Optional[str]:
    """
    Get repository path from current working directory.

    Used by tools to detect the actual repo path for branch detection,
    instead of hardcoding /projects.

    Returns:
        Repository path if cwd is a git repo, None otherwise
    """
    cwd = os.getcwd()
    return cwd if is_git_repo(cwd) else None


# --- Lazy-initialized Services ---

_chroma_client: Optional[chromadb.PersistentClient] = None
_collection: Optional[chromadb.Collection] = None
_hybrid_searcher: Optional[Any] = None  # HybridSearcher, lazy imported
_reranker: Optional[Any] = None  # RerankerService, lazy imported
_anthropic_client: Optional[Anthropic] = None

# Runtime configuration (mutable)
# Use get_full_config() to merge defaults, YAML config, and environment variables
CONFIG = get_full_config()


def get_collection() -> chromadb.Collection:
    """Lazy initialization of ChromaDB collection."""
    global _chroma_client, _collection
    if _collection is None:
        _chroma_client = get_chroma_client()
        _collection = get_or_create_collection(_chroma_client)
    return _collection


def get_searcher() -> "HybridSearcher":
    """Lazy initialization of hybrid searcher."""
    global _hybrid_searcher
    if _hybrid_searcher is None:
        from src.tools.search.hybrid import HybridSearcher

        _hybrid_searcher = HybridSearcher(get_collection())
    return _hybrid_searcher


def get_reranker() -> "RerankerService":
    """Lazy initialization of reranker."""
    global _reranker
    if _reranker is None:
        from src.tools.search.reranker import RerankerService

        _reranker = RerankerService()
    return _reranker


def get_anthropic() -> Optional[Anthropic]:
    """Lazy initialization of Anthropic client."""
    global _anthropic_client
    if _anthropic_client is None and os.environ.get("ANTHROPIC_API_KEY"):
        _anthropic_client = Anthropic()
    return _anthropic_client


def get_chromadb_client() -> chromadb.PersistentClient:
    """Get the ChromaDB client (for testing)."""
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = get_chroma_client()
    return _chroma_client


def reset_services() -> None:
    """Reset all lazy-initialized services. Used for testing."""
    global _chroma_client, _collection, _hybrid_searcher, _reranker, _anthropic_client
    _chroma_client = None
    _collection = None
    _hybrid_searcher = None
    _reranker = None
    _anthropic_client = None


def set_collection(collection: chromadb.Collection) -> None:
    """Set the collection directly. Used for testing."""
    global _collection, _hybrid_searcher
    _collection = collection
    _hybrid_searcher = None  # Reset searcher to use new collection
