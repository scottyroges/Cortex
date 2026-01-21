"""
Tests for utility modules (src/utils/).
"""

import pytest

from src.utils.secret_scrubber import scrub_secrets


class TestSecretScrubbing:
    """Tests for secret scrubbing functionality."""

    def test_aws_access_key_scrubbed(self):
        """Test AWS access key is redacted."""
        text = 'AWS_KEY = "AKIAIOSFODNN7EXAMPLE"'
        result = scrub_secrets(text)
        assert "AKIAIOSFODNN7EXAMPLE" not in result
        assert "[AWS_ACCESS_KEY_REDACTED]" in result

    def test_github_pat_scrubbed(self):
        """Test GitHub PAT is redacted."""
        text = "token = ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        result = scrub_secrets(text)
        assert "ghp_" not in result
        assert "[GITHUB_PAT_REDACTED]" in result

    def test_stripe_key_scrubbed(self):
        """Test Stripe secret key is redacted."""
        # Key must be 24+ chars after sk_test_ to match pattern
        text = "STRIPE_KEY = sk_test_TESTKEY1234567890abcdefgh"
        result = scrub_secrets(text)
        assert "sk_test_" not in result
        assert "[STRIPE_SECRET_REDACTED]" in result

    def test_anthropic_key_scrubbed(self):
        """Test Anthropic API key is redacted."""
        text = "ANTHROPIC_API_KEY = sk-ant-api03-xxxxxxxxxxxxxxxxxxxxx"
        result = scrub_secrets(text)
        assert "sk-ant-" not in result
        assert "[ANTHROPIC_KEY_REDACTED]" in result

    def test_private_key_scrubbed(self):
        """Test private key header is redacted."""
        text = "-----BEGIN RSA PRIVATE KEY-----\nMIIE..."
        result = scrub_secrets(text)
        assert "BEGIN RSA PRIVATE KEY" not in result
        assert "[PRIVATE_KEY_REDACTED]" in result

    def test_slack_token_scrubbed(self):
        """Test Slack token is redacted."""
        text = "SLACK_TOKEN = xoxb-123456789-abcdefghijk"
        result = scrub_secrets(text)
        assert "xoxb-" not in result
        assert "[SLACK_TOKEN_REDACTED]" in result

    def test_normal_text_preserved(self):
        """Test normal text is not modified."""
        text = "This is normal code without any secrets. URL = https://api.example.com"
        result = scrub_secrets(text)
        assert result == text

    def test_generic_api_key_scrubbed(self):
        """Test generic API key assignments are redacted."""
        text = 'api_key = "super_secret_key_12345678"'
        result = scrub_secrets(text)
        assert "super_secret_key" not in result
        assert "[SECRET_REDACTED]" in result
