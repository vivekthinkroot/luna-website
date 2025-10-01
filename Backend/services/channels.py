"""
ChannelsService stub for Luna.
Responsible for platform-agnostic message processing and routing between channel handlers and core services.
"""

import asyncio
from collections import deque
from datetime import datetime, timezone
from typing import Optional

from channels.telegram import TelegramWebhookHandler
from channels.whatsapp import WhatsAppWebhookHandler
from dao.conversations import ConversationDAO
from dao.users import UserDAO
from data.models import ChannelType, MessageType
from services.router import LunaRouter
from utils.logger import get_logger
from utils.models import CanonicalRequestMessage, CanonicalResponseMessage, ContentType

# Initialize logger
logger = get_logger()


class ChannelsService:
    def __init__(self):
        self.user_dao = UserDAO()
        self.conversation_dao = ConversationDAO()
        self.channel_handlers = {
            "telegram": TelegramWebhookHandler(),
            "whatsapp": WhatsAppWebhookHandler(),
        }
        self.router = LunaRouter()  # Initialize the router
        # In-memory idempotency cache; consider Redis for multi-instance
        self._processed_keys: deque[str] = deque()
        self._processed_keys_set: set[str] = set()
        self._processed_keys_max: int = 2048

    def _is_duplicate(self, idempotency_key: str | None) -> bool:
        if not idempotency_key:
            return False
        if idempotency_key in self._processed_keys_set:
            return True
        if len(self._processed_keys) >= self._processed_keys_max:
            old = self._processed_keys.popleft()
            self._processed_keys_set.discard(old)
        self._processed_keys.append(idempotency_key)
        self._processed_keys_set.add(idempotency_key)
        return False

    async def enqueue_incoming_message(self, msg: CanonicalRequestMessage) -> None:
        """
        Non-blocking entrypoint: dedupe and schedule processing in background.
        """
        key = None
        try:
            key = (msg.metadata or {}).get("idempotency_key")
        except Exception:
            key = None
        if self._is_duplicate(key):
            logger.info(f"Duplicate message ignored (key={key})")
            return
        asyncio.create_task(self.process_incoming_message(msg))

    def save_incoming_message(self, user_id: str, msg: CanonicalRequestMessage):
        # Map canonical type to MessageType
        if msg.content_type == ContentType.TEXT:
            message_type = MessageType.INCOMING_TEXT
            content = msg.content
            additional_info = msg.metadata.copy() if msg.metadata else {}
        elif msg.content_type == ContentType.VOICE:
            message_type = MessageType.INCOMING_VOICE
            content = ""
            additional_info = msg.metadata.copy() if msg.metadata else {}
            if msg.content:
                additional_info["content"] = msg.content
            if msg.binary_content:
                additional_info["binary_content"] = (
                    True  # or store a reference if available
                )
        elif msg.content_type == ContentType.DOCUMENT:
            message_type = MessageType.INCOMING_DOCUMENT
            content = ""
            additional_info = msg.metadata.copy() if msg.metadata else {}
            if msg.content:
                additional_info["content"] = msg.content
            if msg.binary_content:
                additional_info["binary_content"] = True
        else:
            message_type = MessageType.INCOMING_MEDIA
            content = ""
            additional_info = msg.metadata.copy() if msg.metadata else {}
            if msg.content:
                additional_info["content"] = msg.content
            if msg.binary_content:
                additional_info["binary_content"] = True
        self.conversation_dao.save_message(
            user_id=user_id,
            channel=ChannelType(msg.channel_type),
            message_type=message_type,
            content=content,
            additional_info=additional_info,
        )

    def save_outgoing_message(self, user_id: str, msg: CanonicalResponseMessage):
        # Map canonical type to MessageType
        if msg.content_type == ContentType.TEXT:
            message_type = MessageType.OUTGOING_TEXT
            content = msg.content
            additional_info = msg.metadata.copy() if msg.metadata else {}
        elif msg.content_type == ContentType.VOICE:
            message_type = MessageType.OUTGOING_VOICE
            content = ""
            additional_info = msg.metadata.copy() if msg.metadata else {}
            if msg.content:
                additional_info["content"] = msg.content
            if msg.binary_content:
                additional_info["binary_content"] = True
        elif msg.content_type == ContentType.DOCUMENT:
            message_type = MessageType.OUTGOING_DOCUMENT
            content = ""
            additional_info = msg.metadata.copy() if msg.metadata else {}
            if msg.content:
                additional_info["content"] = msg.content
            if msg.binary_content:
                additional_info["binary_content"] = True
        else:
            message_type = MessageType.OUTGOING_MEDIA
            content = ""
            additional_info = msg.metadata.copy() if msg.metadata else {}
            if msg.content:
                additional_info["content"] = msg.content
            if msg.binary_content:
                additional_info["binary_content"] = True
        self.conversation_dao.save_message(
            user_id=user_id,
            channel=ChannelType(msg.channel_type),
            message_type=message_type,
            content=content,
            additional_info=additional_info,
        )

    async def send_message(
        self, user_id: str, response: CanonicalResponseMessage
    ) -> bool:
        """
        Generic method to send a message (for notifications, system messages, etc).
        Accepts a fully-formed CanonicalResponseMessage object.
        """
        # Persist and dispatch
        self.save_outgoing_message(user_id, response)
        handler = self.channel_handlers.get(response.channel_type)
        if not handler:
            logger.error(f"No handler registered for channel: {response.channel_type}")
            return False
        try:
            result = await handler.send_message(response.channel_user_id, response)
            content_preview = response.content[:30] if len(response.content) > 30 else response.content
            logger.info(
                f"Sent message to user {user_id} on {response.channel_type}: {content_preview}"
            )
            return result
        except Exception as e:
            logger.error(f"Failed to send message via {response.channel_type}: {e}")
            return False

    async def process_incoming_message(
        self, msg: CanonicalRequestMessage
    ) -> CanonicalResponseMessage:
        """
        Channel-agnostic processing of incoming messages.
        Handles user management and routes messages to the appropriate service via the router.
        """
        # User management: first check if user is already linked to this channel
        user = self.user_dao.get_user_by_channel(msg.channel_type, msg.channel_user_id)

        if not user:
            # User not linked to this channel, check if they exist by phone number (for WhatsApp)
            if msg.channel_type == ChannelType.WHATSAPP:
                # For WhatsApp, try to find user by phone number
                phone = msg.channel_user_id
                if not phone.startswith("+"):
                    phone = "+" + phone
                user = self.user_dao.get_user_by_phone(phone)

                if user:
                    # User exists, link them to this channel
                    self.user_dao.link_channel(
                        user_id=str(user.user_id),
                        channel_type=ChannelType(msg.channel_type),
                        user_identity=msg.channel_user_id,
                        is_primary=False,  # Don't override existing primary channel
                    )
                    logger.info(
                        f"Linked existing user {user.user_id} to WhatsApp channel"
                    )
                else:
                    # User doesn't exist, create new user with phone number
                    user = self.user_dao.create_user(phone=phone, email=None)
                    self.user_dao.link_channel(
                        user_id=str(user.user_id),
                        channel_type=ChannelType(msg.channel_type),
                        user_identity=msg.channel_user_id,
                        is_primary=True,  # First channel is primary
                    )
                    logger.info(
                        f"Created new WhatsApp user and linked channel: {user.user_id}"
                    )
            else:
                # For non-phone channels, create new user without phone
                user = self.user_dao.create_user(phone="", email=None)
                self.user_dao.link_channel(
                    user_id=str(user.user_id),
                    channel_type=ChannelType(msg.channel_type),
                    user_identity=msg.channel_user_id,
                    is_primary=True,  # First channel is primary
                )
                logger.info(
                    f"Created new user and linked channel: {user.user_id} <> {msg.channel_type}"
                )

        # Set the user_id in the message if it wasn't already set
        if not msg.user_id:
            msg.user_id = str(user.user_id)

        # Log incoming message (after user is resolved)
        self.save_incoming_message(str(user.user_id), msg)

        # Route the message through the router
        try:
            response = await self.router.route_to_service(msg)

            # Log outgoing message (already done in send_message)
            logger.debug(
                f"Router returned response for user {user.user_id}: {response.content[:50]}..."
            )

            # Dispatch the response to the appropriate channel handler
            await self.send_message(user_id=str(user.user_id), response=response)

            return response

        except Exception as e:
            logger.exception(f"Error routing message: {e}")
            # Fallback response
            response = msg.create_error_response()
            # Send the error message back to the user
            await self.send_message(user_id=str(user.user_id), response=response)
            return response
