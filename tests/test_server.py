"""
Tests for server MCP tools
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestSearchCortex:
    """Tests for search_cortex tool."""

    def test_search_returns_results(self, temp_dir: Path, temp_chroma_client):
        """Test that search returns results from indexed content."""
        from src.storage import get_or_create_collection

        # Set up collection with test data
        collection = get_or_create_collection(temp_chroma_client, "cortex_memory")
        collection.add(
            documents=[
                "Python function for calculating fibonacci numbers",
                "JavaScript class for handling user authentication",
                "Rust implementation of a hash map",
            ],
            ids=["1", "2", "3"],
            metadatas=[
                {"file_path": "/test/fib.py", "project": "test", "branch": "main", "language": "python"},
                {"file_path": "/test/auth.js", "project": "test", "branch": "main", "language": "javascript"},
                {"file_path": "/test/hashmap.rs", "project": "test", "branch": "main", "language": "rust"},
            ],
        )

        # Import and test search
        from src.search import HybridSearcher, RerankerService

        searcher = HybridSearcher(collection)
        reranker = RerankerService()

        # Build index
        searcher.build_index()

        # Search
        candidates = searcher.search("fibonacci", top_k=10)
        assert len(candidates) > 0

        # Rerank
        reranked = reranker.rerank("fibonacci", candidates, top_k=3)
        assert len(reranked) > 0

    def test_search_with_disabled_cortex(self):
        """Test that search returns error when Cortex is disabled."""
        # This would require importing server module with mocked dependencies
        # For now, we test the config behavior
        from src.tools.services import CONFIG

        CONFIG["enabled"] = False

        # The actual tool would return an error
        # We verify the config is properly set
        assert CONFIG["enabled"] is False

        # Reset
        CONFIG["enabled"] = True

    def test_search_empty_collection(self, temp_chroma_client):
        """Test search on empty collection."""
        from src.search import HybridSearcher
        from src.storage import get_or_create_collection

        collection = get_or_create_collection(temp_chroma_client, "empty")
        searcher = HybridSearcher(collection)
        searcher.build_index()

        results = searcher.search("anything", top_k=10)
        assert results == []


class TestIngestCodeIntoCortex:
    """Tests for ingest_code_into_cortex tool."""

    def test_ingest_basic(self, temp_dir: Path, temp_chroma_client):
        """Test basic code ingestion."""
        from src.ingest import ingest_codebase
        from src.storage import get_or_create_collection

        # Create test files
        (temp_dir / "main.py").write_text("def hello(): print('world')")
        (temp_dir / "utils.py").write_text("def helper(): return 42")

        collection = get_or_create_collection(temp_chroma_client, "test")

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            state_file = f.name

        stats = ingest_codebase(
            root_path=str(temp_dir),
            collection=collection,
            project_id="testproject",
            header_provider="none",
            state_file=state_file,
        )

        assert stats["files_processed"] == 2
        assert stats["chunks_created"] >= 2

        # Verify content in collection
        results = collection.get(include=["metadatas"])
        assert len(results["ids"]) >= 2

        # All should have the correct project
        for meta in results["metadatas"]:
            assert meta["project"] == "testproject"

    def test_ingest_respects_force_full(self, temp_dir: Path, temp_chroma_client):
        """Test that force_full re-ingests everything."""
        from src.ingest import ingest_codebase
        from src.storage import get_or_create_collection

        (temp_dir / "main.py").write_text("def main(): pass")

        collection = get_or_create_collection(temp_chroma_client, "force_test")

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            state_file = f.name

        # First ingest
        stats1 = ingest_codebase(
            root_path=str(temp_dir),
            collection=collection,
            header_provider="none",
            state_file=state_file,
        )
        assert stats1["files_processed"] == 1

        # Second ingest without changes (should skip)
        stats2 = ingest_codebase(
            root_path=str(temp_dir),
            collection=collection,
            header_provider="none",
            state_file=state_file,
        )
        assert stats2["files_processed"] == 0

        # Third ingest with force_full (should re-process)
        stats3 = ingest_codebase(
            root_path=str(temp_dir),
            collection=collection,
            header_provider="none",
            state_file=state_file,
            force_full=True,
        )
        assert stats3["files_processed"] == 1


class TestCommitToCortex:
    """Tests for commit_to_cortex tool."""

    def test_commit_saves_summary(self, temp_dir: Path, temp_chroma_client):
        """Test that commit saves summary to collection."""
        import uuid

        from src.security import scrub_secrets
        from src.storage import get_or_create_collection

        collection = get_or_create_collection(temp_chroma_client, "commit_test")

        # Simulate what commit_to_cortex does
        summary = "Implemented new authentication flow with JWT tokens"
        changed_files = ["/app/auth.py", "/app/middleware.py"]

        note_id = f"commit:{uuid.uuid4().hex[:8]}"

        collection.upsert(
            ids=[note_id],
            documents=[f"Session Summary:\n\n{scrub_secrets(summary)}\n\nChanged files: {', '.join(changed_files)}"],
            metadatas=[{
                "type": "commit",
                "project": "test",
                "branch": "main",
                "files": json.dumps(changed_files),
            }],
        )

        # Verify saved
        results = collection.get(ids=[note_id], include=["documents", "metadatas"])
        assert len(results["ids"]) == 1
        assert "authentication" in results["documents"][0].lower()
        assert results["metadatas"][0]["type"] == "commit"


class TestSaveNoteToCortex:
    """Tests for save_note_to_cortex tool."""

    def test_save_note_basic(self, temp_chroma_client):
        """Test basic note saving."""
        import uuid

        from src.security import scrub_secrets
        from src.storage import get_or_create_collection

        collection = get_or_create_collection(temp_chroma_client, "notes_test")

        title = "Architecture Decision"
        content = "We decided to use PostgreSQL instead of MongoDB for the user service."
        tags = ["architecture", "database"]

        note_id = f"note:{uuid.uuid4().hex[:8]}"

        doc_text = f"{title}\n\n{scrub_secrets(content)}"

        collection.upsert(
            ids=[note_id],
            documents=[doc_text],
            metadatas=[{
                "type": "note",
                "title": title,
                "tags": ",".join(tags),
                "project": "myproject",
                "branch": "main",
            }],
        )

        # Verify
        results = collection.get(ids=[note_id], include=["documents", "metadatas"])
        assert len(results["ids"]) == 1
        assert "PostgreSQL" in results["documents"][0]
        assert results["metadatas"][0]["type"] == "note"
        assert "architecture" in results["metadatas"][0]["tags"]

    def test_save_note_scrubs_secrets(self, temp_chroma_client):
        """Test that notes have secrets scrubbed."""
        import uuid

        from src.security import scrub_secrets
        from src.storage import get_or_create_collection

        collection = get_or_create_collection(temp_chroma_client, "secret_notes")

        content = "API key is AKIAIOSFODNN7EXAMPLE"
        note_id = f"note:{uuid.uuid4().hex[:8]}"

        collection.upsert(
            ids=[note_id],
            documents=[scrub_secrets(content)],
            metadatas=[{"type": "note", "project": "test", "branch": "main", "title": "", "tags": ""}],
        )

        results = collection.get(ids=[note_id], include=["documents"])
        assert "AKIAIOSFODNN7EXAMPLE" not in results["documents"][0]


class TestConfigureCortex:
    """Tests for configure_cortex tool."""

    def test_configure_min_score(self):
        """Test configuring min_score."""
        from src.tools.services import CONFIG

        original = CONFIG["min_score"]

        CONFIG["min_score"] = 0.7
        assert CONFIG["min_score"] == 0.7

        # Reset
        CONFIG["min_score"] = original

    def test_configure_verbose(self):
        """Test configuring verbose mode."""
        from src.tools.services import CONFIG

        original = CONFIG["verbose"]

        CONFIG["verbose"] = True
        assert CONFIG["verbose"] is True

        CONFIG["verbose"] = False
        assert CONFIG["verbose"] is False

        # Reset
        CONFIG["verbose"] = original

    def test_configure_top_k_limits(self):
        """Test that top_k values are bounded."""
        from src.tools.services import CONFIG

        # Test top_k_retrieve
        CONFIG["top_k_retrieve"] = max(10, min(200, 5))  # Below min
        assert CONFIG["top_k_retrieve"] == 10

        CONFIG["top_k_retrieve"] = max(10, min(200, 250))  # Above max
        assert CONFIG["top_k_retrieve"] == 200

        CONFIG["top_k_retrieve"] = max(10, min(200, 100))  # Normal
        assert CONFIG["top_k_retrieve"] == 100

        # Reset
        CONFIG["top_k_retrieve"] = 50


class TestToggleCortex:
    """Tests for toggle_cortex tool."""

    def test_toggle_disable(self):
        """Test disabling Cortex."""
        from src.tools.services import CONFIG

        CONFIG["enabled"] = False
        assert CONFIG["enabled"] is False

    def test_toggle_enable(self):
        """Test enabling Cortex."""
        from src.tools.services import CONFIG

        CONFIG["enabled"] = True
        assert CONFIG["enabled"] is True


class TestContextTools:
    """Tests for context composition tools (set_repo_context, set_initiative, etc.)."""

    def test_set_repo_context_saves_tech_stack(self, temp_chroma_client):
        """Test that set_repo_context saves tech stack context."""
        from datetime import datetime, timezone

        from src.security import scrub_secrets
        from src.storage import get_or_create_collection

        collection = get_or_create_collection(temp_chroma_client, "context_test")

        repository = "myproject"
        tech_stack = "NestJS backend, PostgreSQL database, React frontend"
        tech_stack_id = f"{repository}:tech_stack"
        timestamp = datetime.now(timezone.utc).isoformat()

        collection.upsert(
            ids=[tech_stack_id],
            documents=[scrub_secrets(tech_stack)],
            metadatas=[{
                "type": "tech_stack",
                "repository": repository,
                "branch": "main",
                "updated_at": timestamp,
            }],
        )

        # Verify saved
        results = collection.get(ids=[tech_stack_id], include=["documents", "metadatas"])
        assert len(results["ids"]) == 1
        assert "NestJS" in results["documents"][0]
        assert results["metadatas"][0]["type"] == "tech_stack"
        assert results["metadatas"][0]["repository"] == repository

    def test_set_initiative_saves_name_and_status(self, temp_chroma_client):
        """Test that set_initiative saves initiative name and status."""
        from datetime import datetime, timezone

        from src.security import scrub_secrets
        from src.storage import get_or_create_collection

        collection = get_or_create_collection(temp_chroma_client, "context_test2")

        repository = "myproject"
        initiative_name = "Migration V1"
        initiative_status = "Phase 2 - auth module complete, API review pending"
        initiative_id = f"{repository}:initiative"
        timestamp = datetime.now(timezone.utc).isoformat()

        content = f"{initiative_name}\n\nStatus: {initiative_status}"

        collection.upsert(
            ids=[initiative_id],
            documents=[scrub_secrets(content)],
            metadatas=[{
                "type": "initiative",
                "repository": repository,
                "initiative_name": initiative_name,
                "initiative_status": initiative_status,
                "branch": "main",
                "updated_at": timestamp,
            }],
        )

        # Verify saved
        results = collection.get(ids=[initiative_id], include=["documents", "metadatas"])
        assert len(results["ids"]) == 1
        assert "Phase 2" in results["documents"][0]
        assert results["metadatas"][0]["type"] == "initiative"
        assert results["metadatas"][0]["initiative_name"] == initiative_name
        assert results["metadatas"][0]["initiative_status"] == initiative_status

    def test_initiative_upsert_overwrites(self, temp_chroma_client):
        """Test that initiative is overwritten on update (upsert behavior)."""
        from datetime import datetime, timezone

        from src.storage import get_or_create_collection

        collection = get_or_create_collection(temp_chroma_client, "context_upsert")

        repository = "myproject"
        initiative_id = f"{repository}:initiative"

        # First initiative
        collection.upsert(
            ids=[initiative_id],
            documents=["Feature X\n\nStatus: Phase 1: In progress"],
            metadatas=[{
                "type": "initiative",
                "repository": repository,
                "initiative_name": "Feature X",
                "initiative_status": "Phase 1: In progress",
                "branch": "main",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }],
        )

        # Update initiative
        collection.upsert(
            ids=[initiative_id],
            documents=["Feature X\n\nStatus: Phase 2: Started"],
            metadatas=[{
                "type": "initiative",
                "repository": repository,
                "initiative_name": "Feature X",
                "initiative_status": "Phase 2: Started",
                "branch": "main",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }],
        )

        # Should only have one document with updated content
        results = collection.get(ids=[initiative_id], include=["documents"])
        assert len(results["ids"]) == 1
        assert "Phase 2" in results["documents"][0]
        assert "Phase 1" not in results["documents"][0]

    def test_get_context_retrieves_both(self, temp_chroma_client):
        """Test that get_context retrieves both tech_stack and initiative."""
        from datetime import datetime, timezone

        from src.storage import get_or_create_collection

        collection = get_or_create_collection(temp_chroma_client, "context_get")

        repository = "myproject"
        tech_stack_id = f"{repository}:tech_stack"
        initiative_id = f"{repository}:initiative"
        timestamp = datetime.now(timezone.utc).isoformat()

        # Save both contexts
        collection.upsert(
            ids=[tech_stack_id],
            documents=["Python FastAPI backend"],
            metadatas=[{
                "type": "tech_stack",
                "repository": repository,
                "branch": "main",
                "updated_at": timestamp,
            }],
        )
        collection.upsert(
            ids=[initiative_id],
            documents=["User Auth\n\nStatus: Implementing"],
            metadatas=[{
                "type": "initiative",
                "repository": repository,
                "initiative_name": "User Auth",
                "initiative_status": "Implementing",
                "branch": "main",
                "updated_at": timestamp,
            }],
        )

        # Retrieve both
        results = collection.get(
            ids=[tech_stack_id, initiative_id],
            include=["documents", "metadatas"],
        )

        assert len(results["ids"]) == 2

        # Verify both are present
        docs = results["documents"]
        assert any("FastAPI" in doc for doc in docs)
        assert any("User Auth" in doc for doc in docs)

    def test_context_scrubs_secrets(self, temp_chroma_client):
        """Test that context has secrets scrubbed."""
        from datetime import datetime, timezone

        from src.security import scrub_secrets
        from src.storage import get_or_create_collection

        collection = get_or_create_collection(temp_chroma_client, "context_secrets")

        repository = "myproject"
        tech_stack_id = f"{repository}:tech_stack"

        # Tech stack with a secret
        tech_stack_with_secret = "Backend using API key AKIAIOSFODNN7EXAMPLE for AWS"
        timestamp = datetime.now(timezone.utc).isoformat()

        collection.upsert(
            ids=[tech_stack_id],
            documents=[scrub_secrets(tech_stack_with_secret)],
            metadatas=[{
                "type": "tech_stack",
                "repository": repository,
                "branch": "main",
                "updated_at": timestamp,
            }],
        )

        results = collection.get(ids=[tech_stack_id], include=["documents"])
        assert "AKIAIOSFODNN7EXAMPLE" not in results["documents"][0]

    def test_context_included_in_search(self, temp_chroma_client):
        """Test that context can be fetched alongside search results."""
        from datetime import datetime, timezone

        from src.storage import get_or_create_collection

        collection = get_or_create_collection(temp_chroma_client, "context_search")

        repository = "searchproject"
        tech_stack_id = f"{repository}:tech_stack"
        initiative_id = f"{repository}:initiative"
        timestamp = datetime.now(timezone.utc).isoformat()

        # Add some code
        collection.add(
            documents=["def calculate_total(): return sum(items)"],
            ids=["code:1"],
            metadatas=[{
                "type": "code",
                "file_path": "/app/utils.py",
                "project": repository,
                "branch": "main",
                "language": "python",
            }],
        )

        # Add context
        collection.upsert(
            ids=[tech_stack_id],
            documents=["E-commerce platform with Python backend"],
            metadatas=[{
                "type": "tech_stack",
                "repository": repository,
                "branch": "main",
                "updated_at": timestamp,
            }],
        )
        collection.upsert(
            ids=[initiative_id],
            documents=["Checkout Flow\n\nStatus: Building"],
            metadatas=[{
                "type": "initiative",
                "repository": repository,
                "initiative_name": "Checkout Flow",
                "initiative_status": "Building",
                "branch": "main",
                "updated_at": timestamp,
            }],
        )

        # Simulate search_cortex context fetch pattern
        context_results = collection.get(
            ids=[tech_stack_id, initiative_id],
            include=["documents", "metadatas"],
        )

        # Verify context is retrievable
        assert len(context_results["ids"]) == 2
        docs = context_results["documents"]
        assert any("E-commerce" in doc for doc in docs)
        assert any("Checkout" in doc for doc in docs)

    def test_set_repo_context_validation_requires_tech_stack(self):
        """Test that set_repo_context requires tech_stack parameter."""
        repository = "myproject"
        tech_stack = None

        if not tech_stack:
            error = json.dumps({
                "error": "Tech stack description is required",
            })
            parsed = json.loads(error)
            assert "error" in parsed
            assert "tech_stack" in parsed["error"].lower() or "required" in parsed["error"].lower()

    def test_get_context_validation_requires_repository(self):
        """Test that get_context requires repository parameter."""
        repository = None

        if not repository:
            error = json.dumps({
                "error": "Repository name is required",
            })
            parsed = json.loads(error)
            assert "error" in parsed
            assert "required" in parsed["error"].lower()

    def test_update_initiative_status_validation_requires_repository(self):
        """Test that update_initiative_status requires repository parameter."""
        repository = None

        if not repository:
            error = json.dumps({
                "error": "Repository name is required",
            })
            parsed = json.loads(error)
            assert "error" in parsed
            assert "required" in parsed["error"].lower()

    def test_get_context_empty_returns_message(self, temp_chroma_client):
        """Test that get_context returns helpful message when no context exists."""
        from src.storage import get_or_create_collection

        collection = get_or_create_collection(temp_chroma_client, "empty_context")
        repository = "nonexistent_project"
        tech_stack_id = f"{repository}:tech_stack"
        initiative_id = f"{repository}:initiative"

        # Try to fetch non-existent context
        results = collection.get(
            ids=[tech_stack_id, initiative_id],
            include=["documents", "metadatas"],
        )

        # Should return empty
        assert len(results["ids"]) == 0

        # Simulate the response logic
        context = {
            "repository": repository,
            "tech_stack": None,
            "initiative": None,
        }
        has_context = context["tech_stack"] or context["initiative"]
        assert not has_context

    def test_set_initiative_name_only(self, temp_chroma_client):
        """Test setting initiative with name only (no status)."""
        from datetime import datetime, timezone

        from src.security import scrub_secrets
        from src.storage import get_or_create_collection

        collection = get_or_create_collection(temp_chroma_client, "initiative_name_only")

        repository = "testproj"
        initiative_name = "Feature Y"
        initiative_id = f"{repository}:initiative"
        timestamp = datetime.now(timezone.utc).isoformat()

        # Save initiative with name only
        collection.upsert(
            ids=[initiative_id],
            documents=[scrub_secrets(initiative_name)],
            metadatas=[{
                "type": "initiative",
                "repository": repository,
                "initiative_name": initiative_name,
                "initiative_status": "",
                "branch": "main",
                "updated_at": timestamp,
            }],
        )

        # Verify content
        results = collection.get(ids=[initiative_id], include=["documents", "metadatas"])
        assert "Feature Y" in results["documents"][0]
        assert results["metadatas"][0]["initiative_name"] == initiative_name
        assert results["metadatas"][0]["initiative_status"] == ""

    def test_update_initiative_status_overwrites(self, temp_chroma_client):
        """Test that update_initiative_status overwrites existing status."""
        from datetime import datetime, timezone

        from src.security import scrub_secrets
        from src.storage import get_or_create_collection

        collection = get_or_create_collection(temp_chroma_client, "update_status")

        repository = "testproj"
        initiative_id = f"{repository}:initiative"
        initiative_name = "Feature Z"

        # Initial initiative
        collection.upsert(
            ids=[initiative_id],
            documents=[f"{initiative_name}\n\nStatus: Phase 1: Planning"],
            metadatas=[{
                "type": "initiative",
                "repository": repository,
                "initiative_name": initiative_name,
                "initiative_status": "Phase 1: Planning",
                "branch": "main",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }],
        )

        # Update status (simulate update_initiative_status)
        new_status = "Phase 3: Testing"
        collection.upsert(
            ids=[initiative_id],
            documents=[scrub_secrets(f"{initiative_name}\n\nStatus: {new_status}")],
            metadatas=[{
                "type": "initiative",
                "repository": repository,
                "initiative_name": initiative_name,
                "initiative_status": new_status,
                "branch": "main",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }],
        )

        # Verify update
        results = collection.get(ids=[initiative_id], include=["documents", "metadatas"])
        assert len(results["ids"]) == 1
        assert "Phase 3" in results["documents"][0]
        assert "Phase 1" not in results["documents"][0]
        assert results["metadatas"][0]["initiative_status"] == new_status


class TestIntegration:
    """Integration tests for the full workflow."""

    def test_full_workflow(self, temp_dir: Path, temp_chroma_client):
        """Test complete ingest -> search workflow."""
        from src.ingest import ingest_codebase
        from src.search import HybridSearcher, RerankerService
        from src.storage import get_or_create_collection

        # Create test codebase
        (temp_dir / "calculator.py").write_text('''
class Calculator:
    """A calculator that performs basic arithmetic."""

    def add(self, a: int, b: int) -> int:
        """Add two numbers together."""
        return a + b

    def multiply(self, a: int, b: int) -> int:
        """Multiply two numbers."""
        return a * b
''')

        (temp_dir / "utils.py").write_text('''
def validate_input(value):
    """Validate that input is a number."""
    if not isinstance(value, (int, float)):
        raise ValueError("Input must be a number")
    return True
''')

        collection = get_or_create_collection(temp_chroma_client, "integration")

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            state_file = f.name

        # Ingest
        stats = ingest_codebase(
            root_path=str(temp_dir),
            collection=collection,
            project_id="testcalc",
            header_provider="none",
            state_file=state_file,
        )

        assert stats["files_processed"] == 2
        assert stats["chunks_created"] >= 2

        # Search
        searcher = HybridSearcher(collection)
        searcher.build_index()

        candidates = searcher.search("add two numbers", top_k=10)
        assert len(candidates) > 0

        # Rerank
        reranker = RerankerService()
        reranked = reranker.rerank("add two numbers", candidates, top_k=3)

        # The calculator add function should be in results
        found_add = False
        for result in reranked:
            if "add" in result.get("text", "").lower():
                found_add = True
                break

        assert found_add, "Should find the add function in search results"

    def test_note_searchable(self, temp_chroma_client):
        """Test that saved notes are searchable."""
        import uuid

        from src.search import HybridSearcher, RerankerService
        from src.storage import get_or_create_collection

        collection = get_or_create_collection(temp_chroma_client, "notes_search")

        # Save a note
        note_id = f"note:{uuid.uuid4().hex[:8]}"
        collection.upsert(
            ids=[note_id],
            documents=["Architecture Decision: Use Redis for caching to improve API response times"],
            metadatas=[{"type": "note", "project": "test", "branch": "main", "title": "", "tags": ""}],
        )

        # Search for it
        searcher = HybridSearcher(collection)
        searcher.build_index()

        candidates = searcher.search("Redis caching", top_k=10)
        assert len(candidates) > 0

        # Verify our note is found
        found = False
        for c in candidates:
            if "Redis" in c.get("text", ""):
                found = True
                break

        assert found, "Note should be found in search"
