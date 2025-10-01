"""
Native fallback workflow steps for handling unknown intents.

These steps provide graceful handling of unclear or unclassifiable user messages.
"""

from typing import Any, Dict, Optional

from services.workflows.base import StepAction, StepResult, WorkflowStep
from services.workflows.ids import Steps, Workflows
from utils.logger import get_logger
from utils.models import CanonicalRequestMessage, QuickReplyOption
from utils.sessions import Session

logger = get_logger()

# Response messages for fallback scenarios
UNKNOWN_FALLBACK_MESSAGE = (
    "I'm not sure what you're asking for. I can help you with:\n\n"
    "• **Generating your kundli** (birth chart) - Just tell me you want your kundli\n"
    "• **Managing your profiles** - Add or update birth details for your or your family\n\n"
    "Just send */Luna* at any time to return to the main menu\n\n"
    "Could you please rephrase your request or let me know which of these you'd like help with?"
)

WELCOME_MESSAGE = (
    "Namaste! 🙏 Welcome to Luna, your personal Vedic astrology guide.\n\n"
    "Here is what I can do for you:\n\n"
    "• **Generate your kundli** - Create your vedic birth chart with detailed analysis\n"
    "• **Get predictions** - Daily horoscopes and insights\n\n"
    "Just send */Luna* at any time to return to this menu\n\n"
    "What would you like to explore today?"
)

# Quick reply options for user interactions
WELCOME_QUICK_REPLIES = [
    QuickReplyOption.build(
        Workflows.GENERATE_KUNDLI.value, "generate_kundli", "Generate my Kundli"
    )
]

FALLBACK_QUICK_REPLIES = [
    QuickReplyOption.build(
        Workflows.GENERATE_KUNDLI.value, "generate_kundli", "Generate my Kundli"
    ),
]


class UnknownFallbackStep(WorkflowStep):
    """
    Workflow step for handling unknown or unclear user intents.

    Provides a helpful fallback response when the system cannot
    understand what the user is asking for. For first-time users,
    sends a welcome message instead of a fallback response.
    """

    def __init__(self):
        super().__init__(Steps.UNKNOWN_FALLBACK.value)

    async def execute(
        self,
        message: CanonicalRequestMessage,
        session: Session,
        workflow_id: str,
        workflow_context: Dict[str, Any],
    ) -> StepResult:
        """
        Execute the unknown fallback step.

        Provides a helpful message to the user and suggests available options.
        Detects first-time users and sends a welcome message instead of fallback.
        """
        logger.info(
            f"Executing unknown fallback for message: {message.content[:50]}..."
        )

        # Check if this is the first message from the user
        is_first_message = len(session.conversation_history) == 1

        if is_first_message:
            # Send welcome message for new users
            logger.info(f"Sending welcome message to new user: {session.user_id}")
            response = message.create_text_response(
                content=WELCOME_MESSAGE,
                metadata={
                    "workflow_step": self.step_id,
                    "user_message": message.content,
                    "is_first_message": True,
                },
                reply_options=WELCOME_QUICK_REPLIES,
            )
        else:
            # Send fallback message for existing users
            response = message.create_text_response(
                content=UNKNOWN_FALLBACK_MESSAGE,
                metadata={
                    "intent": "unknown",
                    "workflow_step": self.step_id,
                    "user_message": message.content,
                },
                reply_options=FALLBACK_QUICK_REPLIES,
            )

        # Complete the workflow - no need for multiple steps
        return StepResult(
            action=StepAction.COMPLETE,
            response=response,
            context_updates={"fallback_handled": True},
        )

    async def on_event(
        self,
        event_type: str,
        event_data: Dict[str, Any],
        workflow_id: str,
        workflow_context: Dict[str, Any],
    ) -> Optional[StepResult]:
        """Handle events - not applicable for fallback step."""
        logger.warning(f"Unexpected event {event_type} for fallback step")
        return None
