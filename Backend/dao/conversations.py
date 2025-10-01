"""
ConversationDAO implementation for Luna.
Handles conversation history storage, retrieval, and statistics.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from data.db import get_session
from data.models import ChannelType, MessageType, TConversation


class Conversation(BaseModel):
    message_id: Optional[int] = None
    user_id: UUID
    channel: ChannelType
    message_type: MessageType
    content: str
    additional_info: Dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationDAO:
    """Data access object for conversation operations (synchronous)."""

    def save_message(
        self,
        user_id: str,
        channel: ChannelType,
        message_type: MessageType,
        content: str,
        additional_info: Dict[str, Any],
    ) -> Conversation:
        now = datetime.now(timezone.utc)
        user_id_uuid = user_id if isinstance(user_id, UUID) else UUID(str(user_id))
        message = TConversation(
            user_id=user_id_uuid,
            channel=channel,
            message_type=message_type,
            content=content,
            additional_info=additional_info,
            created_at=now,
        )
        with get_session() as db:
            db.add(message)
            try:
                db.commit()
                db.refresh(message)
                return Conversation.model_validate(message)
            except IntegrityError as e:
                db.rollback()
                raise ValueError(
                    "Conversation save failed or duplicate message_id"
                ) from e

    def get_conversation_history(
        self, user_id: str, channel: ChannelType, limit: int = 50
    ) -> List[Conversation]:
        """
        Get recent conversation history for a user and channel.
        Args:
            user_id (str): User ID.
            channel_id (str): Channel ID.
            limit (int): Max number of messages to return.
        Returns:
            List[Conversations]: List of conversation objects.
        """
        user_id_uuid = user_id if isinstance(user_id, UUID) else UUID(str(user_id))
        with get_session() as db:
            result = db.exec(
                select(TConversation)
                .where(
                    TConversation.user_id == user_id_uuid,
                    TConversation.channel == channel,
                )
                .order_by(desc(getattr(TConversation, "created_at")))
                .limit(limit)
            )
            return [Conversation.model_validate(m) for m in result.all()]

    def get_conversation_by_id(self, message_id: int) -> Optional[Conversation]:
        """
        Get specific conversation turn by message_id.
        Args:
            message_id (int): Message ID.
        Returns:
            Optional[Conversations]: Conversation object or None.
        """
        with get_session() as db:
            result = db.exec(
                select(TConversation).where(TConversation.message_id == message_id)
            )
            message = result.one_or_none()
            return Conversation.model_validate(message) if message else None

    def get_user_conversations(
        self, user_id: str, days: int = 30
    ) -> List[Conversation]:
        """
        Get user's conversations within a timeframe.
        Args:
            user_id (str): User ID.
            days (int): Number of days to look back.
        Returns:
            List[Conversations]: List of conversation objects.
        """
        user_id_uuid = user_id if isinstance(user_id, UUID) else UUID(str(user_id))
        since = datetime.now(timezone.utc) - timedelta(days=days)
        with get_session() as db:
            result = db.exec(
                select(TConversation)
                .where(
                    TConversation.user_id == user_id_uuid,
                    TConversation.created_at >= since,
                )
                .order_by(desc(getattr(TConversation, "created_at")))
            )
            return [Conversation.model_validate(m) for m in result.all()]

    def cleanup_old_conversations(self, days: int = 90) -> int:
        """
        Clean up old conversations.
        Args:
            days (int): Number of days to retain.
        Returns:
            int: Number of deleted records.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        with get_session() as db:
            to_delete = db.exec(
                select(TConversation).where(TConversation.created_at < cutoff)
            ).all()
            count = len(to_delete)
            for conv in to_delete:
                db.delete(conv)
            db.commit()
            return count
