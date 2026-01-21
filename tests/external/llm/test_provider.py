"""
Tests for LLM provider module (src/external/llm/).
"""

from unittest.mock import MagicMock, patch

import pytest


class TestProviderRegistry:
    """Tests for the provider registry pattern."""

    def test_registry_contains_expected_providers(self):
        """PROVIDER_REGISTRY has all expected providers."""
        from src.external.llm import PROVIDER_REGISTRY

        assert "anthropic" in PROVIDER_REGISTRY
        assert "claude-cli" in PROVIDER_REGISTRY
        assert "ollama" in PROVIDER_REGISTRY
        assert "openrouter" in PROVIDER_REGISTRY
        assert len(PROVIDER_REGISTRY) == 4

    def test_registry_entries_have_correct_structure(self):
        """Each registry entry is (class, config_key) tuple."""
        from src.external.llm import (
            PROVIDER_REGISTRY,
            AnthropicProvider,
            ClaudeCLIProvider,
            OllamaProvider,
            OpenRouterProvider,
        )

        assert PROVIDER_REGISTRY["anthropic"] == (AnthropicProvider, "anthropic")
        assert PROVIDER_REGISTRY["claude-cli"] == (ClaudeCLIProvider, "claude_cli")
        assert PROVIDER_REGISTRY["ollama"] == (OllamaProvider, "ollama")
        assert PROVIDER_REGISTRY["openrouter"] == (OpenRouterProvider, "openrouter")

    def test_create_provider_returns_correct_type(self):
        """_create_provider returns instance of correct class."""
        from src.external.llm import (
            AnthropicProvider,
            ClaudeCLIProvider,
            OllamaProvider,
            OpenRouterProvider,
        )
        from src.external.llm import _create_provider

        assert isinstance(_create_provider("anthropic", {}), AnthropicProvider)
        assert isinstance(_create_provider("claude-cli", {}), ClaudeCLIProvider)
        assert isinstance(_create_provider("ollama", {}), OllamaProvider)
        assert isinstance(_create_provider("openrouter", {}), OpenRouterProvider)

    def test_create_provider_passes_config(self):
        """_create_provider passes config section to provider."""
        from src.external.llm import _create_provider

        config = {"ollama": {"model": "llama3", "base_url": "http://localhost:11434"}}
        provider = _create_provider("ollama", config)

        assert provider.default_model == "llama3"
        assert provider._base_url == "http://localhost:11434"

    def test_create_provider_unknown_raises_valueerror(self):
        """_create_provider raises ValueError for unknown provider."""
        from src.external.llm import _create_provider

        with pytest.raises(ValueError) as exc_info:
            _create_provider("unknown-provider", {})

        error_msg = str(exc_info.value)
        assert "Unknown provider: unknown-provider" in error_msg
        assert "anthropic" in error_msg
        assert "claude-cli" in error_msg
        assert "ollama" in error_msg
        assert "openrouter" in error_msg

    def test_get_available_providers_uses_registry(self):
        """get_available_providers iterates over PROVIDER_REGISTRY."""
        from src.external.llm import PROVIDER_REGISTRY, get_available_providers

        with patch("src.external.llm._create_provider") as mock_create:
            mock_provider = MagicMock()
            mock_provider.is_available.return_value = True
            mock_create.return_value = mock_provider

            result = get_available_providers()

            # Should have called _create_provider for each registry entry
            assert mock_create.call_count == len(PROVIDER_REGISTRY)
            # All providers returned as available
            assert len(result) == len(PROVIDER_REGISTRY)


