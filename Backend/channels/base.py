"""
Base channel handler interface for Luna.
Defines the common interface that all channel handlers must implement.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict

from utils.models import CanonicalRequestMessage, CanonicalResponseMessage


class ChannelHandler(ABC):
    """Abstract base class for all channel handlers."""

    @abstractmethod
    async def parse_incoming_message(
        self, webhook_data: Dict[str, Any]
    ) -> CanonicalRequestMessage:
        """
        Parse incoming message and convert to canonical format.
        Args:
            webhook_data (Dict[str, Any]): Incoming webhook payload from the channel.
        Returns:
            CanonicalRequestMessage: Canonical message format.
        """
        pass

    @abstractmethod
    async def send_message(
        self, channel_user_id: str, response: CanonicalResponseMessage
    ) -> bool:
        """
        Send message back to user through the channel.
        Args:
            channel_user_id (str): Channel-specific user ID.
            response (CanonicalResponseMessage): Response payload.
        Returns:
            bool: True if sent successfully, False otherwise.
        """
        pass

    @abstractmethod
    def validate_webhook(self, headers: Dict[str, str], body: str) -> bool:
        """
        Validate webhook authenticity.
        Args:
            headers (Dict[str, str]): Webhook request headers.
            body (str): Raw request body.
        Returns:
            bool: True if valid, False otherwise.
        """
        pass
