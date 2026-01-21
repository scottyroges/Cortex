"""
Session Summary Operations

Functions for saving end-of-session summaries to Cortex memory.
"""

import json
import uuid
from typing import Optional

from src.configs import get_logger
from src.configs.services import get_searcher
from src.utils.secret_scrubber import scrub_secrets

from .helpers import (
    build_base_context,
    add_common_metadata,
    update_initiative_timestamp,
)

logger = get_logger("tools.memory")


def conclude_session(
    summary: str,
    changed_files: list[str],
    repository: Optional[str] = None,
    initiative: Optional[str] = None,
) -> str:
    """
    Save end-of-session summary to Cortex memory.

    **When to use this tool:**
    - Ending a coding session and want to preserve context
    - Capturing decisions, problems solved, and understanding
    - Recording what files changed and why

    Call this BEFORE ending the session to ensure context is captured.

    Args:
        summary: Detailed summary of what was done and why
        changed_files: List of file paths that were modified
        repository: Repository identifier
        initiative: Initiative to tag (uses focused if not specified)

    Returns:
        JSON with session summary status
    """
    ctx = build_base_context(repository, initiative)
    logger.info(f"Saving session summary to Cortex: {len(changed_files)} files, repository={ctx['repo']}")

    try:
        doc_id = f"session_summary:{uuid.uuid4().hex[:8]}"

        metadata = {
            "type": "session_summary",
            "repository": ctx["repo"],
            "branch": ctx["branch"],
            "files": json.dumps(changed_files),
            "created_at": ctx["timestamp"],
            "updated_at": ctx["timestamp"],
            "status": "active",
        }
        add_common_metadata(metadata, ctx)

        # Update initiative's updated_at timestamp if tagged
        if ctx["initiative_id"]:
            update_initiative_timestamp(ctx["collection"], ctx["initiative_id"], ctx["timestamp"])

        ctx["collection"].upsert(
            ids=[doc_id],
            documents=[f"Session Summary:\n\n{scrub_secrets(summary)}\n\nChanged files: {', '.join(changed_files)}"],
            metadatas=[metadata],
        )
        logger.debug(f"Saved session summary: {doc_id}")
        get_searcher().build_index()

        logger.info(f"Session summary complete: {doc_id}")

        response = {
            "status": "success",
            "session_id": doc_id,
            "summary_saved": True,
            "files_recorded": len(changed_files),
        }

        if ctx["initiative_id"]:
            from src.tools.initiatives import detect_completion_signals
            completion_detected = detect_completion_signals(summary)

            response["initiative"] = {
                "id": ctx["initiative_id"],
                "name": ctx["initiative_name"],
                "completion_signal_detected": completion_detected,
            }
            if completion_detected:
                response["initiative"]["prompt"] = "mark_complete"

        return json.dumps(response, indent=2)

    except Exception as e:
        logger.error(f"Session summary error: {e}")
        return json.dumps({
            "status": "error",
            "error": str(e),
        })


# --- Backward Compatibility Alias ---

def session_summary_to_cortex(
    summary: str,
    changed_files: list[str],
    repository: Optional[str] = None,
    initiative: Optional[str] = None,
) -> str:
    """Backward-compatible alias for conclude_session."""
    return conclude_session(summary, changed_files, repository, initiative)
