"""
Profile Q&A step: Multi-turn Q&A session based on a user profile.

This step provides ongoing Q&A based on the selected profile using LLM responses.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel

from dao.profiles import Profile, ProfileDAO
from llms.client import LLMClient
from llms.models import LLMMessage, LLMMessageRole, LLMResponseType
from qna.system_prompt_service import SystemPromptService
from services.workflows.base import StepAction, StepResult, WorkflowStep
from services.workflows.ids import Steps
from utils.logger import get_logger
from utils.models import CanonicalRequestMessage, QuickReplyOption
from utils.sessions import Session

logger = get_logger()

# ===== Response Content Constants =====
CHANGE_PROFILE_MESSAGE = (
    "Alright, let's select a different profile for your Astrological consultation."
)
PROFILE_NOT_FOUND_MESSAGE = (
    "I couldn't find that profile. Let's select a different one."
)
PROFILE_NOT_FOUND_FALLBACK = (
    "I need to know which profile you'd like to discuss. Let's start over."
)
WELCOME_MESSAGE_TEMPLATE = "Great! I'm ready to answer your questions about {profile_name} astrological profile. What would you like to know?\n\n(You can also switch to a different profile if needed.)"
ERROR_MESSAGE = (
    "I apologize, but I couldn't process that. Could you please rephrase your question?"
)


# ===== Structured Response Objects =====
class QueryCategory(str, Enum):
    """Categories for astrological queries."""

    FINANCE = "finance"
    HEALTH = "health"
    RELATIONSHIPS = "relationships"
    CAREER = "career"
    EDUCATION = "education"
    TRAVEL = "travel"
    SPIRITUALITY = "spirituality"
    GENERAL = "general"
    OTHER = "other"


class ProfileQnAResponse(BaseModel):
    """Structured response from LLM for profile Q&A."""

    response_text: str
    query_category: QueryCategory
    confidence: float = 0.8
    wants_to_switch_profile: bool = False


class ProfileQnAContext(BaseModel):
    """Structured workflow context for profile Q&A sessions."""

    conversation_history: List[LLMMessage] = []
    current_query_category: Optional[QueryCategory] = None
    profile_id: Optional[str] = None
    session_started: bool = False


class ProfileQnaStep(WorkflowStep):
    """
    Workflow step for multi-turn Q&A sessions based on user profiles.

    This step provides ongoing Q&A based on the selected profile using LLM responses.
    """

    def __init__(self):
        super().__init__(Steps.PROFILE_QNA_STEP.value)
        self.llm_client = LLMClient()
        self.profile_dao = ProfileDAO()
        self.system_prompt_service = SystemPromptService()
        self.workflow_id: str = "profile_qna"

    def _get_qna_options(self) -> List[QuickReplyOption]:
        """Get quick reply options for the Q&A session."""
        return [
            QuickReplyOption.build(
                self.workflow_id, "change_profile", "Switch profile"
            ),
        ]

    def _get_system_prompt_for_profile(self, profile_id: str) -> str:
        """Get the comprehensive system prompt for the profile using SystemPromptService."""
        return self.system_prompt_service.construct_system_prompt(profile_id)

    async def execute(
        self,
        message: CanonicalRequestMessage,
        session: Session,
        workflow_id: str,
        workflow_context: Dict[str, Any],
    ) -> StepResult:
        """Execute the profile Q&A step."""
        try:
            self.workflow_id = workflow_id

            # Handle quick reply actions first
            if message.selected_reply and message.selected_reply.has_valid_format():
                action = message.selected_reply.get_action()

                if action == "change_profile":
                    # Clear current profile selection and jump back to profile resolution
                    return StepResult(
                        response=message.create_text_response(
                            content=CHANGE_PROFILE_MESSAGE,
                            metadata={"workflow_step": self.step_id},
                        ),
                        action=StepAction.JUMP,
                        next_step_id=Steps.PROFILE_RESOLUTION.value,
                    )

            # Get or create structured context
            context_data = workflow_context.get("profile_qna_state", {})
            qna_context = ProfileQnAContext(**context_data)

            # At this point, we should have a profile from the previous step
            # Get the profile from session (set by profile resolution step)
            profile_id = session.current_profile_id
            if not profile_id:
                # This shouldn't happen if profile resolution step worked correctly
                response = message.create_text_response(
                    content=PROFILE_NOT_FOUND_FALLBACK,
                    metadata={"workflow_step": self.step_id},
                )
                return StepResult(
                    response=response,
                    action=StepAction.JUMP,
                    next_step_id=Steps.PROFILE_RESOLUTION.value,
                )

            # Get profile and start Q&A
            profile = self.profile_dao.get_profile_by_id(str(profile_id))
            if not profile:
                # ideally, this should never happen
                response = message.create_text_response(
                    content=PROFILE_NOT_FOUND_MESSAGE,
                    metadata={"workflow_step": self.step_id},
                )
                return StepResult(
                    response=response,
                    action=StepAction.JUMP,
                    next_step_id=Steps.PROFILE_RESOLUTION.value,
                )

            # Update context with profile ID
            qna_context.profile_id = str(profile.profile_id)

            # Check if this is the first message in the Q&A session
            if not qna_context.session_started:
                # First message - provide a welcome and ask what they'd like to know
                profile_name = (profile.name + "'s") if profile.name else "your"
                welcome_message = WELCOME_MESSAGE_TEMPLATE.format(
                    profile_name=profile_name
                )

                response = message.create_text_response(
                    content=welcome_message,
                    metadata={
                        "workflow_step": self.step_id,
                        "continue_multi_turn": True,
                        "profile_id": str(profile.profile_id),
                    },
                    reply_options=self._get_qna_options(),
                )

                qna_context.session_started = True
                return StepResult(
                    response=response,
                    action=StepAction.REPEAT,
                    context_updates={"profile_qna_state": qna_context.model_dump()},
                )
            else:
                # Continue existing Q&A interaction
                return await self._handle_qna_interaction(message, profile, qna_context)

        except Exception as e:
            logger.exception(f"Error in ProfileQnaStep: {e}")
            response = message.create_text_response(
                content=ERROR_MESSAGE,
                metadata={"workflow_step": self.step_id, "error": str(e)},
            )
            return StepResult(response=response, action=StepAction.COMPLETE)

    async def _handle_qna_interaction(
        self,
        message: CanonicalRequestMessage,
        profile: Profile,
        qna_context: ProfileQnAContext,
    ) -> StepResult:
        """Handle the actual Q&A interaction with the LLM."""
        try:
            # Create system prompt with comprehensive profile information
            system_prompt = self._get_system_prompt_for_profile(str(profile.profile_id))

            # Create user message
            user_message = LLMMessage(role=LLMMessageRole.USER, content=message.content)

            # Get conversation history for context
            messages = [
                LLMMessage(role=LLMMessageRole.SYSTEM, content=system_prompt),
                *qna_context.conversation_history,
                user_message,
            ]

            # Get LLM response with structured output
            llm_response = await self.llm_client.get_response(
                messages=messages,
                temperature=0.7,
                max_tokens=250,
                response_model=ProfileQnAResponse,
            )

            if (
                llm_response.response_type == LLMResponseType.OBJECT
                and llm_response.object
            ):
                # Get the structured response object
                parsed_response: ProfileQnAResponse = llm_response.object

                # Update conversation history
                updated_history = qna_context.conversation_history + [user_message]
                updated_history.append(
                    LLMMessage(
                        role=LLMMessageRole.ASSISTANT,
                        content=parsed_response.response_text,
                    )
                )

                # Keep only last 20 messages to avoid context getting too long
                if len(updated_history) > 20:
                    updated_history = updated_history[-20:]

                # Update context
                qna_context.conversation_history = updated_history
                qna_context.current_query_category = parsed_response.query_category

                # Check if user wants to switch profiles
                if parsed_response.wants_to_switch_profile:
                    # User wants to switch profiles - transition to profile resolution
                    noop_response = message.create_text_response(
                        content="",
                        metadata={"internal_noop": True},
                    )

                    return StepResult(
                        response=noop_response,
                        action=StepAction.ADVANCE_NOW,
                        next_step_id=Steps.PROFILE_RESOLUTION.value,
                        context_updates={
                            "_handoff": {
                                "user_requested_switch_profile": True,
                            }
                        },
                    )

                response = message.create_text_response(
                    content=parsed_response.response_text,
                    metadata={
                        "workflow_step": self.step_id,
                        "continue_multi_turn": True,
                        "profile_id": str(profile.profile_id),
                        "llm_response": True,
                        "query_category": parsed_response.query_category.value,
                    },
                )

                return StepResult(
                    response=response,
                    action=StepAction.REPEAT,
                    context_updates={"profile_qna_state": qna_context.model_dump()},
                )
            else:
                # Fallback response if LLM fails
                response = message.create_text_response(
                    content=ERROR_MESSAGE,
                    metadata={
                        "workflow_step": self.step_id,
                        "continue_multi_turn": True,
                    },
                )
                return StepResult(response=response, action=StepAction.REPEAT)

        except Exception as e:
            logger.exception(f"Error in Q&A interaction: {e}")
            response = message.create_text_response(
                content=ERROR_MESSAGE,
                metadata={
                    "workflow_step": self.step_id,
                    "continue_multi_turn": True,
                    "error": str(e),
                },
            )
            return StepResult(response=response, action=StepAction.REPEAT)
