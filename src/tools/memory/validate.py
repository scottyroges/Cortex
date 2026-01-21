"""
Insight Validation Operations

Functions for validating and managing insight lifecycle.
"""

import json
from datetime import datetime, timezone
from typing import Optional

from src.configs import get_logger
from src.configs.services import get_collection, get_repo_path, get_searcher
from src.external.git import get_head_commit

from .helpers import resolve_repository, compute_file_hashes
from .save import save_insight

logger = get_logger("tools.memory")


def validate_insight(
    insight_id: str,
    validation_result: str,
    notes: Optional[str] = None,
    deprecate: bool = False,
    replacement_insight: Optional[str] = None,
    repository: Optional[str] = None,
) -> str:
    """
    Validate a stored insight and optionally update its status.

    Call this after re-reading linked files to verify whether a stale
    insight is still accurate.

    Args:
        insight_id: The insight ID to validate (e.g., "insight:abc123")
        validation_result: Assessment result - one of:
            - "still_valid": Insight is still accurate
            - "partially_valid": Some parts are still accurate
            - "no_longer_valid": Insight is outdated/wrong
        notes: Optional notes about the validation
        deprecate: If True and result is "no_longer_valid", mark as deprecated
        replacement_insight: If deprecating, new insight content to save as replacement
        repository: Repository identifier (optional)

    Returns:
        JSON with validation status and any actions taken
    """
    repo = resolve_repository(repository)

    logger.info(f"Validating insight: {insight_id}, result={validation_result}")

    try:
        collection = get_collection()
        repo_path = get_repo_path()
        timestamp = datetime.now(timezone.utc).isoformat()

        # Fetch the insight
        result = collection.get(
            ids=[insight_id],
            include=["documents", "metadatas"],
        )

        if not result["ids"]:
            return json.dumps({
                "status": "error",
                "error": f"Insight not found: {insight_id}",
            })

        meta = result["metadatas"][0]
        doc = result["documents"][0]

        # Verify it's actually an insight
        if meta.get("type") != "insight":
            return json.dumps({
                "status": "error",
                "error": f"Document {insight_id} is not an insight (type={meta.get('type')})",
            })

        # Update timestamps
        meta["verified_at"] = timestamp
        meta["updated_at"] = timestamp
        meta["last_validation_result"] = validation_result
        # Backfill created_at if missing
        if not meta.get("created_at"):
            meta["created_at"] = timestamp
        if notes:
            meta["validation_notes"] = notes

        response = {
            "status": "validated",
            "insight_id": insight_id,
            "validation_result": validation_result,
            "verified_at": timestamp,
        }

        # Handle deprecation
        if validation_result == "no_longer_valid" and deprecate:
            meta["status"] = "deprecated"
            meta["deprecated_at"] = timestamp
            meta["deprecation_reason"] = notes or "Marked invalid during validation"
            response["deprecated"] = True
            logger.info(f"Deprecated insight: {insight_id}")

            # Create replacement if provided
            if replacement_insight:
                linked_files = json.loads(meta.get("files", "[]"))
                tags = json.loads(meta.get("tags", "[]"))

                new_result_json = save_insight(
                    insight=replacement_insight,
                    files=linked_files,
                    title=meta.get("title", "") + " (Updated)" if meta.get("title") else None,
                    tags=tags,
                    repository=meta.get("repository", repo),
                )
                new_result = json.loads(new_result_json)

                if new_result.get("status") == "saved":
                    meta["superseded_by"] = new_result["insight_id"]
                    response["replacement_id"] = new_result["insight_id"]
                    logger.info(f"Created replacement insight: {new_result['insight_id']}")

        elif validation_result == "still_valid":
            # Refresh file hashes to current state
            linked_files = json.loads(meta.get("files", "[]"))

            if linked_files and repo_path:
                new_hashes = compute_file_hashes(linked_files, repo_path)
                if new_hashes:
                    meta["file_hashes"] = json.dumps(new_hashes)
                    response["file_hashes_refreshed"] = True

            # Update commit reference for validation tracking
            current_commit = get_head_commit(repo_path) if repo_path else None
            if current_commit:
                meta["validated_commit"] = current_commit

            logger.info(f"Validated insight as still valid: {insight_id}")

        # Save updated metadata
        collection.upsert(
            ids=[insight_id],
            documents=[doc],
            metadatas=[meta],
        )

        # Rebuild search index
        get_searcher().build_index()

        return json.dumps(response, indent=2)

    except Exception as e:
        logger.error(f"Validate insight error: {e}")
        return json.dumps({
            "status": "error",
            "error": str(e),
        })
