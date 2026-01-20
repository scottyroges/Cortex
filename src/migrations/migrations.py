"""
Individual Migrations

Each migration is a function that modifies the database/state.
Migrations should be idempotent where possible.
"""

from src.configs import get_logger

logger = get_logger("migrations")


def migration_001_initial():
    """
    Initial migration - establishes schema versioning.

    This migration doesn't change data structure, it just confirms
    the current state is compatible with v1 schema.
    """
    # No-op for initial migration
    # Future: could validate existing data structure
    logger.info("Established schema versioning at v1")


def migration_002_commit_to_session_summary():
    """
    Rename document type 'commit' to 'session_summary'.

    This migration:
    1. Finds all documents with type="commit"
    2. Updates metadata type to "session_summary"
    3. Updates document IDs from "commit:xxx" to "session_summary:xxx"

    The migration is idempotent - safe to run multiple times.
    """
    from src.tools.services import get_collection

    collection = get_collection()

    # Query all documents with type="commit"
    try:
        results = collection.get(
            where={"type": "commit"},
            include=["documents", "metadatas", "embeddings"],
        )
    except Exception as e:
        # No documents with type="commit" - nothing to migrate
        logger.info(f"No documents to migrate (query returned: {e})")
        return

    ids = results.get("ids", [])
    documents = results.get("documents", [])
    metadatas = results.get("metadatas", [])
    embeddings = results.get("embeddings", [])

    if not ids:
        logger.info("No documents with type='commit' found - nothing to migrate")
        return

    logger.info(f"Found {len(ids)} documents with type='commit' to migrate")

    migrated = 0
    skipped = 0

    for i, doc_id in enumerate(ids):
        old_metadata = metadatas[i]
        document = documents[i] if documents is not None else None
        embedding = embeddings[i] if embeddings is not None else None

        # Generate new ID
        if doc_id.startswith("commit:"):
            new_id = "session_summary:" + doc_id[7:]
        else:
            new_id = "session_summary:" + doc_id

        # Check if new ID already exists (migration already ran for this doc)
        existing = collection.get(ids=[new_id])
        if existing["ids"]:
            logger.debug(f"Skipping {doc_id} -> {new_id} (already exists)")
            skipped += 1
            continue

        # Update metadata
        new_metadata = dict(old_metadata)
        new_metadata["type"] = "session_summary"

        # Delete old document
        collection.delete(ids=[doc_id])

        # Add with new ID and metadata
        add_kwargs = {
            "ids": [new_id],
            "metadatas": [new_metadata],
        }
        if document is not None:
            add_kwargs["documents"] = [document]
        if embedding is not None:
            add_kwargs["embeddings"] = [embedding]

        collection.add(**add_kwargs)
        migrated += 1
        logger.debug(f"Migrated {doc_id} -> {new_id}")

    logger.info(f"Migration complete: {migrated} migrated, {skipped} skipped (already migrated)")


# Future migrations follow this pattern:
#
# def migration_002_add_field():
#     """Add new_field to all documents of type X."""
#     from src.tools.services import get_collection
#     collection = get_collection()
#
#     # Query documents that need migration
#     results = collection.get(where={"type": "insight"})
#
#     # Update each document
#     for doc_id, metadata in zip(results["ids"], results["metadatas"]):
#         if "new_field" not in metadata:
#             collection.update(
#                 ids=[doc_id],
#                 metadatas=[{**metadata, "new_field": "default_value"}]
#             )
#
#     logger.info(f"Migrated {len(results['ids'])} documents")
