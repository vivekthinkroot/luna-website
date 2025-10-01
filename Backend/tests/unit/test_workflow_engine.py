"""
Unit tests for the workflow engine implementation.

These tests validate that the workflow engine correctly executes
legacy handler steps and maintains the same behavior as the
traditional handler approach.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from data.models import ChannelType
from services.workflows.engine import WorkflowEngine
from services.workflows.registry import get_workflow_registry
from services.workflows.setup import initialize_workflows
from utils.models import CanonicalRequestMessage, CanonicalResponseMessage, ContentType
from utils.sessions import Session


class TestWorkflowEngine:
    """Test cases for WorkflowEngine."""

    @pytest.fixture
    def workflow_engine(self):
        """Create workflow engine with test setup."""
        # Clear registry and initialize fresh
        registry = get_workflow_registry()
        registry._workflows.clear()
        registry._steps.clear()

        initialize_workflows()
        return WorkflowEngine()

    @pytest.fixture
    def sample_message(self):
        """Create a sample canonical request message."""
        return CanonicalRequestMessage(
            user_id="550e8400-e29b-41d4-a716-446655440000",  # Valid UUID format
            channel_type="telegram",
            channel_user_id="telegram_user_456",
            content_type=ContentType.TEXT,
            content="I want to create my profile",
            metadata={},
            timestamp=datetime.now(timezone.utc),
        )

    @pytest.fixture
    def sample_session(self):
        """Create a sample session."""
        return Session(
            user_id="550e8400-e29b-41d4-a716-446655440000",  # Valid UUID format
            channel_type=ChannelType.TELEGRAM,
            conversation_history=[],
            session_metadata={},
            active_intent=None,
            current_profile_id=None,
        )

    @pytest.mark.asyncio
    async def test_workflow_engine_initialization(self, workflow_engine):
        """Test that workflow engine initializes correctly."""
        assert workflow_engine.registry is not None

        # Check that workflows are registered
        workflows = workflow_engine.registry.list_workflows()
        assert "generate_kundli" in workflows
        assert "profile_qna" in workflows

        # Check that steps are registered
        steps = workflow_engine.registry.list_steps()
        assert "profile_resolution_step" in steps
        assert "kundli_generation_step" in steps

    @pytest.mark.asyncio
    async def test_unknown_workflow_handling(
        self, workflow_engine, sample_message, sample_session
    ):
        """Test handling of unknown workflow IDs."""
        response = await workflow_engine.execute_workflow(
            "unknown_workflow", sample_message, sample_session
        )

        assert response.content_type == ContentType.TEXT
        # Check that error is properly handled (either in content or metadata)
        assert (
            "error" in response.content.lower()
            or response.metadata.get("error") is not None
        )

    @pytest.mark.asyncio
    @patch("kundli.add_profile_handler.AddProfileHandler.handle")
    async def test_add_profile_workflow_delegation(
        self, mock_handler, workflow_engine, sample_message, sample_session
    ):
        """Test that add_profile workflow correctly delegates to legacy handler."""
        # Mock the handler response
        expected_response = CanonicalResponseMessage(
            user_id=sample_message.user_id,
            channel_type=sample_message.channel_type,
            channel_user_id=sample_message.channel_user_id,
            content_type=ContentType.TEXT,
            content="Please tell me your name.",
            metadata={"continue_multi_turn": True},
            timestamp=datetime.now(timezone.utc),
        )
        mock_handler.return_value = expected_response

        # Execute workflow
        response = await workflow_engine.execute_workflow(
            "add_profile", sample_message, sample_session
        )

        # Verify handler was called
        mock_handler.assert_called_once_with(sample_message, sample_session)

        # Verify response matches expected
        assert response.content == expected_response.content
        assert response.metadata.get("continue_multi_turn") == True

    @pytest.mark.asyncio
    @patch("kundli.generate_kundli_handler.GenerateKundliHandler.handle")
    async def test_generate_kundli_workflow_delegation(
        self, mock_handler, workflow_engine, sample_message, sample_session
    ):
        """Test that generate_kundli workflow correctly delegates to legacy handler."""
        # Set up session with profile (required for kundli generation)
        sample_session.current_profile_id = "profile_123"

        # Mock the handler response
        expected_response = CanonicalResponseMessage(
            user_id=sample_message.user_id,
            channel_type=sample_message.channel_type,
            channel_user_id=sample_message.channel_user_id,
            content_type=ContentType.TEXT,
            content="Your sun sign is Aries. Would you like a detailed kundli?",
            metadata={"continue_multi_turn": True},
            timestamp=datetime.now(timezone.utc),
        )
        mock_handler.return_value = expected_response

        # Execute workflow
        response = await workflow_engine.execute_workflow(
            "generate_kundli", sample_message, sample_session
        )

        # Verify handler was called
        mock_handler.assert_called_once_with(sample_message, sample_session)

        # Verify response matches expected
        assert response.content == expected_response.content

    @pytest.mark.asyncio
    async def test_workflow_context_persistence(
        self, workflow_engine, sample_message, sample_session
    ):
        """Test that workflow context is properly stored in session."""
        # Before workflow execution
        assert "workflows" not in sample_session.session_metadata

        with patch(
            "kundli.add_profile_handler.AddProfileHandler.handle"
        ) as mock_handler:
            mock_response = CanonicalResponseMessage(
                user_id=sample_message.user_id,
                channel_type=sample_message.channel_type,
                channel_user_id=sample_message.channel_user_id,
                content_type=ContentType.TEXT,
                content="Please tell me your name.",
                metadata={"continue_multi_turn": True},
                timestamp=datetime.now(timezone.utc),
            )
            mock_handler.return_value = mock_response

            # Execute workflow
            await workflow_engine.execute_workflow(
                "add_profile", sample_message, sample_session
            )

        # After workflow execution, context should be stored
        assert "workflows" in sample_session.session_metadata
        assert "add_profile" in sample_session.session_metadata["workflows"]

        workflow_context = sample_session.session_metadata["workflows"]["add_profile"]
        assert workflow_context["workflow_id"] == "add_profile"
        assert workflow_context["current_step_id"] == "add_profile"

    def test_workflow_registry_validation(self):
        """Test that workflow registry validates workflows correctly."""
        registry = get_workflow_registry()

        # Valid workflows should validate successfully
        assert registry.validate_workflow("add_profile") == True
        assert registry.validate_workflow("generate_kundli") == True
        assert registry.validate_workflow("profile_qna") == True

        # Invalid workflow should fail validation
        assert registry.validate_workflow("nonexistent_workflow") == False

    @pytest.mark.asyncio
    async def test_workflow_transition_to_generate_kundli(
        self, workflow_engine, sample_message, sample_session
    ):
        """Test that profile resolution can transition to generate_kundli workflow."""
        with patch(
            "services.workflows.steps.profile_resolution_step.ProfileResolutionStep.execute"
        ) as mock_profile_resolution, patch(
            "kundli.add_profile.AddProfileStep.execute"
        ) as mock_profile_addition:
            # Mock the profile resolution step to return a JUMP to generate_kundli workflow
            from services.workflows.base import StepAction, StepResult
            from services.workflows.ids import Steps, Workflows

            jump_response = sample_message.create_text_response(
                content="Creating new profile and transitioning to kundli generation",
                metadata={"continue_multi_turn": True},
            )

            mock_profile_resolution.return_value = StepResult(
                response=jump_response,
                action=StepAction.JUMP,
                next_step_id=Steps.PROFILE_ADDITION.value,
                next_workflow_id=Workflows.GENERATE_KUNDLI.value,
            )

            # Mock the profile addition step to avoid LLM calls
            profile_addition_response = sample_message.create_text_response(
                content="Profile created successfully",
                metadata={"continue_multi_turn": False},
            )

            mock_profile_addition.return_value = StepResult(
                response=profile_addition_response,
                action=StepAction.CONTINUE,
            )

            # Execute the generate_kundli workflow (which starts with profile resolution)
            response = await workflow_engine.execute_workflow(
                Workflows.GENERATE_KUNDLI.value, sample_message, sample_session
            )

            # Verify the profile resolution step was called
            mock_profile_resolution.assert_called_once()

            # Profile addition step should NOT be called immediately after workflow transition
            # The engine now just sets up the context and waits for the next user message
            mock_profile_addition.assert_not_called()

            # Verify the response matches the profile resolution response (not profile addition)
            assert (
                response.content
                == "Creating new profile and transitioning to kundli generation"
            )

            # Verify that the workflow context was set up for generate_kundli
            assert "workflows" in sample_session.session_metadata
            assert "generate_kundli" in sample_session.session_metadata["workflows"]


class TestLegacyWrapperSteps:
    """Test cases for legacy wrapper steps."""

    @pytest.fixture
    def sample_message(self):
        """Create a sample canonical request message."""
        return CanonicalRequestMessage(
            user_id="550e8400-e29b-41d4-a716-446655440000",  # Valid UUID format
            channel_type="telegram",
            channel_user_id="telegram_user_456",
            content_type=ContentType.TEXT,
            content="My name is John",
            metadata={},
            timestamp=datetime.now(timezone.utc),
        )

    @pytest.fixture
    def sample_session(self):
        """Create a sample session."""
        return Session(
            user_id="550e8400-e29b-41d4-a716-446655440000",  # Valid UUID format
            channel_type=ChannelType.TELEGRAM,
            conversation_history=[],
            session_metadata={},
            active_intent=None,
            current_profile_id=None,
        )
