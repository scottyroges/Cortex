"""
Cortex Ingestion Engine

Metadata-first codebase ingestion with delta sync.
"""

from src.ingest.engine import ingest_codebase
from src.ingest.skeleton import generate_tree_structure, store_skeleton
from src.ingest.walker import compute_file_hash, get_changed_files, walk_codebase

__all__ = [
    # Walker
    "walk_codebase",
    "get_changed_files",
    "compute_file_hash",
    # Skeleton
    "generate_tree_structure",
    "store_skeleton",
    # Engine
    "ingest_codebase",
]
