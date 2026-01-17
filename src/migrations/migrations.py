"""
Individual Migrations

Each migration is a function that modifies the database/state.
Migrations should be idempotent where possible.
"""

from logging_config import get_logger

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
