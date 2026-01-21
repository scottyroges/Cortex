"""
Tests for maintenance tools (src/tools/maintenance/).
"""

import json
import pytest
from unittest.mock import MagicMock, patch


class TestCleanupStorage:
    """Tests for cleanup_storage function."""

    def test_cleanup_storage_requires_repository(self):
        """cleanup_storage returns error when repository is missing."""
        from src.tools.maintenance.maintenance import cleanup_storage

        result = json.loads(cleanup_storage(path="/some/path"))

        assert result["status"] == "error"
        assert "repository parameter is required" in result["error"]

    def test_cleanup_storage_requires_path(self):
        """cleanup_storage returns error when path is missing."""
        from src.tools.maintenance.maintenance import cleanup_storage

        result = json.loads(cleanup_storage(repository="test-repo"))

        assert result["status"] == "error"
        assert "path parameter is required" in result["error"]

    def test_cleanup_storage_preview_mode(self):
        """cleanup_storage preview mode shows what would be deleted."""
        from src.tools.maintenance.maintenance import cleanup_storage
        from src.tools.maintenance.orchestrator import CleanupResult

        mock_collection = MagicMock()
        mock_searcher = MagicMock()

        mock_cleanup_result = CleanupResult(
            file_metadata={"orphaned_count": 1, "deleted_count": 0},
            insights={"orphaned_count": 1, "deleted_count": 0},
            dependencies={"orphaned_count": 1, "deleted_count": 0},
            total_orphaned=3,
            total_deleted=0,
            index_rebuilt=False,
        )

        with patch("src.tools.maintenance.maintenance.get_collection", return_value=mock_collection), \
             patch("src.tools.maintenance.maintenance.get_searcher", return_value=mock_searcher), \
             patch("src.tools.maintenance.maintenance.run_cleanup", return_value=mock_cleanup_result):

            result = json.loads(cleanup_storage(
                action="preview",
                repository="test-repo",
                path="/test/repo",
            ))

            assert result["status"] == "success"
            assert result["action"] == "preview"
            assert result["total_orphaned"] == 3
            assert result["total_deleted"] == 0
            assert "Found 3 orphaned documents" in result["message"]

    def test_cleanup_storage_execute_mode(self):
        """cleanup_storage execute mode performs deletion."""
        from src.tools.maintenance.maintenance import cleanup_storage
        from src.tools.maintenance.orchestrator import CleanupResult

        mock_collection = MagicMock()
        mock_searcher = MagicMock()

        mock_cleanup_result = CleanupResult(
            file_metadata={"orphaned_count": 1, "deleted_count": 1},
            insights={"orphaned_count": 0, "deleted_count": 0},
            dependencies={"orphaned_count": 0, "deleted_count": 0},
            total_orphaned=1,
            total_deleted=1,
            index_rebuilt=True,
        )

        with patch("src.tools.maintenance.maintenance.get_collection", return_value=mock_collection), \
             patch("src.tools.maintenance.maintenance.get_searcher", return_value=mock_searcher), \
             patch("src.tools.maintenance.maintenance.run_cleanup", return_value=mock_cleanup_result):

            result = json.loads(cleanup_storage(
                action="execute",
                repository="test-repo",
                path="/test/repo",
            ))

            assert result["status"] == "success"
            assert result["action"] == "execute"
            assert result["total_orphaned"] == 1
            assert result["total_deleted"] == 1

    def test_cleanup_storage_no_orphans(self):
        """cleanup_storage reports when no orphans found."""
        from src.tools.maintenance.maintenance import cleanup_storage
        from src.tools.maintenance.orchestrator import CleanupResult

        mock_collection = MagicMock()
        mock_searcher = MagicMock()

        mock_cleanup_result = CleanupResult(
            file_metadata={"orphaned_count": 0, "deleted_count": 0},
            insights={"orphaned_count": 0, "deleted_count": 0},
            dependencies={"orphaned_count": 0, "deleted_count": 0},
            total_orphaned=0,
            total_deleted=0,
            index_rebuilt=False,
        )

        with patch("src.tools.maintenance.maintenance.get_collection", return_value=mock_collection), \
             patch("src.tools.maintenance.maintenance.get_searcher", return_value=mock_searcher), \
             patch("src.tools.maintenance.maintenance.run_cleanup", return_value=mock_cleanup_result):

            result = json.loads(cleanup_storage(
                action="preview",
                repository="test-repo",
                path="/test/repo",
            ))

            assert result["status"] == "success"
            assert result["total_orphaned"] == 0
            assert "message" not in result  # No message when nothing found

    def test_cleanup_storage_handles_exception(self):
        """cleanup_storage returns error on exception."""
        from src.tools.maintenance.maintenance import cleanup_storage

        with patch("src.tools.maintenance.maintenance.get_collection", side_effect=Exception("DB error")):

            result = json.loads(cleanup_storage(
                action="preview",
                repository="test-repo",
                path="/test/repo",
            ))

            assert result["status"] == "error"
            assert "DB error" in result["error"]


class TestDeleteDocument:
    """Tests for delete_document function."""

    def test_delete_document_requires_id(self):
        """delete_document returns error when document_id is missing."""
        from src.tools.maintenance.maintenance import delete_document

        result = json.loads(delete_document(""))

        assert result["status"] == "error"
        assert "document_id parameter is required" in result["error"]

    def test_delete_document_success(self):
        """delete_document succeeds with valid ID."""
        from src.tools.maintenance.maintenance import delete_document

        mock_collection = MagicMock()
        mock_searcher = MagicMock()

        delete_result = {
            "status": "deleted",
            "document_id": "note:abc123",
            "document_type": "note",
        }

        with patch("src.tools.maintenance.maintenance.get_collection", return_value=mock_collection), \
             patch("src.tools.maintenance.maintenance.get_searcher", return_value=mock_searcher), \
             patch("src.tools.maintenance.maintenance.delete_document_storage", return_value=delete_result):

            result = json.loads(delete_document("note:abc123"))

            assert result["status"] == "deleted"
            assert result["document_id"] == "note:abc123"
            # Should rebuild search index
            mock_searcher.build_index.assert_called_once()

    def test_delete_document_not_found(self):
        """delete_document returns error when document not found."""
        from src.tools.maintenance.maintenance import delete_document

        mock_collection = MagicMock()
        mock_searcher = MagicMock()

        delete_result = {
            "status": "error",
            "error": "Document not found: note:missing",
        }

        with patch("src.tools.maintenance.maintenance.get_collection", return_value=mock_collection), \
             patch("src.tools.maintenance.maintenance.get_searcher", return_value=mock_searcher), \
             patch("src.tools.maintenance.maintenance.delete_document_storage", return_value=delete_result):

            result = json.loads(delete_document("note:missing"))

            assert result["status"] == "error"
            assert "not found" in result["error"]
            # Should NOT rebuild search index on error
            mock_searcher.build_index.assert_not_called()

    def test_delete_document_handles_exception(self):
        """delete_document returns error on exception."""
        from src.tools.maintenance.maintenance import delete_document

        with patch("src.tools.maintenance.maintenance.get_collection", side_effect=Exception("DB connection failed")):

            result = json.loads(delete_document("note:abc123"))

            assert result["status"] == "error"
            assert "DB connection failed" in result["error"]


class TestDeleteDocumentStorage:
    """Tests for storage-level delete_document function."""

    def test_delete_document_storage_requires_id(self):
        """Storage delete_document returns error when ID is empty."""
        from src.storage.gc.purge import delete_document

        mock_collection = MagicMock()

        result = delete_document(mock_collection, "")

        assert result["status"] == "error"
        assert "document_id parameter is required" in result["error"]

    def test_delete_document_storage_not_found(self):
        """Storage delete_document returns error when document not found."""
        from src.storage.gc.purge import delete_document

        mock_collection = MagicMock()
        mock_collection.get.return_value = {"ids": [], "metadatas": []}

        result = delete_document(mock_collection, "note:missing")

        assert result["status"] == "error"
        assert "not found" in result["error"]

    def test_delete_document_storage_success(self):
        """Storage delete_document succeeds with valid document."""
        from src.storage.gc.purge import delete_document

        mock_collection = MagicMock()
        mock_collection.get.return_value = {
            "ids": ["note:abc123"],
            "metadatas": [{"type": "note", "title": "Test note"}],
        }

        result = delete_document(mock_collection, "note:abc123")

        assert result["status"] == "deleted"
        assert result["document_id"] == "note:abc123"
        assert result["document_type"] == "note"
        mock_collection.delete.assert_called_once_with(ids=["note:abc123"])

    def test_delete_document_storage_insight(self):
        """Storage delete_document handles insight type correctly."""
        from src.storage.gc.purge import delete_document

        mock_collection = MagicMock()
        mock_collection.get.return_value = {
            "ids": ["insight:def456"],
            "metadatas": [{"type": "insight", "files": '["src/a.py"]'}],
        }

        result = delete_document(mock_collection, "insight:def456")

        assert result["status"] == "deleted"
        assert result["document_type"] == "insight"

    def test_delete_document_storage_handles_exception(self):
        """Storage delete_document returns error on exception."""
        from src.storage.gc.purge import delete_document

        mock_collection = MagicMock()
        mock_collection.get.side_effect = Exception("ChromaDB error")

        result = delete_document(mock_collection, "note:abc123")

        assert result["status"] == "error"
        assert "ChromaDB error" in result["error"]


class TestCleanupOrchestrator:
    """Tests for the cleanup orchestrator."""

    def test_cleanup_result_dataclass(self):
        """CleanupResult dataclass works correctly."""
        from src.tools.maintenance.orchestrator import CleanupResult

        result = CleanupResult(
            file_metadata={"orphaned_count": 2, "deleted_count": 2, "ids": ["fm:1", "fm:2"]},
            insights={"orphaned_count": 1, "deleted_count": 1, "ids": ["i:1"]},
            dependencies={"orphaned_count": 0, "deleted_count": 0, "ids": []},
            total_orphaned=3,
            total_deleted=3,
            index_rebuilt=True,
        )

        assert result.file_metadata["orphaned_count"] == 2
        assert result.insights["orphaned_count"] == 1
        assert result.dependencies["orphaned_count"] == 0
        assert result.total_orphaned == 3
        assert result.total_deleted == 3
        assert result.index_rebuilt is True

    def test_run_cleanup_dry_run(self, temp_dir):
        """run_cleanup in dry_run mode doesn't delete."""
        from src.tools.maintenance.orchestrator import run_cleanup

        mock_collection = MagicMock()
        # Return some orphan candidates
        mock_collection.get.return_value = {
            "ids": ["file_metadata:deleted_file"],
            "metadatas": [{"type": "file_metadata", "path": str(temp_dir / "missing.py")}],
        }

        rebuild_fn = MagicMock()

        result = run_cleanup(
            collection=mock_collection,
            repo_path=str(temp_dir),
            repository="test-repo",
            dry_run=True,
            rebuild_index_fn=rebuild_fn,
        )

        # In dry_run, total_deleted should be 0
        assert result.total_deleted == 0
        # rebuild_index should NOT be called in dry_run
        rebuild_fn.assert_not_called()
        # Collection.delete should NOT be called
        mock_collection.delete.assert_not_called()

    def test_run_cleanup_execute(self, temp_dir):
        """run_cleanup in execute mode deletes orphans."""
        from src.tools.maintenance.orchestrator import run_cleanup

        mock_collection = MagicMock()
        # Return some orphan candidates
        mock_collection.get.return_value = {
            "ids": ["file_metadata:deleted_file"],
            "metadatas": [{"type": "file_metadata", "path": str(temp_dir / "missing.py")}],
        }

        rebuild_fn = MagicMock()

        result = run_cleanup(
            collection=mock_collection,
            repo_path=str(temp_dir),
            repository="test-repo",
            dry_run=False,
            rebuild_index_fn=rebuild_fn,
        )

        # In execute mode, total_deleted should match orphaned
        assert result.total_deleted == result.total_orphaned
        # rebuild_index SHOULD be called when items were deleted
        if result.total_deleted > 0:
            rebuild_fn.assert_called_once()
