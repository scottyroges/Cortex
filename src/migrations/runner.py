"""
Migration Runner

Handles schema versioning and migration execution.
"""

import json
import os
from datetime import datetime, timezone
from typing import Callable, Optional

from logging_config import get_logger
from src.config import DB_PATH

logger = get_logger("migrations")

# Current schema version - increment when adding migrations
SCHEMA_VERSION = 1

# Schema version file name
SCHEMA_VERSION_FILE = "schema_version.json"


def get_schema_version_path() -> str:
    """Get path to schema version file."""
    return os.path.join(os.path.expanduser(DB_PATH), SCHEMA_VERSION_FILE)


def get_current_schema_version() -> int:
    """
    Get the current schema version from disk.

    Returns:
        Current schema version (0 if not set)
    """
    path = get_schema_version_path()
    if not os.path.exists(path):
        return 0

    try:
        with open(path, "r") as f:
            data = json.load(f)
            return data.get("version", 0)
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Failed to read schema version: {e}")
        return 0


def save_schema_version(version: int) -> None:
    """Save schema version to disk."""
    path = get_schema_version_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)

    data = {
        "version": version,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    # Atomic write
    temp_path = path + ".tmp"
    with open(temp_path, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(temp_path, path)


def needs_migration() -> bool:
    """Check if migrations are needed."""
    current = get_current_schema_version()
    return current < SCHEMA_VERSION


def get_migrations() -> list[tuple[int, str, Callable]]:
    """
    Get list of migrations to run.

    Returns:
        List of (version, description, migration_function) tuples
    """
    from src.migrations import migrations as m

    return [
        (1, "Initial schema version tracking", m.migration_001_initial),
        # Future migrations added here:
        # (2, "Add insight staleness tracking", m.migration_002_insights),
    ]


def run_migrations(
    from_version: Optional[int] = None,
    dry_run: bool = False,
) -> dict:
    """
    Run pending migrations.

    Args:
        from_version: Override starting version (for testing)
        dry_run: If True, don't apply changes

    Returns:
        Dict with migration results
    """
    current = from_version if from_version is not None else get_current_schema_version()
    migrations = get_migrations()

    # Filter to pending migrations
    pending = [(v, desc, fn) for v, desc, fn in migrations if v > current]

    if not pending:
        return {
            "status": "up_to_date",
            "current_version": current,
            "target_version": SCHEMA_VERSION,
            "migrations_run": 0,
        }

    logger.info(f"Running {len(pending)} migrations (from v{current} to v{SCHEMA_VERSION})")

    results = []
    final_version = current

    for version, description, migration_fn in pending:
        logger.info(f"Running migration {version}: {description}")

        if dry_run:
            results.append({"version": version, "description": description, "status": "dry_run"})
            continue

        try:
            migration_fn()
            save_schema_version(version)
            final_version = version
            results.append({"version": version, "description": description, "status": "success"})
            logger.info(f"Migration {version} complete")
        except Exception as e:
            logger.error(f"Migration {version} failed: {e}")
            results.append({"version": version, "description": description, "status": "failed", "error": str(e)})
            break

    return {
        "status": "complete" if final_version == SCHEMA_VERSION else "partial",
        "current_version": final_version,
        "target_version": SCHEMA_VERSION,
        "migrations_run": len([r for r in results if r["status"] == "success"]),
        "results": results,
    }
