"""
Tests for the main menu workflow functionality.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from services.workflows.steps.main_menu_step import MAIN_MENU_MESSAGE, MainMenuStep
from utils.models import CanonicalRequestMessage, ContentType
from utils.sessions import Session


class TestMainMenuStep:
    """Test cases for the MainMenuStep class."""

    @pytest.fixture
    def step(self):
        """Create a MainMenuStep instance for testing."""
        return MainMenuStep()

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

    @pytest.fixture
    def mock_session(self):
        """Create a mock Session for testing."""
        session = MagicMock(spec=Session)
        session.user_id = "test_user_123"
        session.conversation_history = []
        return session

    @pytest.fixture
    def mock_workflow_context(self):
        """Create a mock workflow context for testing."""
        return {}

    def test_step_initialization(self, step):
        """Test that the step is properly initialized."""
        assert step.step_id == "main_menu_step"

    def test_main_menu_message_content(self, step):
        """Test that the main menu message contains expected content."""
        assert "Namaste" in MAIN_MENU_MESSAGE
        assert "Generate Kundli" in MAIN_MENU_MESSAGE
        assert "Astro Consultation" in MAIN_MENU_MESSAGE

    def test_quick_replies_are_defined(self, step):
        """Test that quick reply options are properly defined."""
        from services.workflows.steps.main_menu_step import MAIN_MENU_QUICK_REPLIES

        assert len(MAIN_MENU_QUICK_REPLIES) == 2

        # Check first option (Generate Kundli)
        assert MAIN_MENU_QUICK_REPLIES[0].text == "Generate my Kundli"
        assert "generate_kundli" in MAIN_MENU_QUICK_REPLIES[0].id

        # Check second option (Astro Consultation)
        assert MAIN_MENU_QUICK_REPLIES[1].text == "Astro Consultation"
        assert "profile_qna" in MAIN_MENU_QUICK_REPLIES[1].id

    def test_step_has_required_methods(self, step):
        """Test that the step has the required methods."""
        assert hasattr(step, "execute")
        assert hasattr(step, "get_step_id")
        assert callable(step.execute)
        assert callable(step.get_step_id)
