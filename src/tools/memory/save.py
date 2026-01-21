"""
Memory Save Operations

Functions for saving notes and insights to Cortex memory.
"""

import json
import uuid
from typing import Literal, Optional

from src.configs import get_logger
from src.configs.services import get_searcher
from src.utils.secret_scrubber import scrub_secrets

from .helpers import (
    build_base_context,
    add_common_metadata,
    compute_file_hashes,
    update_initiative_timestamp,
)

logger = get_logger("tools.memory")


def save_memory(
    content: str,
    kind: Literal["note", "insight"],
    title: Optional[str] = None,
    tags: Optional[list[str]] = None,
    repository: Optional[str] = None,
    initiative: Optional[str] = None,
    files: Optional[list[str]] = None,
) -> str:
    """
    Save understanding to Cortex memory.

    **When to use this tool:**
    - Discovered a pattern or gotcha? kind="insight", link to files
    - Making an architectural decision? kind="note"
    - Documenting a non-obvious behavior? kind="insight"
    - Recording a learning for future sessions? kind="note"

    Args:
        content: The content to save (note text or insight analysis)
        kind: Type of memory - "note" for decisions/docs, "insight" for file-linked analysis
        title: Optional title
        tags: Optional categorization tags
        repository: Repository identifier (defaults to "global")
        initiative: Initiative to tag (uses focused if not specified)
        files: File paths this insight is about (REQUIRED for kind="insight")

    Returns:
        JSON with saved memory ID and status
    """
    if kind == "note":
        return save_note(content, title, tags, repository, initiative)
    elif kind == "insight":
        if not files:
            return json.dumps({
                "status": "error",
                "error": "files parameter is required when kind='insight'",
            })
        return save_insight(content, files, title, tags, repository, initiative)
    else:
        return json.dumps({
            "status": "error",
            "error": f"Unknown kind: {kind}. Valid kinds: 'note', 'insight'",
        })


def save_note(
    content: str,
    title: Optional[str] = None,
    tags: Optional[list[str]] = None,
    repository: Optional[str] = None,
    initiative: Optional[str] = None,
) -> str:
    """
    Save a note, documentation snippet, or decision to Cortex memory.

    Args:
        content: The note content
        title: Optional title for the note
        tags: Optional list of tags for categorization
        repository: Repository identifier
        initiative: Initiative ID/name to tag (uses focused initiative if not specified)

    Returns:
        JSON with note ID and save status
    """
    ctx = build_base_context(repository, initiative)
    logger.info(f"Saving note: title='{title}', repository={ctx['repo']}")

    try:
        note_id = f"note:{uuid.uuid4().hex[:8]}"

        # Build document text
        doc_text = f"{title}\n\n" if title else ""
        doc_text += scrub_secrets(content)

        metadata = {
            "type": "note",
            "title": title or "",
            "tags": json.dumps(tags) if tags else "[]",
            "repository": ctx["repo"],
            "branch": ctx["branch"],
            "created_at": ctx["timestamp"],
            "updated_at": ctx["timestamp"],
            "verified_at": ctx["timestamp"],
            "status": "active",
        }
        add_common_metadata(metadata, ctx)

        ctx["collection"].upsert(
            ids=[note_id],
            documents=[doc_text],
            metadatas=[metadata],
        )
        get_searcher().build_index()

        logger.info(f"Note saved: {note_id}")

        response = {
            "status": "saved",
            "note_id": note_id,
            "title": title,
        }
        if ctx["initiative_id"]:
            response["initiative"] = {
                "id": ctx["initiative_id"],
                "name": ctx["initiative_name"],
            }

        return json.dumps(response, indent=2)

    except Exception as e:
        logger.error(f"Note save error: {e}")
        return json.dumps({
            "status": "error",
            "error": str(e),
        })


def save_insight(
    insight: str,
    files: list[str],
    title: Optional[str] = None,
    tags: Optional[list[str]] = None,
    repository: Optional[str] = None,
    initiative: Optional[str] = None,
) -> str:
    """
    Save an insight to Cortex memory.

    Args:
        insight: The insight content
        files: File paths this insight is about (required)
        title: Optional title
        tags: Optional categorization tags
        repository: Repository identifier
        initiative: Initiative ID/name to tag (uses focused initiative if not specified)

    Returns:
        JSON with insight ID and save status
    """
    if not files:
        return json.dumps({
            "status": "error",
            "error": "files parameter is required and must be a non-empty list",
        })

    ctx = build_base_context(repository, initiative)
    logger.info(f"Saving insight: title='{title}', files={len(files)}, repository={ctx['repo']}")

    try:
        insight_id = f"insight:{uuid.uuid4().hex[:8]}"

        # Build document text
        doc_text = f"{title}\n\n" if title else ""
        doc_text += scrub_secrets(insight)
        doc_text += f"\n\nLinked files: {', '.join(files)}"

        # Compute file hashes for linked files (for staleness detection)
        file_hashes = compute_file_hashes(files, ctx["repo_path"])

        metadata = {
            "type": "insight",
            "title": title or "",
            "files": json.dumps(files),
            "tags": json.dumps(tags) if tags else "[]",
            "repository": ctx["repo"],
            "branch": ctx["branch"],
            "created_at": ctx["timestamp"],
            "updated_at": ctx["timestamp"],
            "verified_at": ctx["timestamp"],
            "status": "active",
            "file_hashes": json.dumps(file_hashes),
        }
        add_common_metadata(metadata, ctx)

        # Update initiative's updated_at timestamp if tagged
        if ctx["initiative_id"]:
            update_initiative_timestamp(ctx["collection"], ctx["initiative_id"], ctx["timestamp"])

        ctx["collection"].upsert(
            ids=[insight_id],
            documents=[doc_text],
            metadatas=[metadata],
        )
        get_searcher().build_index()

        logger.info(f"Insight saved: {insight_id}")

        response = {
            "status": "saved",
            "insight_id": insight_id,
            "type": "insight",
            "title": title,
            "files": files,
            "tags": tags or [],
        }
        if ctx["initiative_id"]:
            response["initiative"] = {
                "id": ctx["initiative_id"],
                "name": ctx["initiative_name"],
            }
            response["initiative_name"] = ctx["initiative_name"]

        return json.dumps(response, indent=2)

    except Exception as e:
        logger.error(f"Insight save error: {e}")
        return json.dumps({
            "status": "error",
            "error": str(e),
        })


# --- Backward Compatibility Aliases ---

def insight_to_cortex(
    insight: str,
    files: list[str],
    title: Optional[str] = None,
    tags: Optional[list[str]] = None,
    repository: Optional[str] = None,
    initiative: Optional[str] = None,
) -> str:
    """Backward-compatible alias for save_insight."""
    return save_insight(insight, files, title, tags, repository, initiative)


def save_note_to_cortex(
    content: str,
    title: Optional[str] = None,
    tags: Optional[list[str]] = None,
    repository: Optional[str] = None,
    initiative: Optional[str] = None,
) -> str:
    """Backward-compatible alias for save_note."""
    return save_note(content, title, tags, repository, initiative)
