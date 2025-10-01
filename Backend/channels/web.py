"""
Web channel handler interface for Luna.
Responsible for processing web-based webhook messages and sending responses.
"""

from typing import Any, Dict

from channels.base import ChannelHandler
from utils.models import CanonicalRequestMessage, CanonicalResponseMessage


class WebHandler(ChannelHandler):
    """Web channel handler implementation."""

    async def parse_incoming_message(
        self, webhook_data: Dict[str, Any]
    ) -> CanonicalRequestMessage:
        """
        Parse incoming message and convert to canonical format.
        Args:
            webhook_data (Dict[str, Any]): Incoming webhook payload from Web.
        Returns:
            CanonicalRequestMessage: Canonical message format.
        """
        # TODO: Implement Web-specific message parsing
        raise NotImplementedError("Web message parsing not yet implemented")

    async def send_message(
        self, channel_user_id: str, response: CanonicalResponseMessage
    ) -> bool:
        """
        Send message back to user through Web.
        Args:
            channel_user_id (str): Channel-specific user ID.
            response (CanonicalResponseMessage): Response payload.
        Returns:
            bool: True if sent successfully, False otherwise.
        """
        # TODO: Implement Web-specific message sending
        raise NotImplementedError("Web message sending not yet implemented")

    def validate_webhook(self, headers: Dict[str, str], body: str) -> bool:
        """
        Validate webhook authenticity.
        Args:
            headers (Dict[str, str]): Webhook request headers.
            body (str): Raw request body.
        Returns:
            bool: True if valid, False otherwise.
        """
        # TODO: Implement Web-specific webhook validation
        raise NotImplementedError("Web webhook validation not yet implemented")
