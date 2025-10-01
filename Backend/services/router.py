"""
Router service interface for Luna.
Responsible for intent classification and routing messages to appropriate domain services.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import List, cast

from pydantic import BaseModel

from llms.client import LLMClient
from llms.models import LLMMessage, LLMMessageRole
from services.base import INTENT_DESCRIPTIONS, get_all_intents
from services.prompts import (
    INTENT_CLASSIFICATION_SYSTEM_PROMPT,
    INTENT_CLASSIFICATION_USER_PROMPT,
)
from utils.logger import get_logger
from utils.models import (
    CanonicalRequestMessage,
    CanonicalResponseMessage,
    ContentType,
    IntentType,
)
from utils.sessions import MessageTurn, Session, SessionManager

# Initialize logger
logger = get_logger()


class Router(ABC):
    """Abstract base class for the router service."""

    @abstractmethod
    async def route_to_service(
        self, message: CanonicalRequestMessage
    ) -> CanonicalResponseMessage:
        """
        Route message to appropriate service based on intent.
        Args:
            message (CanonicalRequestMessage): Canonical message from channel handler.
        Returns:
            CanonicalResponseMessage: Service response.
        """
        pass


class IntentResponse(BaseModel):
    """Pydantic model for structured LLM intent classification response."""

    intent: str


class LunaRouter(Router):
    """
    Concrete implementation of Router for Luna.
    Handles intent classification and routing to appropriate domain services.
    """

    def __init__(self):
        self.llm = LLMClient()
        self.session_manager = SessionManager()

        # Initialize workflow engine (required for all intents)
        from services.workflows.engine import WorkflowEngine
        from services.workflows.setup import initialize_workflows

        self.workflow_engine = WorkflowEngine()
        initialize_workflows()

    def _format_history_as_string(
        self, history: List[MessageTurn], limit: int = 5
    ) -> str:
        """
        Format conversation history as a string for LLM prompt.

        Args:
            history (List[MessageTurn]): Conversation history
            limit (int): Maximum number of turns to include

        Returns:
            str: Formatted history string
        """
        recent = history[-limit:] if len(history) > limit else history
        return "\n".join([f"{turn.role}: {turn.content}" for turn in recent])

    def _format_history_as_messages(
        self, history: List[MessageTurn], limit: int = 10
    ) -> List[LLMMessage]:
        """
        Format conversation history as a list of LLMMessage objects for LLMClient.

        Args:
            history (List[MessageTurn]): Conversation history
            limit (int): Maximum number of turns to include

        Returns:
            List[LLMMessage]: List of messages for LLM context
        """
        recent = history[-limit:] if len(history) > limit else history
        messages: List[LLMMessage] = []

        for turn in recent:
            # Map to LLMMessage format
            # Note: LLMMessage expects 'role' to be one of: 'system', 'user', 'assistant'
            role = turn.role
            # Ensure role is one of the expected values
            if role not in ["system", "user", "assistant"]:
                # Default to user if unknown
                role = "user" if role == "user" else "assistant"

            # Create a properly typed LLMMessage
            messages.append(LLMMessage(role=LLMMessageRole(role), content=turn.content))

        return messages

    def _is_slash_command(self, message: CanonicalRequestMessage) -> bool:
        """
        Check if the message is a slash command that should trigger the main menu.

        Args:
            message: The user's message

        Returns:
            bool: True if it's a slash command, False otherwise
        """
        if not message.content:
            return False

        content = message.content.strip().lower()
        slash_commands = ["/luna", "/menu", "/help"]

        return any(content.startswith(cmd) for cmd in slash_commands)

    async def _classify_intent(
        self, message: CanonicalRequestMessage, session: Session
    ) -> str:
        """
        Classify user intent from message by inferring it from selected_reply, or using LLM.

        Args:
            message (CanonicalRequestMessage): User message
            session (Session): Session context

        Returns:
            str: Classified intent name
        """

        try:
            # Check for deterministic quick reply intent first
            if message.selected_reply and message.selected_reply.has_valid_format():
                workflow_id = message.selected_reply.get_workflow_id()
                if workflow_id and workflow_id in get_all_intents():
                    logger.info(
                        f"Deterministic intent from quick reply: {workflow_id} (action: {message.selected_reply.get_action()})"
                    )
                    return workflow_id
                else:
                    logger.warning(f"Invalid quick reply workflow_id: {workflow_id}")

        except Exception as e:
            logger.warning(
                f"Error in intent classification from quick-reply {message.selected_reply}: {e}"
            )
            # continue with LLM classification

        try:
            # Check if this is a slash command first
            if self._is_slash_command(message):
                logger.info(
                    f"Slash command detected, returning main_menu intent: {message.content}"
                )
                return IntentType.MAIN_MENU.value

            # Format conversation history for context
            formatted_history = self._format_history_as_string(
                session.conversation_history
            )

            metadata = session.session_metadata
            active_intent = session.active_intent

            # Build intent descriptions string
            intent_descriptions = ""
            for intent, description in INTENT_DESCRIPTIONS.items():
                intent_descriptions += f"- {intent}: {description}\n"

            # Format system prompt with intent descriptions
            system_prompt = INTENT_CLASSIFICATION_SYSTEM_PROMPT.format(
                intent_descriptions=intent_descriptions
            )

            # Format user prompt with template variables (no intent_descriptions needed)
            user_prompt = INTENT_CLASSIFICATION_USER_PROMPT.format(
                conversation_history=formatted_history,
                active_intent=active_intent,
            )

            # Prepare messages for LLMClient
            messages: List[LLMMessage] = [
                LLMMessage(
                    role=LLMMessageRole.SYSTEM,
                    content=system_prompt,
                ),
                LLMMessage(role=LLMMessageRole.USER, content=user_prompt),
            ]

            # Call LLM with structured response
            response = await self.llm.get_response(
                messages=messages,
                temperature=0.2,  # Low temperature for deterministic classification
                response_model=IntentResponse,
            )

            if response.response_type == "error" or not response.object:
                logger.error(f"LLM intent classification error: {response.error}")
                return "unknown"

            # Access the intent from the structured response object
            # Cast to IntentResponse to help type checking
            intent_response = cast(IntentResponse, response.object)
            intent = intent_response.intent

            # Validate intent is in our list
            if intent not in get_all_intents():
                logger.warning(f"LLM returned invalid intent: {intent}")
                return "unknown"

            logger.info(
                f"Classified intent: {intent} for message: {message.content[:50]}..."
            )
            return intent

        except Exception as e:
            logger.exception(f"Error in intent classification: {e}")
            return "unknown"  # Fallback to unknown intent

    async def route_to_service(
        self, message: CanonicalRequestMessage
    ) -> CanonicalResponseMessage:
        """
        Route message to appropriate service based on classified intent.

        Args:
            message (CanonicalRequestMessage): Canonical message from channel handler

        Returns:
            CanonicalResponseMessage: Service response
        """

        user_id = str(message.user_id) if message.user_id else message.channel_user_id
        if not user_id:
            logger.error("Missing user identification in message")
            return message.create_error_response(
                error_message="Error: Missing user identification"
            )

        # Get or create session, hydrating from the appropriate channel
        session = self.session_manager.get_or_create_session(
            user_id, message.channel_type
        )

        # Add the current message to history
        self.session_manager.update_session(
            user_id,
            MessageTurn(
                role="user",
                content=message.content,
                timestamp=datetime.now(timezone.utc).isoformat(),
                metadata=message.metadata,
            ),
            channel_type=message.channel_type,
        )

        # Classify intent (including slash command detection)
        intent = await self._classify_intent(message, session)

        try:
            # Update active intent in session for future context if classification succeeded
            if intent and intent != "unknown":
                self.session_manager.set_active_intent(
                    user_id, intent, channel_type=message.channel_type
                )

            # Route all intents to workflow engine
            logger.info(f"Routing intent {intent} to workflow engine")
            response = await self.workflow_engine.execute_workflow(
                intent, message, session
            )

            # Add predicted intent to response metadata for testability
            if response.metadata is None:
                response.metadata = {}
            response.metadata["predicted_intent"] = intent

            # Update session with assistant response (no multi-turn logic)
            self.session_manager.update_session(
                user_id,
                MessageTurn(
                    role="assistant",
                    content=response.content,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    metadata=response.metadata,
                ),
                channel_type=message.channel_type,
            )

            return response

        except Exception as e:
            logger.exception(f"Error in handler for intent {intent}: {e}")
            error_response = message.create_error_response()

            # Update session with error response
            self.session_manager.update_session(
                user_id,
                MessageTurn(
                    role="assistant",
                    content=error_response.content,
                    timestamp=error_response.timestamp.isoformat(),
                    metadata={"predicted_intent": "unknown"},  # Also tag errors
                ),
                channel_type=message.channel_type,
            )

            return error_response
