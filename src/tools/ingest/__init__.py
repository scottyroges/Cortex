"""
Cortex Ingestion Engine

Metadata-first codebase ingestion with delta sync.
"""

from src.tools.ingest.engine import run_ingestion, select_delta_strategy
from src.tools.ingest.skeleton import generate_tree_structure, get_skeleton, store_skeleton
from src.tools.ingest.walker import compute_file_hash, get_changed_files, walk_codebase
from src.tools.ingest.ingest import ASYNC_FILE_THRESHOLD, ingest_code_into_cortex

# Backward compatibility alias - tests use ingest_codebase with engine signature
ingest_codebase = run_ingestion

__all__ = [
    # Walker
    "walk_codebase",
    "get_changed_files",
    "compute_file_hash",
    # Skeleton
    "generate_tree_structure",
    "store_skeleton",
    "get_skeleton",
    # Engine
    "run_ingestion",
    "ingest_codebase",  # Alias for run_ingestion (backward compat)
    "select_delta_strategy",
    # Tool
    "ingest_code_into_cortex",
    # Constants
    "ASYNC_FILE_THRESHOLD",
]
