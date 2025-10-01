"""
Tests for slash command detection in the router.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from services.router import LunaRouter
from utils.models import CanonicalRequestMessage, ContentType


class TestSlashCommandDetection:
    """Test cases for slash command detection in the router."""

    @pytest.fixture
    def router(self):
        """Create a LunaRouter instance for testing."""
        return LunaRouter()

    @pytest.fixture
    def mock_message(self):
        """Create a mock CanonicalRequestMessage for testing."""
        return CanonicalRequestMessage(
            user_id="test_user_123",
            channel_type="telegram",
            channel_user_id="telegram_user_456",
            content_type=ContentType.TEXT,
            content="/luna",
            metadata={},
            timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

    def test_slash_command_detection_luna(self, router):
        """Test that /luna is detected as a slash command."""
        message = CanonicalRequestMessage(
            user_id="test_user_123",
            channel_type="telegram",
            channel_user_id="telegram_user_456",
            content_type=ContentType.TEXT,
            content="/luna",
            metadata={},
            timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

        assert router._is_slash_command(message) is True

    def test_slash_command_detection_menu(self, router):
        """Test that /menu is detected as a slash command."""
        message = CanonicalRequestMessage(
            user_id="test_user_123",
            channel_type="telegram",
            channel_user_id="telegram_user_456",
            content_type=ContentType.TEXT,
            content="/menu",
            metadata={},
            timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

        assert router._is_slash_command(message) is True

    def test_slash_command_detection_help(self, router):
        """Test that /help is detected as a slash command."""
        message = CanonicalRequestMessage(
            user_id="test_user_123",
            channel_type="telegram",
            channel_user_id="telegram_user_456",
            content_type=ContentType.TEXT,
            content="/help",
            metadata={},
            timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

        assert router._is_slash_command(message) is True

    def test_slash_command_detection_case_insensitive(self, router):
        """Test that slash commands are detected case-insensitively."""
        message = CanonicalRequestMessage(
            user_id="test_user_123",
            channel_type="telegram",
            channel_user_id="telegram_user_456",
            content_type=ContentType.TEXT,
            content="/LUNA",
            metadata={},
            timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

        assert router._is_slash_command(message) is True

    def test_slash_command_detection_with_whitespace(self, router):
        """Test that slash commands with leading whitespace are detected."""
        message = CanonicalRequestMessage(
            user_id="test_user_123",
            channel_type="telegram",
            channel_user_id="telegram_user_456",
            content_type=ContentType.TEXT,
            content="  /luna",
            metadata={},
            timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

        assert router._is_slash_command(message) is True

    def test_non_slash_command_not_detected(self, router):
        """Test that regular messages are not detected as slash commands."""
        message = CanonicalRequestMessage(
            user_id="test_user_123",
            channel_type="telegram",
            channel_user_id="telegram_user_456",
            content_type=ContentType.TEXT,
            content="Hello, I want to generate my kundli",
            metadata={},
            timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

        assert router._is_slash_command(message) is False

    def test_empty_content_not_detected(self, router):
        """Test that empty content is not detected as a slash command."""
        message = CanonicalRequestMessage(
            user_id="test_user_123",
            channel_type="telegram",
            channel_user_id="telegram_user_456",
            content_type=ContentType.TEXT,
            content="",
            metadata={},
            timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

        assert router._is_slash_command(message) is False

    def test_none_content_not_detected(self, router):
        """Test that None content is not detected as a slash command."""
        # For this test, we'll create a message with empty string content
        # since CanonicalRequestMessage requires a string for content
        message = CanonicalRequestMessage(
            user_id="test_user_123",
            channel_type="telegram",
            channel_user_id="telegram_user_456",
            content_type=ContentType.TEXT,
            content="",  # Use empty string instead of None
            metadata={},
            timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

        assert router._is_slash_command(message) is False
