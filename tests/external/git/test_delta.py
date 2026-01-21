"""
Tests for git delta sync functions (src/external/git/).
"""

from pathlib import Path

import pytest

from src.external.git import get_git_changed_files, get_head_commit, get_untracked_files, is_git_repo


class TestGitIntegration:
    """Tests for git-based delta sync."""

    def test_is_git_repo_true(self, temp_dir: Path):
        """Test git repo detection in actual git repo."""
        import subprocess

        # Initialize a git repo
        subprocess.run(["git", "init"], cwd=temp_dir, capture_output=True)

        assert is_git_repo(str(temp_dir)) is True

    def test_is_git_repo_false(self, temp_dir: Path):
        """Test git repo detection in non-git directory."""
        assert is_git_repo(str(temp_dir)) is False

    def test_get_head_commit(self, temp_dir: Path):
        """Test getting HEAD commit hash."""
        import subprocess

        # Initialize git repo with a commit
        subprocess.run(["git", "init"], cwd=temp_dir, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=temp_dir,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=temp_dir,
            capture_output=True,
        )
        (temp_dir / "test.txt").write_text("content")
        subprocess.run(["git", "add", "."], cwd=temp_dir, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "initial"],
            cwd=temp_dir,
            capture_output=True,
        )

        commit = get_head_commit(str(temp_dir))

        assert commit is not None
        assert len(commit) == 40  # SHA-1 hash length

    def test_get_head_commit_no_commits(self, temp_dir: Path):
        """Test HEAD commit in repo with no commits."""
        import subprocess

        subprocess.run(["git", "init"], cwd=temp_dir, capture_output=True)

        commit = get_head_commit(str(temp_dir))

        assert commit is None

    def test_get_git_changed_files(self, temp_dir: Path):
        """Test git-based change detection."""
        import subprocess

        # Initialize git repo with initial commit
        subprocess.run(["git", "init"], cwd=temp_dir, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=temp_dir,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=temp_dir,
            capture_output=True,
        )
        (temp_dir / "file1.py").write_text("original")
        subprocess.run(["git", "add", "."], cwd=temp_dir, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "initial"],
            cwd=temp_dir,
            capture_output=True,
        )

        initial_commit = get_head_commit(str(temp_dir))

        # Make changes: modify file1, add file2, delete file3
        (temp_dir / "file1.py").write_text("modified")
        (temp_dir / "file2.py").write_text("new file")
        subprocess.run(["git", "add", "."], cwd=temp_dir, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "changes"],
            cwd=temp_dir,
            capture_output=True,
        )

        modified, deleted, renamed = get_git_changed_files(str(temp_dir), initial_commit)

        assert any("file1.py" in f for f in modified)
        assert any("file2.py" in f for f in modified)
        assert deleted == []
        assert renamed == []

    def test_get_git_changed_files_with_delete(self, temp_dir: Path):
        """Test git detects deleted files."""
        import subprocess

        # Initialize git repo
        subprocess.run(["git", "init"], cwd=temp_dir, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=temp_dir,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=temp_dir,
            capture_output=True,
        )
        (temp_dir / "to_delete.py").write_text("will be deleted")
        (temp_dir / "keep.py").write_text("keep this")
        subprocess.run(["git", "add", "."], cwd=temp_dir, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "initial"],
            cwd=temp_dir,
            capture_output=True,
        )

        initial_commit = get_head_commit(str(temp_dir))

        # Delete file
        (temp_dir / "to_delete.py").unlink()
        subprocess.run(["git", "add", "."], cwd=temp_dir, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "delete file"],
            cwd=temp_dir,
            capture_output=True,
        )

        modified, deleted, renamed = get_git_changed_files(str(temp_dir), initial_commit)

        assert any("to_delete.py" in f for f in deleted)
        assert not any("keep.py" in f for f in deleted)

    def test_get_git_changed_files_with_rename(self, temp_dir: Path):
        """Test git detects renamed files."""
        import subprocess

        # Initialize git repo
        subprocess.run(["git", "init"], cwd=temp_dir, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=temp_dir,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=temp_dir,
            capture_output=True,
        )
        (temp_dir / "old_name.py").write_text("content")
        subprocess.run(["git", "add", "."], cwd=temp_dir, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "initial"],
            cwd=temp_dir,
            capture_output=True,
        )

        initial_commit = get_head_commit(str(temp_dir))

        # Rename file
        (temp_dir / "old_name.py").rename(temp_dir / "new_name.py")
        subprocess.run(["git", "add", "."], cwd=temp_dir, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "rename file"],
            cwd=temp_dir,
            capture_output=True,
        )

        modified, deleted, renamed = get_git_changed_files(str(temp_dir), initial_commit)

        # Renamed files should appear in renamed list
        assert len(renamed) == 1
        old_path, new_path = renamed[0]
        assert "old_name.py" in old_path
        assert "new_name.py" in new_path
        # New path should also be in modified for indexing
        assert any("new_name.py" in f for f in modified)

    def test_get_untracked_files(self, temp_dir: Path):
        """Test detection of untracked files."""
        import os
        import subprocess

        subprocess.run(["git", "init"], cwd=temp_dir, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=temp_dir,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=temp_dir,
            capture_output=True,
        )

        # Create initial tracked file
        (temp_dir / "committed_file.py").write_text("tracked")
        subprocess.run(["git", "add", "."], cwd=temp_dir, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "initial"],
            cwd=temp_dir,
            capture_output=True,
        )

        # Add untracked file
        (temp_dir / "new_untracked.py").write_text("untracked")

        untracked = get_untracked_files(str(temp_dir))

        # Check by filename to avoid path substring issues
        untracked_names = [os.path.basename(f) for f in untracked]
        assert "new_untracked.py" in untracked_names
        assert "committed_file.py" not in untracked_names
