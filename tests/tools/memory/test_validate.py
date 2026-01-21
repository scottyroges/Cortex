"""
Tests for insight validation (src/tools/memory/validate.py).
"""

import json
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch


class TestValidateInsight:
    """Tests for the validate_insight function."""

    def test_validate_insight_not_found(self):
        """validate_insight returns error when insight not found."""
        from src.tools.memory.validate import validate_insight

        mock_collection = MagicMock()
        mock_collection.get.return_value = {"ids": [], "documents": [], "metadatas": []}

        with patch("src.tools.memory.validate.get_collection", return_value=mock_collection), \
             patch("src.tools.memory.validate.resolve_repository", return_value="test-repo"):

            result = json.loads(validate_insight(
                insight_id="insight:missing",
                validation_result="still_valid",
            ))

            assert result["status"] == "error"
            assert "not found" in result["error"]

    def test_validate_insight_wrong_type(self):
        """validate_insight returns error when document is not an insight."""
        from src.tools.memory.validate import validate_insight

        mock_collection = MagicMock()
        mock_collection.get.return_value = {
            "ids": ["note:abc123"],
            "documents": ["This is a note"],
            "metadatas": [{"type": "note", "title": "Test note"}],
        }

        with patch("src.tools.memory.validate.get_collection", return_value=mock_collection), \
             patch("src.tools.memory.validate.resolve_repository", return_value="test-repo"), \
             patch("src.tools.memory.validate.get_repo_path", return_value="/test/repo"):

            result = json.loads(validate_insight(
                insight_id="note:abc123",
                validation_result="still_valid",
            ))

            assert result["status"] == "error"
            assert "not an insight" in result["error"]

    def test_validate_insight_still_valid(self):
        """validate_insight marks insight as still valid."""
        from src.tools.memory.validate import validate_insight

        mock_collection = MagicMock()
        mock_collection.get.return_value = {
            "ids": ["insight:abc123"],
            "documents": ["This insight describes pattern X"],
            "metadatas": [{
                "type": "insight",
                "files": '["src/a.py"]',
                "created_at": "2024-01-01T00:00:00Z",
            }],
        }
        mock_searcher = MagicMock()

        with patch("src.tools.memory.validate.get_collection", return_value=mock_collection), \
             patch("src.tools.memory.validate.get_searcher", return_value=mock_searcher), \
             patch("src.tools.memory.validate.get_repo_path", return_value="/test/repo"), \
             patch("src.tools.memory.validate.get_head_commit", return_value="abc123"), \
             patch("src.tools.memory.validate.compute_file_hashes", return_value={"src/a.py": "hash1"}), \
             patch("src.tools.memory.validate.resolve_repository", return_value="test-repo"):

            result = json.loads(validate_insight(
                insight_id="insight:abc123",
                validation_result="still_valid",
            ))

            assert result["status"] == "validated"
            assert result["validation_result"] == "still_valid"
            assert result["insight_id"] == "insight:abc123"
            assert "verified_at" in result

            # Should update metadata
            mock_collection.upsert.assert_called_once()
            call_kwargs = mock_collection.upsert.call_args[1]
            meta = call_kwargs["metadatas"][0]
            assert meta["last_validation_result"] == "still_valid"
            assert "verified_at" in meta

            # Should rebuild search index
            mock_searcher.build_index.assert_called_once()

    def test_validate_insight_still_valid_refreshes_hashes(self):
        """validate_insight refreshes file hashes when marked still_valid."""
        from src.tools.memory.validate import validate_insight

        mock_collection = MagicMock()
        mock_collection.get.return_value = {
            "ids": ["insight:abc123"],
            "documents": ["This insight describes pattern X"],
            "metadatas": [{
                "type": "insight",
                "files": '["src/a.py", "src/b.py"]',
                "file_hashes": '{"src/a.py": "old_hash"}',
                "created_at": "2024-01-01T00:00:00Z",
            }],
        }
        mock_searcher = MagicMock()

        new_hashes = {"src/a.py": "new_hash", "src/b.py": "hash2"}

        with patch("src.tools.memory.validate.get_collection", return_value=mock_collection), \
             patch("src.tools.memory.validate.get_searcher", return_value=mock_searcher), \
             patch("src.tools.memory.validate.get_repo_path", return_value="/test/repo"), \
             patch("src.tools.memory.validate.get_head_commit", return_value="def456"), \
             patch("src.tools.memory.validate.compute_file_hashes", return_value=new_hashes), \
             patch("src.tools.memory.validate.resolve_repository", return_value="test-repo"):

            result = json.loads(validate_insight(
                insight_id="insight:abc123",
                validation_result="still_valid",
            ))

            assert result["file_hashes_refreshed"] is True

            call_kwargs = mock_collection.upsert.call_args[1]
            meta = call_kwargs["metadatas"][0]
            assert "new_hash" in meta["file_hashes"]
            assert meta["validated_commit"] == "def456"

    def test_validate_insight_partially_valid(self):
        """validate_insight handles partially_valid status."""
        from src.tools.memory.validate import validate_insight

        mock_collection = MagicMock()
        mock_collection.get.return_value = {
            "ids": ["insight:abc123"],
            "documents": ["This insight is partially accurate"],
            "metadatas": [{
                "type": "insight",
                "files": '["src/a.py"]',
            }],
        }
        mock_searcher = MagicMock()

        with patch("src.tools.memory.validate.get_collection", return_value=mock_collection), \
             patch("src.tools.memory.validate.get_searcher", return_value=mock_searcher), \
             patch("src.tools.memory.validate.get_repo_path", return_value="/test/repo"), \
             patch("src.tools.memory.validate.resolve_repository", return_value="test-repo"):

            result = json.loads(validate_insight(
                insight_id="insight:abc123",
                validation_result="partially_valid",
                notes="The main pattern is correct but some details changed",
            ))

            assert result["status"] == "validated"
            assert result["validation_result"] == "partially_valid"

            call_kwargs = mock_collection.upsert.call_args[1]
            meta = call_kwargs["metadatas"][0]
            assert meta["last_validation_result"] == "partially_valid"
            assert meta["validation_notes"] == "The main pattern is correct but some details changed"

    def test_validate_insight_no_longer_valid(self):
        """validate_insight handles no_longer_valid status."""
        from src.tools.memory.validate import validate_insight

        mock_collection = MagicMock()
        mock_collection.get.return_value = {
            "ids": ["insight:abc123"],
            "documents": ["This insight is outdated"],
            "metadatas": [{
                "type": "insight",
                "files": '["src/a.py"]',
            }],
        }
        mock_searcher = MagicMock()

        with patch("src.tools.memory.validate.get_collection", return_value=mock_collection), \
             patch("src.tools.memory.validate.get_searcher", return_value=mock_searcher), \
             patch("src.tools.memory.validate.get_repo_path", return_value="/test/repo"), \
             patch("src.tools.memory.validate.resolve_repository", return_value="test-repo"):

            result = json.loads(validate_insight(
                insight_id="insight:abc123",
                validation_result="no_longer_valid",
            ))

            assert result["status"] == "validated"
            assert result["validation_result"] == "no_longer_valid"
            # Should NOT be deprecated unless deprecate=True
            assert "deprecated" not in result

    def test_validate_insight_deprecate(self):
        """validate_insight deprecates insight when deprecate=True."""
        from src.tools.memory.validate import validate_insight

        mock_collection = MagicMock()
        mock_collection.get.return_value = {
            "ids": ["insight:abc123"],
            "documents": ["This insight is outdated"],
            "metadatas": [{
                "type": "insight",
                "files": '["src/a.py"]',
                "tags": '["architecture"]',
            }],
        }
        mock_searcher = MagicMock()

        with patch("src.tools.memory.validate.get_collection", return_value=mock_collection), \
             patch("src.tools.memory.validate.get_searcher", return_value=mock_searcher), \
             patch("src.tools.memory.validate.get_repo_path", return_value="/test/repo"), \
             patch("src.tools.memory.validate.resolve_repository", return_value="test-repo"):

            result = json.loads(validate_insight(
                insight_id="insight:abc123",
                validation_result="no_longer_valid",
                deprecate=True,
                notes="The architecture changed completely",
            ))

            assert result["status"] == "validated"
            assert result["deprecated"] is True

            call_kwargs = mock_collection.upsert.call_args[1]
            meta = call_kwargs["metadatas"][0]
            assert meta["status"] == "deprecated"
            assert "deprecated_at" in meta
            assert "The architecture changed completely" in meta["deprecation_reason"]

    def test_validate_insight_deprecate_with_replacement(self):
        """validate_insight creates replacement when provided."""
        from src.tools.memory.validate import validate_insight

        mock_collection = MagicMock()
        mock_collection.get.return_value = {
            "ids": ["insight:abc123"],
            "documents": ["Old insight about pattern X"],
            "metadatas": [{
                "type": "insight",
                "files": '["src/a.py"]',
                "tags": '["patterns"]',
                "title": "Pattern X",
                "repository": "test-repo",
            }],
        }
        mock_searcher = MagicMock()

        # Mock save_insight to return a new insight ID
        mock_save_result = json.dumps({
            "status": "saved",
            "insight_id": "insight:new456",
        })

        with patch("src.tools.memory.validate.get_collection", return_value=mock_collection), \
             patch("src.tools.memory.validate.get_searcher", return_value=mock_searcher), \
             patch("src.tools.memory.validate.get_repo_path", return_value="/test/repo"), \
             patch("src.tools.memory.validate.resolve_repository", return_value="test-repo"), \
             patch("src.tools.memory.validate.save_insight", return_value=mock_save_result):

            result = json.loads(validate_insight(
                insight_id="insight:abc123",
                validation_result="no_longer_valid",
                deprecate=True,
                replacement_insight="New understanding of pattern X with updated details",
            ))

            assert result["status"] == "validated"
            assert result["deprecated"] is True
            assert result["replacement_id"] == "insight:new456"

            # Old insight should point to replacement
            call_kwargs = mock_collection.upsert.call_args[1]
            meta = call_kwargs["metadatas"][0]
            assert meta["superseded_by"] == "insight:new456"

    def test_validate_insight_with_notes(self):
        """validate_insight stores validation notes."""
        from src.tools.memory.validate import validate_insight

        mock_collection = MagicMock()
        mock_collection.get.return_value = {
            "ids": ["insight:abc123"],
            "documents": ["Test insight"],
            "metadatas": [{"type": "insight", "files": '[]'}],
        }
        mock_searcher = MagicMock()

        with patch("src.tools.memory.validate.get_collection", return_value=mock_collection), \
             patch("src.tools.memory.validate.get_searcher", return_value=mock_searcher), \
             patch("src.tools.memory.validate.get_repo_path", return_value="/test/repo"), \
             patch("src.tools.memory.validate.resolve_repository", return_value="test-repo"):

            result = json.loads(validate_insight(
                insight_id="insight:abc123",
                validation_result="still_valid",
                notes="Verified after reviewing src/a.py changes",
            ))

            assert result["status"] == "validated"

            call_kwargs = mock_collection.upsert.call_args[1]
            meta = call_kwargs["metadatas"][0]
            assert meta["validation_notes"] == "Verified after reviewing src/a.py changes"

    def test_validate_insight_backfills_created_at(self):
        """validate_insight backfills created_at if missing."""
        from src.tools.memory.validate import validate_insight

        mock_collection = MagicMock()
        mock_collection.get.return_value = {
            "ids": ["insight:abc123"],
            "documents": ["Old insight without created_at"],
            "metadatas": [{
                "type": "insight",
                "files": '[]',
                # No created_at field
            }],
        }
        mock_searcher = MagicMock()

        with patch("src.tools.memory.validate.get_collection", return_value=mock_collection), \
             patch("src.tools.memory.validate.get_searcher", return_value=mock_searcher), \
             patch("src.tools.memory.validate.get_repo_path", return_value="/test/repo"), \
             patch("src.tools.memory.validate.resolve_repository", return_value="test-repo"):

            result = json.loads(validate_insight(
                insight_id="insight:abc123",
                validation_result="still_valid",
            ))

            assert result["status"] == "validated"

            call_kwargs = mock_collection.upsert.call_args[1]
            meta = call_kwargs["metadatas"][0]
            assert "created_at" in meta

    def test_validate_insight_handles_exception(self):
        """validate_insight returns error on exception."""
        from src.tools.memory.validate import validate_insight

        with patch("src.tools.memory.validate.get_collection", side_effect=Exception("DB error")), \
             patch("src.tools.memory.validate.resolve_repository", return_value="test-repo"):

            result = json.loads(validate_insight(
                insight_id="insight:abc123",
                validation_result="still_valid",
            ))

            assert result["status"] == "error"
            assert "DB error" in result["error"]

    def test_validate_insight_deprecate_only_when_no_longer_valid(self):
        """validate_insight only deprecates when validation_result is no_longer_valid."""
        from src.tools.memory.validate import validate_insight

        mock_collection = MagicMock()
        mock_collection.get.return_value = {
            "ids": ["insight:abc123"],
            "documents": ["Test insight"],
            "metadatas": [{"type": "insight", "files": '[]'}],
        }
        mock_searcher = MagicMock()

        with patch("src.tools.memory.validate.get_collection", return_value=mock_collection), \
             patch("src.tools.memory.validate.get_searcher", return_value=mock_searcher), \
             patch("src.tools.memory.validate.get_repo_path", return_value="/test/repo"), \
             patch("src.tools.memory.validate.resolve_repository", return_value="test-repo"):

            # Try to deprecate a still_valid insight (should be ignored)
            result = json.loads(validate_insight(
                insight_id="insight:abc123",
                validation_result="still_valid",
                deprecate=True,  # This should be ignored
            ))

            assert result["status"] == "validated"
            assert "deprecated" not in result

            call_kwargs = mock_collection.upsert.call_args[1]
            meta = call_kwargs["metadatas"][0]
            assert meta.get("status") != "deprecated"
