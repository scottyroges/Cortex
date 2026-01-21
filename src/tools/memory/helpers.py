"""
Memory Module Helpers

Shared utilities for memory operations: repository resolution,
context building, and file hashing.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Callable

from src.configs import get_logger
from src.configs.services import get_collection, get_repo_path
from src.external.git import get_current_branch, get_head_commit
from src.tools.ingest.walker import compute_file_hash
from src.tools.initiatives import get_any_focused_repository, get_focused_initiative
from src.tools.initiatives.utils import resolve_initiative

logger = get_logger("tools.memory")


def get_focused_initiative_info(repository: str) -> tuple[Optional[str], Optional[str]]:
    """Get focused initiative (id, name) tuple for resolve_initiative callback."""
    try:
        focus = get_focused_initiative(repository)
        if focus:
            return focus.get("initiative_id"), focus.get("initiative_name")
    except Exception as e:
        logger.warning(f"Failed to get focused initiative: {e}")
    return None, None


def resolve_repository(repository: Optional[str]) -> str:
    """
    Resolve repository name, auto-detecting if not provided.

    Resolution order:
    1. Explicit repository parameter
    2. Current working directory (if git repo)
    3. Repository from any focused initiative
    4. "global" fallback

    Args:
        repository: Explicit repository name, or None to auto-detect

    Returns:
        Repository name (falls back to "global" if detection fails)
    """
    if repository:
        return repository

    # Auto-detect from current working directory
    repo_path = get_repo_path()
    if repo_path:
        return repo_path.rstrip("/").split("/")[-1]

    # Try to get repository from any focused initiative
    focused_repo = get_any_focused_repository()
    if focused_repo:
        return focused_repo

    return "global"


def build_base_context(
    repository: Optional[str],
    initiative: Optional[str],
) -> dict:
    """
    Build common context for save operations.

    Returns dict with:
        - repo: resolved repository name
        - collection: ChromaDB collection
        - repo_path: path to repo (or None)
        - branch: current git branch
        - timestamp: ISO timestamp
        - current_commit: HEAD commit SHA (or None)
        - initiative_id: resolved initiative ID (or None)
        - initiative_name: resolved initiative name (or None)
    """
    repo = resolve_repository(repository)
    collection = get_collection()
    repo_path = get_repo_path()
    branch = get_current_branch(repo_path) if repo_path else "unknown"
    timestamp = datetime.now(timezone.utc).isoformat()
    current_commit = get_head_commit(repo_path) if repo_path else None

    initiative_id, initiative_name = resolve_initiative(
        collection, repo, initiative, get_focused_initiative_info
    )

    return {
        "repo": repo,
        "collection": collection,
        "repo_path": repo_path,
        "branch": branch,
        "timestamp": timestamp,
        "current_commit": current_commit,
        "initiative_id": initiative_id,
        "initiative_name": initiative_name,
    }


def add_common_metadata(metadata: dict, ctx: dict) -> None:
    """Add common fields to metadata dict from context."""
    if ctx["current_commit"]:
        metadata["created_commit"] = ctx["current_commit"]
    if ctx["initiative_id"]:
        metadata["initiative_id"] = ctx["initiative_id"]
        metadata["initiative_name"] = ctx["initiative_name"] or ""


def compute_file_hashes(files: list[str], repo_path: Optional[str]) -> dict[str, str]:
    """Compute content hashes for a list of files (for staleness detection)."""
    file_hashes = {}
    if not repo_path:
        return file_hashes

    for file_path in files:
        full_path = Path(file_path)
        if not full_path.is_absolute():
            full_path = Path(repo_path) / file_path
        if full_path.exists():
            try:
                file_hashes[file_path] = compute_file_hash(full_path)
            except (OSError, IOError) as e:
                logger.warning(f"Could not hash file {file_path}: {e}")

    return file_hashes


def update_initiative_timestamp(collection, initiative_id: str, timestamp: str) -> None:
    """Update an initiative's updated_at timestamp."""
    try:
        result = collection.get(
            ids=[initiative_id],
            include=["documents", "metadatas"],
        )
        if result["ids"]:
            meta = result["metadatas"][0]
            meta["updated_at"] = timestamp
            collection.upsert(
                ids=[initiative_id],
                documents=[result["documents"][0]],
                metadatas=[meta],
            )
    except Exception as e:
        logger.warning(f"Failed to update initiative timestamp: {e}")
