"""
Tests for ProfileResolutionStep handoff handling.
"""

from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest

from services.workflows.base import StepAction
from services.workflows.steps.profile_resolution_step import ProfileResolutionStep
from utils.models import CanonicalRequestMessage, CanonicalResponseMessage
from utils.sessions import Session


@pytest.mark.asyncio
class TestProfileResolutionStepHandoff:
    """Test profile resolution step handoff functionality."""

    @pytest.fixture
    def profile_resolution_step(self):
        """Create a ProfileResolutionStep instance for testing."""
        return ProfileResolutionStep()

    @pytest.fixture
    def mock_message(self):
        """Create a mock CanonicalRequestMessage."""
        message = MagicMock(spec=CanonicalRequestMessage)
        message.create_text_response = MagicMock()
        message.selected_reply = None  # Add this attribute
        return message

    @pytest.fixture
    def mock_session(self):
        """Create a mock Session."""
        session = MagicMock(spec=Session)
        session.user_id = UUID("12345678-1234-5678-1234-567812345678")
        session.current_profile_id = None  # Add this attribute
        return session

    async def test_no_handoff_data_normal_flow(
        self, profile_resolution_step, mock_message, mock_session
    ):
        """Test that normal flow continues when no handoff data is present."""
        # Setup mocks by patching the instance attribute
        with patch.object(profile_resolution_step, "profile_dao") as mock_profile_dao:
            mock_profile_dao.get_profiles_for_user.return_value = []

            # Mock the response creation
            mock_response = MagicMock(spec=CanonicalResponseMessage)
            mock_message.create_text_response.return_value = mock_response

            # Create workflow context with no handoff data
            workflow_context = {}

            # Execute the step
            result = await profile_resolution_step.execute(
                mock_message, mock_session, "test_workflow", workflow_context
            )

            # Verify the result continues to normal flow
            assert result.action == StepAction.JUMP
            assert result.next_step_id == "profile_addition_step"
