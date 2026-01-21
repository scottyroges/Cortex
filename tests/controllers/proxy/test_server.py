"""
Tests for the proxy server module (src/controllers/proxy/server.py).
"""

from unittest.mock import MagicMock, patch

import pytest


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
