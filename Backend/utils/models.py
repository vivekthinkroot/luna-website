from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class IntentType(str, Enum):
    """Enumeration of all available intent types to prevent typos and ensure consistency."""

    GENERATE_KUNDLI = "generate_kundli"
    PROFILE_QNA = "profile_qna"
    MAIN_MENU = "main_menu"
    UNKNOWN = "unknown"

    # Future intents can be added here following the same pattern
    # QUERY_KUNDLI = "query_kundli"
    # SUBSCRIBE_PREDICTIONS = "subscribe_predictions"


class ContentType(Enum):
    TEXT = "text"
    VOICE = "voice"
    MEDIA = "media"
    DOCUMENT = "document"


class QuickReplyOption(BaseModel):
    """Definition of a quick-reply option rendered to the user."""

    id: str
    text: str
    payload: Optional[Dict[str, Any]] = None

    @classmethod
    def build(
        cls, workflow_id: str, action: str, text: str, suffix: str = ""
    ) -> "QuickReplyOption":
        """Build a quick reply option with standardized ID format: workflow_id__action__suffix"""
        parts = [workflow_id, action]
        if suffix:
            parts.append(suffix)

        return cls(id="__".join(parts), text=text)


class SelectedQuickReply(BaseModel):
    """Structured capture when a user selects a quick-reply option."""

    id: str
    text: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    source_message_id: Optional[str] = None

    def get_workflow_id(self) -> Optional[str]:
        """Extract workflow ID from quick reply ID format: workflow_id__action__suffix"""
        if not self.id:
            return None
        parts = self.id.split("__")
        return parts[0] if len(parts) > 0 else None

    def get_action(self) -> Optional[str]:
        """Extract action from quick reply ID format: workflow_id__action__suffix"""
        if not self.id:
            return None
        parts = self.id.split("__")
        return parts[1] if len(parts) > 1 else None

    def get_suffix(self) -> Optional[str]:
        """Extract suffix from quick reply ID format: workflow_id__action__suffix"""
        if not self.id:
            return None
        parts = self.id.split("__")
        return parts[2] if len(parts) > 2 else None

    def has_valid_format(self) -> bool:
        """Check if quick reply ID follows expected format"""
        return bool(self.id and "__" in self.id and len(self.id.split("__")) >= 2)


class CanonicalRequestMessage(BaseModel):
    """
    Channel-agnostic internal message format for incoming messages.
    Includes optional binary_content for voice or other binary payloads.
    """

    user_id: Optional[str]  # Internal user ID (to be resolved)
    channel_type: str  # e.g., "telegram", "whatsapp"
    channel_user_id: str  # Platform-specific user ID
    content_type: ContentType  # text, voice, media, document
    content: str  # Text content or file reference
    metadata: Dict[str, Any]
    timestamp: datetime
    binary_content: Optional[bytes] = None
    selected_reply: Optional[SelectedQuickReply] = None

    def create_response(
        self,
        content: str,
        content_type: ContentType = ContentType.TEXT,
        metadata: Optional[Dict[str, Any]] = None,
        binary_content: Optional[bytes] = None,
        reply_options: Optional[List[QuickReplyOption]] = None,
        timestamp: Optional[datetime] = None,
    ) -> "CanonicalResponseMessage":
        """
        Create a response message with common fields copied from this request.

        Args:
            content: The response content text
            content_type: Content type for the response (defaults to TEXT)
            metadata: Response metadata (defaults to empty dict)
            binary_content: Optional binary content for voice/media responses
            reply_options: Optional quick reply options for the user
            timestamp: Response timestamp (defaults to current UTC time)

        Returns:
            CanonicalResponseMessage: A new response message with request fields copied
        """
        return CanonicalResponseMessage(
            user_id=self.user_id,
            channel_type=self.channel_type,
            channel_user_id=self.channel_user_id,
            content_type=content_type,
            content=content,
            metadata=metadata or {},
            timestamp=timestamp or datetime.now(timezone.utc),
            binary_content=binary_content,
            reply_options=reply_options,
        )

    def create_text_response(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        reply_options: Optional[List[QuickReplyOption]] = None,
    ) -> "CanonicalResponseMessage":
        """
        Create a simple text response message.

        Args:
            content: The response text content
            metadata: Response metadata (defaults to empty dict)
            reply_options: Optional quick reply options for the user

        Returns:
            CanonicalResponseMessage: A new text response message
        """
        return self.create_response(
            content=content,
            content_type=ContentType.TEXT,
            metadata=metadata,
            reply_options=reply_options,
        )

    def create_voice_response(
        self,
        content: str,
        binary_content: bytes,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "CanonicalResponseMessage":
        """
        Create a voice response message.

        Args:
            content: Text description or transcript of the voice content
            binary_content: The binary audio data
            metadata: Response metadata (defaults to empty dict)

        Returns:
            CanonicalResponseMessage: A new voice response message
        """
        return self.create_response(
            content=content,
            content_type=ContentType.VOICE,
            binary_content=binary_content,
            metadata=metadata,
        )

    def create_error_response(
        self,
        error_message: str = "Sorry, I encountered an error processing your request. Please try again.",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "CanonicalResponseMessage":
        """
        Create a standardized error response message.

        Args:
            error_message: The error message to display to the user
            metadata: Response metadata (defaults to empty dict)

        Returns:
            CanonicalResponseMessage: A new error response message
        """
        return self.create_text_response(
            content=error_message,
            metadata=metadata,
        )


class CanonicalResponseMessage(BaseModel):
    """
    Channel-agnostic internal message format for outgoing responses.
    Includes optional binary_content for voice or other binary payloads.
    """

    user_id: Optional[str]  # Internal user ID (to be resolved)
    channel_type: str  # e.g., "telegram", "whatsapp"
    channel_user_id: str  # Platform-specific user ID
    content_type: ContentType  # text, voice, media, document
    content: str  # Text content or file reference
    metadata: Dict[str, Any]
    timestamp: datetime
    binary_content: Optional[bytes] = None
    reply_options: Optional[List[QuickReplyOption]] = None

    def add_metadata(self, key: str, value: Any) -> "CanonicalResponseMessage":
        """
        Add a key-value pair to the metadata dictionary.

        Args:
            key: The metadata key
            value: The metadata value

        Returns:
            CanonicalResponseMessage: Self for method chaining
        """
        self.metadata[key] = value
        return self

    def update_metadata(
        self, metadata_dict: Dict[str, Any]
    ) -> "CanonicalResponseMessage":
        """
        Update the metadata dictionary with multiple key-value pairs.

        Args:
            metadata_dict: Dictionary of metadata to add/update

        Returns:
            CanonicalResponseMessage: Self for method chaining
        """
        self.metadata.update(metadata_dict)
        return self
