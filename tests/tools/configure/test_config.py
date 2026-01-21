"""
Tests for configure_cortex tool (src/tools/configure/).
"""

import json
import pytest
from unittest.mock import MagicMock, patch


class TestConfigureCortex:
    """Tests for the configure_cortex function."""

    def test_configure_min_score(self):
        """Test setting min_score configuration."""
        from src.tools.configure.config import configure_cortex

        with patch("src.tools.configure.config.CONFIG", {"min_score": 0.5}):
            result = json.loads(configure_cortex(min_score=0.7))

            assert result["status"] == "configured"
            assert "min_score=0.7" in result["changes"]

    def test_configure_min_score_clamped(self):
        """Test that min_score is clamped to [0.0, 1.0]."""
        from src.tools.configure.config import configure_cortex

        with patch("src.tools.configure.config.CONFIG", {"min_score": 0.5}) as mock_config:
            # Test clamping high values
            configure_cortex(min_score=1.5)
            assert mock_config["min_score"] == 1.0

            # Test clamping low values
            configure_cortex(min_score=-0.5)
            assert mock_config["min_score"] == 0.0

    def test_configure_verbose(self):
        """Test setting verbose configuration."""
        from src.tools.configure.config import configure_cortex

        with patch("src.tools.configure.config.CONFIG", {"verbose": False}):
            result = json.loads(configure_cortex(verbose=True))

            assert result["status"] == "configured"
            assert "verbose=True" in result["changes"]

    def test_configure_top_k_retrieve(self):
        """Test setting top_k_retrieve configuration."""
        from src.tools.configure.config import configure_cortex

        with patch("src.tools.configure.config.CONFIG", {"top_k_retrieve": 50}):
            result = json.loads(configure_cortex(top_k_retrieve=100))

            assert result["status"] == "configured"
            assert "top_k_retrieve=100" in result["changes"]

    def test_configure_top_k_retrieve_clamped(self):
        """Test that top_k_retrieve is clamped to [10, 200]."""
        from src.tools.configure.config import configure_cortex

        with patch("src.tools.configure.config.CONFIG", {"top_k_retrieve": 50}) as mock_config:
            # Test clamping high values
            configure_cortex(top_k_retrieve=500)
            assert mock_config["top_k_retrieve"] == 200

            # Test clamping low values
            configure_cortex(top_k_retrieve=5)
            assert mock_config["top_k_retrieve"] == 10

    def test_configure_top_k_rerank(self):
        """Test setting top_k_rerank configuration."""
        from src.tools.configure.config import configure_cortex

        with patch("src.tools.configure.config.CONFIG", {"top_k_rerank": 10}):
            result = json.loads(configure_cortex(top_k_rerank=20))

            assert result["status"] == "configured"
            assert "top_k_rerank=20" in result["changes"]

    def test_configure_top_k_rerank_clamped(self):
        """Test that top_k_rerank is clamped to [1, 50]."""
        from src.tools.configure.config import configure_cortex

        with patch("src.tools.configure.config.CONFIG", {"top_k_rerank": 10}) as mock_config:
            # Test clamping high values
            configure_cortex(top_k_rerank=100)
            assert mock_config["top_k_rerank"] == 50

            # Test clamping low values
            configure_cortex(top_k_rerank=0)
            assert mock_config["top_k_rerank"] == 1

    def test_configure_valid_llm_provider(self):
        """Test setting a valid LLM provider."""
        from src.tools.configure.config import configure_cortex

        with patch("src.tools.configure.config.CONFIG", {"llm_provider": "anthropic"}):
            for provider in ["anthropic", "claude-cli", "ollama", "openrouter", "none"]:
                result = json.loads(configure_cortex(llm_provider=provider))
                assert result["status"] == "configured"
                assert f"llm_provider={provider}" in result["changes"]

    def test_configure_invalid_llm_provider(self):
        """Test that invalid LLM provider is rejected."""
        from src.tools.configure.config import configure_cortex

        with patch("src.tools.configure.config.CONFIG", {"llm_provider": "anthropic"}) as mock_config:
            result = json.loads(configure_cortex(llm_provider="invalid_provider"))

            # Should not change the provider
            assert mock_config["llm_provider"] == "anthropic"
            # Should not include llm_provider in changes
            assert "llm_provider=" not in str(result["changes"])

    def test_configure_recency_boost(self):
        """Test setting recency_boost configuration."""
        from src.tools.configure.config import configure_cortex

        with patch("src.tools.configure.config.CONFIG", {"recency_boost": False}):
            result = json.loads(configure_cortex(recency_boost=True))

            assert result["status"] == "configured"
            assert "recency_boost=True" in result["changes"]

    def test_configure_recency_half_life_days(self):
        """Test setting recency_half_life_days configuration."""
        from src.tools.configure.config import configure_cortex

        with patch("src.tools.configure.config.CONFIG", {"recency_half_life_days": 14.0}):
            result = json.loads(configure_cortex(recency_half_life_days=30.0))

            assert result["status"] == "configured"
            assert "recency_half_life_days=30.0" in result["changes"]

    def test_configure_recency_half_life_days_clamped(self):
        """Test that recency_half_life_days is clamped to [1.0, 365.0]."""
        from src.tools.configure.config import configure_cortex

        with patch("src.tools.configure.config.CONFIG", {"recency_half_life_days": 14.0}) as mock_config:
            # Test clamping high values
            configure_cortex(recency_half_life_days=500.0)
            assert mock_config["recency_half_life_days"] == 365.0

            # Test clamping low values
            configure_cortex(recency_half_life_days=0.5)
            assert mock_config["recency_half_life_days"] == 1.0

    def test_configure_enabled(self):
        """Test enabling/disabling Cortex."""
        from src.tools.configure.config import configure_cortex

        with patch("src.tools.configure.config.CONFIG", {"enabled": True}):
            result = json.loads(configure_cortex(enabled=False))

            assert result["status"] == "configured"
            assert "enabled=False" in result["changes"]

    def test_configure_no_changes(self):
        """Test configure with no parameters makes no changes."""
        from src.tools.configure.config import configure_cortex

        with patch("src.tools.configure.config.CONFIG", {}):
            result = json.loads(configure_cortex())

            assert result["status"] == "configured"
            assert result["changes"] == []

    def test_configure_multiple_changes(self):
        """Test configuring multiple settings at once."""
        from src.tools.configure.config import configure_cortex

        with patch("src.tools.configure.config.CONFIG", {
            "min_score": 0.5,
            "verbose": False,
            "top_k_retrieve": 50,
        }):
            result = json.loads(configure_cortex(
                min_score=0.8,
                verbose=True,
                top_k_retrieve=100,
            ))

            assert result["status"] == "configured"
            assert len(result["changes"]) == 3
            assert "min_score=0.8" in result["changes"]
            assert "verbose=True" in result["changes"]
            assert "top_k_retrieve=100" in result["changes"]


class TestSetTechStack:
    """Tests for tech stack configuration."""

    def test_set_tech_stack(self, temp_chroma_client):
        """Test setting tech stack for a repository."""
        from src.tools.configure.config import configure_cortex

        mock_collection = MagicMock()
        mock_searcher = MagicMock()

        with patch("src.tools.configure.config.CONFIG", {}), \
             patch("src.tools.configure.config.get_collection", return_value=mock_collection), \
             patch("src.tools.configure.config.get_repo_path", return_value="/test/repo"), \
             patch("src.tools.configure.config.get_current_branch", return_value="main"), \
             patch("src.tools.configure.config.get_searcher", return_value=mock_searcher):

            result = json.loads(configure_cortex(
                repository="my-app",
                tech_stack="Python FastAPI, PostgreSQL, React frontend",
            ))

            assert result["status"] == "configured"
            assert "tech_stack for my-app" in result["changes"]

            # Verify upsert was called with correct arguments
            mock_collection.upsert.assert_called_once()
            call_kwargs = mock_collection.upsert.call_args
            assert call_kwargs[1]["ids"] == ["my-app:tech_stack"]
            assert "Python FastAPI" in call_kwargs[1]["documents"][0]

    def test_set_tech_stack_scrubs_secrets(self, temp_chroma_client):
        """Test that tech stack content is scrubbed for secrets."""
        from src.tools.configure.config import configure_cortex

        mock_collection = MagicMock()
        mock_searcher = MagicMock()

        with patch("src.tools.configure.config.CONFIG", {}), \
             patch("src.tools.configure.config.get_collection", return_value=mock_collection), \
             patch("src.tools.configure.config.get_repo_path", return_value="/test/repo"), \
             patch("src.tools.configure.config.get_current_branch", return_value="main"), \
             patch("src.tools.configure.config.get_searcher", return_value=mock_searcher):

            # Use a secret that matches the pattern (sk-ant- followed by 20+ alphanumeric chars)
            configure_cortex(
                repository="my-app",
                tech_stack="Python app using API key sk-ant-abcdefghijklmnopqrstuvwxyz12345",
            )

            # Verify secret was scrubbed
            call_kwargs = mock_collection.upsert.call_args
            saved_doc = call_kwargs[1]["documents"][0]
            assert "sk-ant-" not in saved_doc
            assert "[ANTHROPIC_KEY_REDACTED]" in saved_doc

    def test_set_tech_stack_requires_repository(self):
        """Test that tech_stack without repository makes no changes."""
        from src.tools.configure.config import configure_cortex

        with patch("src.tools.configure.config.CONFIG", {}):
            result = json.loads(configure_cortex(tech_stack="Python FastAPI"))

            assert result["status"] == "configured"
            assert "tech_stack" not in str(result["changes"])


class TestGetStatus:
    """Tests for get_status functionality."""

    def test_get_status_returns_runtime_config(self):
        """Test that get_status returns runtime configuration."""
        from src.tools.configure.config import configure_cortex

        test_config = {
            "min_score": 0.5,
            "verbose": True,
            "top_k_retrieve": 50,
        }

        mock_yaml_config = {"autocapture": {}, "llm": {}}

        # Create a mock hook_status object
        mock_hook_status = MagicMock()
        mock_hook_status.claude_code_installed = True
        mock_hook_status.hook_script_exists = True

        with patch("src.tools.configure.config.CONFIG", test_config), \
             patch("src.configs.yaml_config.load_yaml_config", return_value=mock_yaml_config), \
             patch("src.integrations.hooks.get_hook_status", return_value=mock_hook_status), \
             patch("src.external.llm.get_available_providers", return_value=["claude-cli"]):

            result = json.loads(configure_cortex(get_status=True))

            assert result["status"] == "ok"
            assert "runtime_config" in result
            assert result["runtime_config"]["min_score"] == 0.5

    def test_get_status_includes_autocapture_info(self):
        """Test that get_status includes autocapture configuration."""
        from src.tools.configure.config import configure_cortex

        mock_yaml_config = {
            "autocapture": {
                "enabled": True,
                "auto_commit_async": True,
                "significance": {"min_tokens": 1000},
            },
            "llm": {"primary_provider": "claude-cli"},
        }

        # Create a mock hook_status object
        mock_hook_status = MagicMock()
        mock_hook_status.claude_code_installed = True
        mock_hook_status.hook_script_exists = True

        with patch("src.tools.configure.config.CONFIG", {}), \
             patch("src.configs.yaml_config.load_yaml_config", return_value=mock_yaml_config), \
             patch("src.integrations.hooks.get_hook_status", return_value=mock_hook_status), \
             patch("src.external.llm.get_available_providers", return_value=["claude-cli"]):

            result = json.loads(configure_cortex(get_status=True))

            assert "autocapture" in result
            assert result["autocapture"]["config"]["enabled"] is True


class TestConfigureAutocapture:
    """Tests for autocapture configuration."""

    def test_configure_autocapture_enabled(self):
        """Test enabling/disabling autocapture."""
        from src.tools.configure.config import configure_cortex

        mock_yaml_config = {"autocapture": {}, "llm": {}}

        with patch("src.tools.configure.config.CONFIG", {}), \
             patch("src.configs.yaml_config.load_yaml_config", return_value=mock_yaml_config), \
             patch("src.configs.yaml_config.save_yaml_config") as mock_save, \
             patch("src.configs.yaml_config.create_default_config"):

            result = json.loads(configure_cortex(autocapture_enabled=True))

            assert "autocapture_enabled=True" in result["changes"]
            mock_save.assert_called_once()

    def test_configure_autocapture_min_tokens(self):
        """Test setting autocapture min_tokens threshold."""
        from src.tools.configure.config import configure_cortex

        mock_yaml_config = {"autocapture": {"significance": {}}, "llm": {}}

        with patch("src.tools.configure.config.CONFIG", {}), \
             patch("src.configs.yaml_config.load_yaml_config", return_value=mock_yaml_config), \
             patch("src.configs.yaml_config.save_yaml_config") as mock_save, \
             patch("src.configs.yaml_config.create_default_config"):

            result = json.loads(configure_cortex(autocapture_min_tokens=5000))

            assert "autocapture_min_tokens=5000" in result["changes"]
            mock_save.assert_called_once()
            saved_config = mock_save.call_args[0][0]
            assert saved_config["autocapture"]["significance"]["min_tokens"] == 5000

    def test_configure_autocapture_llm_provider(self):
        """Test setting autocapture LLM provider."""
        from src.tools.configure.config import configure_cortex

        mock_yaml_config = {"autocapture": {}, "llm": {}}

        with patch("src.tools.configure.config.CONFIG", {}), \
             patch("src.configs.yaml_config.load_yaml_config", return_value=mock_yaml_config), \
             patch("src.configs.yaml_config.save_yaml_config") as mock_save, \
             patch("src.configs.yaml_config.create_default_config"):

            result = json.loads(configure_cortex(autocapture_llm_provider="ollama"))

            assert "autocapture_llm_provider=ollama" in result["changes"]
            saved_config = mock_save.call_args[0][0]
            assert saved_config["llm"]["primary_provider"] == "ollama"

    def test_configure_autocapture_invalid_provider(self):
        """Test that invalid autocapture provider is rejected."""
        from src.tools.configure.config import configure_cortex

        mock_yaml_config = {"autocapture": {}, "llm": {"primary_provider": "claude-cli"}}

        with patch("src.tools.configure.config.CONFIG", {}), \
             patch("src.configs.yaml_config.load_yaml_config", return_value=mock_yaml_config), \
             patch("src.configs.yaml_config.save_yaml_config") as mock_save, \
             patch("src.configs.yaml_config.create_default_config"):

            result = json.loads(configure_cortex(autocapture_llm_provider="invalid"))

            assert "autocapture_llm_provider=" not in str(result["changes"])

    def test_configure_autocapture_async_mode(self):
        """Test setting autocapture async mode."""
        from src.tools.configure.config import configure_cortex

        mock_yaml_config = {"autocapture": {}, "llm": {}}

        with patch("src.tools.configure.config.CONFIG", {}), \
             patch("src.configs.yaml_config.load_yaml_config", return_value=mock_yaml_config), \
             patch("src.configs.yaml_config.save_yaml_config") as mock_save, \
             patch("src.configs.yaml_config.create_default_config"):

            result = json.loads(configure_cortex(autocapture_async=False))

            assert "autocapture_async=False" in result["changes"]
            saved_config = mock_save.call_args[0][0]
            assert saved_config["autocapture"]["auto_commit_async"] is False

    def test_configure_autocapture_multiple_thresholds(self):
        """Test setting multiple autocapture thresholds at once."""
        from src.tools.configure.config import configure_cortex

        mock_yaml_config = {"autocapture": {"significance": {}}, "llm": {}}

        with patch("src.tools.configure.config.CONFIG", {}), \
             patch("src.configs.yaml_config.load_yaml_config", return_value=mock_yaml_config), \
             patch("src.configs.yaml_config.save_yaml_config") as mock_save, \
             patch("src.configs.yaml_config.create_default_config"):

            result = json.loads(configure_cortex(
                autocapture_min_tokens=5000,
                autocapture_min_tool_calls=10,
                autocapture_min_file_edits=3,
            ))

            assert "autocapture_min_tokens=5000" in result["changes"]
            assert "autocapture_min_tool_calls=10" in result["changes"]
            assert "autocapture_min_file_edits=3" in result["changes"]

            saved_config = mock_save.call_args[0][0]
            assert saved_config["autocapture"]["significance"]["min_tokens"] == 5000
            assert saved_config["autocapture"]["significance"]["min_tool_calls"] == 10
            assert saved_config["autocapture"]["significance"]["min_file_edits"] == 3
