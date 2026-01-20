"""
Tests for LLM provider module and proxy server.
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


class TestProxyServer:
    """Tests for the proxy server module."""

    def test_get_provider_returns_claude_cli_provider(self):
        """get_provider returns ClaudeCLIProvider instance."""
        from src.controllers.proxy.server import get_provider
        from src.external.llm import ClaudeCLIProvider

        # Reset the cached provider
        import src.controllers.proxy.server as proxy_module
        proxy_module._provider = None

        provider = get_provider()
        assert isinstance(provider, ClaudeCLIProvider)

    def test_get_provider_caches_instance(self):
        """get_provider returns same instance on subsequent calls."""
        from src.controllers.proxy.server import get_provider

        # Reset the cached provider
        import src.controllers.proxy.server as proxy_module
        proxy_module._provider = None

        provider1 = get_provider()
        provider2 = get_provider()
        assert provider1 is provider2

    @patch("src.controllers.proxy.server.get_provider")
    def test_generate_with_claude_delegates_to_provider(self, mock_get_provider):
        """generate_with_claude delegates to ClaudeCLIProvider.generate."""
        from src.controllers.proxy.server import generate_with_claude
        from src.external.llm import LLMResponse

        mock_provider = MagicMock()
        mock_provider.generate.return_value = LLMResponse(
            text="Generated text",
            model="haiku",
            tokens_used=10,
            latency_ms=100,
            provider="claude-cli",
        )
        mock_get_provider.return_value = mock_provider

        result = generate_with_claude("Test prompt", model="haiku", max_tokens=500)

        assert result == "Generated text"
        mock_provider.generate.assert_called_once()
        call_args = mock_provider.generate.call_args
        assert call_args[0][0] == "Test prompt"
        assert call_args[0][1].model == "haiku"
        assert call_args[0][1].max_tokens == 500
        assert call_args[0][1].timeout == 120

    @patch("src.controllers.proxy.server.get_provider")
    def test_generate_with_claude_returns_none_on_error(self, mock_get_provider):
        """generate_with_claude returns None when provider raises."""
        from src.controllers.proxy.server import generate_with_claude

        mock_provider = MagicMock()
        mock_provider.generate.side_effect = Exception("Provider error")
        mock_get_provider.return_value = mock_provider

        result = generate_with_claude("Test prompt")

        assert result is None

    @patch("src.controllers.proxy.server.generate_with_claude")
    def test_summarize_with_claude_uses_prompt_template(self, mock_generate):
        """summarize_with_claude wraps transcript in SUMMARIZE_PROMPT."""
        from src.controllers.proxy.server import summarize_with_claude, SUMMARIZE_PROMPT

        mock_generate.return_value = "Summary text"

        result = summarize_with_claude("Test transcript", model="sonnet")

        assert result == "Summary text"
        mock_generate.assert_called_once()
        call_args = mock_generate.call_args
        # Check that the prompt contains the transcript
        assert "Test transcript" in call_args[0][0]
        assert call_args[0][1] == "sonnet"
