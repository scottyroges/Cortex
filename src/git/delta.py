"""
Git Delta Sync Utilities

Functions for tracking file changes between commits.
"""

import os
from typing import Optional

from src.configs import get_logger
from src.git.subprocess_utils import git_diff_name_status, git_list_files

logger = get_logger("git.delta")


def get_git_changed_files(
    path: str,
    since_commit: Optional[str],
) -> tuple[list[str], list[str], list[tuple[str, str]]]:
    """
    Get files changed since a commit using git.

    Args:
        path: Repository root path
        since_commit: Commit to compare against (None = all files)

    Returns:
        Tuple of (modified_files, deleted_files, renamed_files)
        - modified_files: Files that were added or modified
        - deleted_files: Files that were deleted
        - renamed_files: List of (old_path, new_path) tuples
    """
    if not since_commit:
        return [], [], []

    returncode, stdout, stderr = git_diff_name_status(path, since_commit)
    if returncode != 0:
        logger.warning(f"git diff failed: {stderr}")
        return [], [], []

    modified = []
    deleted = []
    renamed = []

    for line in stdout.strip().split("\n"):
        if not line:
            continue

        parts = line.split("\t")
        status = parts[0]

        if status.startswith("R"):
            # Rename: R100\told_path\tnew_path
            if len(parts) >= 3:
                old_path = os.path.join(path, parts[1])
                new_path = os.path.join(path, parts[2])
                renamed.append((old_path, new_path))
                modified.append(new_path)  # Also index the new location
        elif status == "D":
            # Deleted
            deleted.append(os.path.join(path, parts[1]))
        elif status in ("A", "M", "T"):
            # Added, Modified, or Type changed
            modified.append(os.path.join(path, parts[1]))

    return modified, deleted, renamed


def get_untracked_files(path: str) -> list[str]:
    """
    Get untracked files that should be indexed.

    Args:
        path: Repository root path

    Returns:
        List of absolute paths to untracked files
    """
    return git_list_files(
        ["ls-files", "--others", "--exclude-standard"],
        path,
        prefix_with_path=True,
        timeout=30,
    )
