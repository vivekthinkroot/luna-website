"""
Session manager utility for Luna.
Handles user session management and context storage.
"""

import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from pydantic import BaseModel, Field

from config.settings import SessionSettings, get_session_settings
from dao.conversations import ConversationDAO
from dao.profiles import ProfileDAO
from data.models import ChannelType
from utils.logger import get_logger

logger = get_logger()


class MessageTurn(BaseModel):
    """Represents a single message turn in a conversation."""

    role: str  # 'user' or 'assistant'
    content: str
    timestamp: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Session(BaseModel):
    """
    Typed model for user session data.
    Provides structured access to session attributes.
    """

    user_id: str
    current_profile_id: Optional[UUID] = None
    conversation_history: List[MessageTurn] = Field(default_factory=list)
    active_intent: Optional[str] = None
    session_metadata: Dict[str, Any] = Field(default_factory=dict)

    def set_active_intent(self, intent: Optional[str]) -> None:
        """
        Set the active intent for this session.

        Args:
            intent: The intent to set as active, or None to clear
        """
        self.active_intent = intent


class SessionManager:
    """
    Manages user sessions for conversational context.

    Currently implements in-memory storage with configurable limits.
    Future enhancements will include persistent storage (e.g., Redis).
    """

    def __init__(self):
        # Keyed by (user_id, channel_type)
        self.sessions: Dict[Tuple[str, Optional[str]], Session] = {}
        self.settings: SessionSettings = get_session_settings()
        self.conversation_dao = ConversationDAO()
        self.profile_dao = ProfileDAO()

    def _make_key(
        self, user_id: str, channel_type: Optional[str] = None
    ) -> Tuple[str, Optional[str]]:
        """
        Build a composite key for session storage.
        If channel_type is None, use a global namespace for the user.
        """
        return (user_id, channel_type)

    def get_or_create_session(
        self, user_id: str, channel_type: Optional[str] = None
    ) -> Session:
        """
        Get an existing session or create a new one if it doesn't exist.
        If creating new, hydrates from conversation history in the database.

        Args:
            user_id (str): Unique identifier for the user
            channel_type (Optional[str]): The channel type for fetching conversation history

        Returns:
            Session: The user's session data
        """
        key = self._make_key(user_id, channel_type)
        if key in self.sessions:
            return self.sessions[key]

        # Create new session and hydrate from DB
        try:
            # Try to get user profiles and use the first one as default
            default_profile_id = None
            try:
                profile = self.profile_dao.get_default_profile_for_user(user_id)
                if profile:
                    default_profile_id = profile.profile_id
                    logger.info(
                        f"Found default profile {default_profile_id} for user {user_id}"
                    )
            except Exception as e:
                logger.warning(f"Failed to get profiles for user {user_id}: {e}")

            # Create basic session
            session = Session(
                user_id=user_id,
                current_profile_id=default_profile_id,
                conversation_history=[],
                active_intent=None,
                session_metadata={},
            )

            # Hydrate conversation history if channel_type is provided
            if channel_type:
                try:
                    history = self.conversation_dao.get_conversation_history(
                        user_id=user_id,
                        channel=ChannelType(channel_type),
                        limit=self.settings.max_turns_in_cache,
                    )

                    # Convert to MessageTurn objects
                    for msg in history:
                        # Map message type to role
                        role = (
                            "user"
                            if msg.message_type.value.startswith("incoming")
                            else "assistant"
                        )

                        # Create MessageTurn
                        turn = MessageTurn(
                            role=role,
                            content=msg.content,
                            timestamp=msg.created_at.isoformat(),
                            metadata=msg.additional_info,
                        )
                        session.conversation_history.append(turn)

                    # Sort by timestamp (oldest first)
                    session.conversation_history.sort(
                        key=lambda x: datetime.datetime.fromisoformat(x.timestamp)
                    )

                    logger.info(
                        f"Hydrated session for user {user_id} with {len(session.conversation_history)} messages"
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to hydrate conversation history for user {user_id}: {e}"
                    )

            # Trim if needed
            self._trim_session(session)

            # Store in cache
            self.sessions[key] = session
            return session

        except Exception as e:
            logger.error(f"Error creating session for user {user_id}: {e}")
            # Fallback to empty session
            session = Session(user_id=user_id)
            self.sessions[key] = session
            return session

    def update_session(
        self,
        user_id: str,
        new_turn: MessageTurn,
        active_intent: Optional[str] = None,
        metadata_updates: Optional[Dict] = None,
        channel_type: Optional[str] = None,
    ) -> None:
        """
        Update a session with a new conversation turn and optional metadata.

        Args:
            user_id (str): Unique identifier for the user
            new_turn (MessageTurn): New conversation turn
            active_intent (Optional[str]): Current active intent, if any
            metadata_updates (Optional[Dict]): Updates to session metadata
        """
        session = self.get_or_create_session(user_id, channel_type)

        # Add timestamp if not present
        if not new_turn.timestamp:
            new_turn.timestamp = datetime.datetime.now().isoformat()

        # Only add if not a duplicate of the most recent message
        if (
            not session.conversation_history
            or session.conversation_history[-1].content != new_turn.content
            or session.conversation_history[-1].role != new_turn.role
        ):
            session.conversation_history.append(new_turn)

        if active_intent is not None:
            session.active_intent = active_intent

        if metadata_updates:
            session.session_metadata.update(metadata_updates)

        self._trim_session(session)

    def _trim_session(self, session: Session) -> None:
        """
        Trim session history if it exceeds configured limits.

        Args:
            session (Session): Session to trim
        """
        history = session.conversation_history
        total_size = sum(len(turn.content) for turn in history)

        while (
            len(history) > self.settings.max_turns_in_cache
            or total_size > self.settings.max_cache_size
        ) and history:
            removed = history.pop(0)  # Remove oldest
            total_size -= len(removed.content)

    def clear_session(self, user_id: str, channel_type: Optional[str] = None) -> None:
        """
        Clear a user's session from memory.

        Args:
            user_id (str): Unique identifier for the user
        """
        if channel_type is not None:
            key = self._make_key(user_id, channel_type)
            if key in self.sessions:
                del self.sessions[key]
            return

        # If no channel specified, clear all sessions for the user
        to_delete = [k for k in self.sessions.keys() if k[0] == user_id]
        for k in to_delete:
            del self.sessions[k]

    def get_recent_history(
        self, user_id: str, limit: int = 5, channel_type: Optional[str] = None
    ) -> List[MessageTurn]:
        """
        Get the most recent conversation turns for a user.

        Args:
            user_id (str): Unique identifier for the user
            limit (int): Maximum number of turns to return

        Returns:
            List[MessageTurn]: List of recent conversation turns
        """
        session = self.get_or_create_session(user_id, channel_type)
        history = session.conversation_history
        return history[-limit:] if history else []

    def set_active_intent(
        self,
        user_id: str,
        active_intent: Optional[str],
        channel_type: Optional[str] = None,
    ) -> None:
        """
        Set the active intent for a user's session without modifying message history.

        Args:
            user_id (str): Unique identifier for the user
            active_intent (Optional[str]): Intent name to set, or None to clear
        """
        session = self.get_or_create_session(user_id, channel_type)
        session.active_intent = active_intent
