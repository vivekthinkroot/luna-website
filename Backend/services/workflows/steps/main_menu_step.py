"""
Main menu workflow step for Luna.

This step provides a main menu interface that can be invoked at any time
with slash commands like /luna, /menu, or /help.
"""

from typing import Any, Dict

from services.workflows.base import StepAction, StepResult, WorkflowStep
from services.workflows.ids import Steps, Workflows
from utils.logger import get_logger
from utils.models import CanonicalRequestMessage, QuickReplyOption
from utils.sessions import Session

logger = get_logger()

# Welcome message for new users
NEW_USER_WELCOME_MESSAGE = (
    "🙏 Welcome to Luna, your personal Vedic astrology guide.\n\n"
    "Here's what I can help you with:\n\n"
    "• **Generate Kundli** - Create your vedic birth chart with detailed analysis\n"
    "• **Astro Consultation** - Get personalized answers to your astrology questions\n\n"
    "Just send */Luna* at any time to return to this menu\n\n"
    "What would you like to explore today?"
)

# Main menu message for returning users
RETURNING_USER_MENU_MESSAGE = (
    "🌟 Welcome back to Luna!\n\n"
    "Here's what I can help you with:\n\n"
    "• **Generate Kundli** - Create your vedic birth chart with detailed analysis\n"
    "• **Astro Consultation** - Get personalized answers to your astrology questions\n\n"
    "Just send */Luna* at any time to return to this menu\n\n"
    "What would you like to explore today?"
)

# Quick reply options for main menu
MAIN_MENU_QUICK_REPLIES = [
    QuickReplyOption.build(
        Workflows.GENERATE_KUNDLI.value, "generate_kundli", "Generate my Kundli"
    ),
    QuickReplyOption.build(
        Workflows.PROFILE_QNA.value, "astro_consultation", "Astro Consultation"
    ),
]


class MainMenuStep(WorkflowStep):
    """
    Workflow step for the main menu interface.

    This step provides a welcoming main menu that can be invoked at any time
    during a conversation. It presents the user with available options and
    allows them to navigate to different workflows.
    """

    def __init__(self):
        super().__init__(Steps.MAIN_MENU_STEP.value)

    def _is_new_user(self, session: Session) -> bool:
        """
        Determine if the user is new to Luna based on conversation history.

        Args:
            session: User session data

        Returns:
            bool: True if user is new (no conversation history), False otherwise
        """
        # Check if user has any conversation history
        return len(session.conversation_history) == 1

    async def execute(
        self,
        message: CanonicalRequestMessage,
        session: Session,
        workflow_id: str,
        workflow_context: Dict[str, Any],
    ) -> StepResult:
        """
        Execute the main menu step.

        Provides an appropriate message based on whether the user is new or returning,
        and presents available options to the user.
        """
        logger.info(f"Executing main menu step for user: {session.user_id}")

        # Determine if user is new and select appropriate message
        is_new_user = self._is_new_user(session)
        if is_new_user:
            content = NEW_USER_WELCOME_MESSAGE
            logger.info(
                f"User {session.user_id} is new to Luna - showing welcome message"
            )
        else:
            content = RETURNING_USER_MENU_MESSAGE
            logger.info(f"User {session.user_id} is returning - showing main menu")

        # Create response with main menu options
        response = message.create_text_response(
            content=content,
            metadata={
                "workflow_step": self.step_id,
                "workflow_id": workflow_id,
                "user_message": message.content,
                "is_main_menu": True,
                "is_new_user": is_new_user,
            },
            reply_options=MAIN_MENU_QUICK_REPLIES,
        )

        # Complete the workflow after showing the menu
        # The user will select an option which will trigger a new workflow
        return StepResult(
            response=response,
            action=StepAction.COMPLETE,
            context_updates={
                "main_menu_shown": True,
                "is_new_user": is_new_user,
                "timestamp": message.timestamp.isoformat(),
            },
        )
