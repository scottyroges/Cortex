"""
Tests for git detection functions (src/external/git/detection.py).
"""

import subprocess
from pathlib import Path

import pytest


class TestGitStalenessDetection:
    """Tests for git staleness detection functions."""

    def _get_head_commit(self, repo_path: Path) -> str:
        """Helper to get the current HEAD commit hash."""
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()

    def _get_default_branch(self, repo_path: Path) -> str:
        """Helper to get the default branch name (main or master)."""
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )
        branch = result.stdout.strip()
        if branch:
            return branch
        # Fallback: check if main or master exists
        result = subprocess.run(
            ["git", "branch", "--list", "main"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )
        if result.stdout.strip():
            return "main"
        return "master"

    def test_get_commits_since(self, temp_git_repo: Path):
        """Test counting commits since a commit hash."""
        from src.external.git.detection import get_commits_since

        # Get the initial commit hash before adding new commits
        initial_commit = self._get_head_commit(temp_git_repo)

        # Create some commits
        for i in range(3):
            test_file = temp_git_repo / f"file{i}.txt"
            test_file.write_text(f"content {i}")
            subprocess.run(["git", "add", "."], cwd=temp_git_repo, capture_output=True)
            subprocess.run(
                ["git", "commit", "-m", f"Commit {i}"],
                cwd=temp_git_repo,
                capture_output=True,
            )

        count = get_commits_since(str(temp_git_repo), initial_commit)
        # Should find exactly the 3 commits we just created
        assert count == 3

    def test_get_commits_since_no_new_commits(self, temp_git_repo: Path):
        """Test counting commits when there are none since the commit."""
        from src.external.git.detection import get_commits_since

        # Get the current HEAD - there should be no commits after it
        current_commit = self._get_head_commit(temp_git_repo)

        count = get_commits_since(str(temp_git_repo), current_commit)
        assert count == 0

    def test_get_merge_commits_since(self, temp_git_repo: Path):
        """Test counting merge commits since a commit hash."""
        from src.external.git.detection import get_merge_commits_since

        # Get the commit hash before creating the merge
        before_commit = self._get_head_commit(temp_git_repo)
        default_branch = self._get_default_branch(temp_git_repo)

        # Create a branch and merge it
        subprocess.run(
            ["git", "checkout", "-b", "feature"],
            cwd=temp_git_repo,
            capture_output=True,
        )
        test_file = temp_git_repo / "feature.txt"
        test_file.write_text("feature content")
        subprocess.run(["git", "add", "."], cwd=temp_git_repo, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Feature commit"],
            cwd=temp_git_repo,
            capture_output=True,
        )

        subprocess.run(
            ["git", "checkout", default_branch],
            cwd=temp_git_repo,
            capture_output=True,
        )

        subprocess.run(
            ["git", "merge", "feature", "--no-ff", "-m", "Merge feature"],
            cwd=temp_git_repo,
            capture_output=True,
        )

        count = get_merge_commits_since(str(temp_git_repo), before_commit)
        assert count >= 1

    def test_count_tracked_files(self, temp_git_repo: Path):
        """Test counting tracked files."""
        from src.external.git.detection import count_tracked_files

        # Initial repo has README.md
        initial_count = count_tracked_files(str(temp_git_repo))
        assert initial_count >= 1

        # Add more files
        for i in range(5):
            test_file = temp_git_repo / f"new_file{i}.txt"
            test_file.write_text(f"content {i}")
        subprocess.run(["git", "add", "."], cwd=temp_git_repo, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Add files"],
            cwd=temp_git_repo,
            capture_output=True,
        )

        new_count = count_tracked_files(str(temp_git_repo))
        assert new_count == initial_count + 5

    def test_count_tracked_files_non_git_dir(self, temp_dir: Path):
        """Test count_tracked_files returns 0 for non-git directory."""
        from src.external.git.detection import count_tracked_files

        count = count_tracked_files(str(temp_dir))
        assert count == 0

    def test_get_commits_since_non_git_dir(self, temp_dir: Path):
        """Test get_commits_since returns 0 for non-git directory."""
        from src.external.git.detection import get_commits_since

        # Use a fake commit hash - should return 0 for non-git dir regardless
        count = get_commits_since(str(temp_dir), "abc123")
        assert count == 0
