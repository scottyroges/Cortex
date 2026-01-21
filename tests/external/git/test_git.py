"""
Tests for git utility functions (src/external/git/).
"""

from pathlib import Path

import pytest

from src.external.git import get_current_branch, get_git_info


class TestGitDetection:
    """Tests for git information detection."""

    def test_git_repo_detection(self, temp_git_repo: Path):
        """Test detection of git repository."""
        branch, is_git, root = get_git_info(str(temp_git_repo))
        assert is_git is True
        # Resolve both paths to handle macOS /var -> /private/var symlink
        assert Path(root).resolve() == temp_git_repo.resolve()
        # Branch should be main or master (depends on git config)
        assert branch in ["main", "master"]

    def test_non_git_directory(self, temp_dir: Path):
        """Test non-git directory returns appropriate values."""
        branch, is_git, root = get_git_info(str(temp_dir))
        assert is_git is False
        assert branch is None
        assert root is None

    def test_get_current_branch_git(self, temp_git_repo: Path):
        """Test get_current_branch in a git repo."""
        branch = get_current_branch(str(temp_git_repo))
        assert branch in ["main", "master"]

    def test_get_current_branch_non_git(self, temp_dir: Path):
        """Test get_current_branch in a non-git directory."""
        branch = get_current_branch(str(temp_dir))
        assert branch == "unknown"
