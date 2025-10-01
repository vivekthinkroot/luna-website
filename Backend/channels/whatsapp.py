"""
WhatsApp channel handler interface for Luna.
Responsible for processing WhatsApp webhook messages and sending responses.
"""

import hashlib
import hmac
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import httpx
from pydantic import BaseModel, Field

from channels.base import ChannelHandler
from config.settings import get_settings
from utils.logger import logger
from utils.models import (
    CanonicalRequestMessage,
    CanonicalResponseMessage,
    ContentType,
    SelectedQuickReply,
)

settings = get_settings()


class WhatsAppProfile(BaseModel):
    name: str


class WhatsAppContact(BaseModel):
    profile: WhatsAppProfile
    wa_id: str


class WhatsAppText(BaseModel):
    body: str


class WhatsAppAudio(BaseModel):
    id: str
    mime_type: Optional[str] = None
    sha256: Optional[str] = None
    file_size: Optional[int] = None
    voice: Optional[bool] = None


class WhatsAppImage(BaseModel):
    id: str
    mime_type: Optional[str] = None
    sha256: Optional[str] = None
    caption: Optional[str] = None


class WhatsAppVideo(BaseModel):
    id: str
    mime_type: Optional[str] = None
    sha256: Optional[str] = None
    caption: Optional[str] = None


class WhatsAppDocument(BaseModel):
    id: str
    filename: Optional[str] = None
    mime_type: Optional[str] = None
    sha256: Optional[str] = None
    caption: Optional[str] = None


class WhatsAppMessage(BaseModel):
    id: str
    from_: str = Field(..., alias="from")
    timestamp: str
    type: str
    text: Optional[WhatsAppText] = None
    audio: Optional[WhatsAppAudio] = None
    voice: Optional[WhatsAppAudio] = None
    image: Optional[WhatsAppImage] = None
    video: Optional[WhatsAppVideo] = None
    document: Optional[WhatsAppDocument] = None
    interactive: Optional[Dict[str, Any]] = None

    class Config:
        populate_by_name = True

    @property
    def timestamp_as_datetime(self) -> datetime:
        """Returns the message timestamp as a datetime object (UTC)."""
        return datetime.fromtimestamp(int(self.timestamp), tz=timezone.utc)


class WhatsAppStatus(BaseModel):
    id: str
    status: str  # "sent", "delivered", "read", "failed"
    timestamp: str
    recipient_id: str
    conversation: Optional[Dict[str, Any]] = None
    pricing: Optional[Dict[str, Any]] = None


class WhatsAppValue(BaseModel):
    messaging_product: str
    metadata: Dict[str, Any]
    contacts: Optional[list[WhatsAppContact]] = None
    messages: Optional[list[WhatsAppMessage]] = None
    statuses: Optional[list[WhatsAppStatus]] = None


class WhatsAppChange(BaseModel):
    value: WhatsAppValue
    field: str


class WhatsAppEntry(BaseModel):
    id: str
    changes: list[WhatsAppChange]


class WhatsAppWebhookPayload(BaseModel):
    object: str
    entry: list[WhatsAppEntry]


class WhatsAppWebhookHandler(ChannelHandler):
    def __init__(self):
        self.settings = get_settings().whatsapp
        self.access_token = self.settings.access_token
        self.phone_number_id = self.settings.phone_number_id
        self.webhook_verify_token = self.settings.webhook_verify_token
        self.webhook_secret = self.settings.webhook_secret
        self.max_message_length = self.settings.max_message_length
        self.base_url = (
            f"https://graph.facebook.com/v18.0/{self.phone_number_id}/messages"
        )
        self.media_url = "https://graph.facebook.com/v18.0"

    def validate_webhook(self, headers: Dict[str, str], body: str) -> bool:
        """Validate WhatsApp webhook signature using X-Hub-Signature-256 header"""
        try:
            if not self.webhook_secret or self.webhook_secret.startswith("your_"):
                logger.debug(
                    "⚠️ WhatsApp webhook secret not configured - skipping signature verification"
                )
                return True

            signature = None
            for k, v in headers.items():
                if k.lower() == "x-hub-signature-256":
                    signature = v
                    break

            if not signature or signature.strip() == "":
                logger.debug(
                    "⚠️ No WhatsApp signature provided - skipping verification (testing mode)"
                )
                return True

            if signature.startswith("sha256="):
                signature = signature[7:]

            expected_signature = hmac.new(
                self.webhook_secret.encode(), body.encode(), hashlib.sha256
            ).hexdigest()

            is_valid = hmac.compare_digest(expected_signature, signature)
            if not is_valid:
                logger.error("❌ WhatsApp webhook signature verification failed")
            else:
                logger.debug("✅ WhatsApp webhook signature verified")

            return is_valid

        except Exception as e:
            logger.error(f"❌ Error verifying WhatsApp webhook signature: {str(e)}")
            return True

    async def parse_incoming_message(
        self, webhook_data: Dict[str, Any]
    ) -> Optional[CanonicalRequestMessage]:
        """Parse WhatsApp webhook message and convert to canonical format"""
        try:
            try:
                webhook_payload = WhatsAppWebhookPayload(**webhook_data)
            except Exception as e:
                logger.warning(f"Failed to parse webhook payload: {e}, ignoring")
                return None

            if not webhook_payload.entry or not webhook_payload.entry[0].changes:
                logger.warning("Received webhook with no changes, ignoring")
                return None

            change = webhook_payload.entry[0].changes[0]
            change_value = change.value

            # Check if this is a status update (delivery receipt) rather than a message
            if change_value.statuses and len(change_value.statuses) > 0:
                # This is a status update - log and return None to indicate no processing needed
                logger.debug(
                    f"Received WhatsApp status update: {change_value.statuses[0].status}"
                )
                return None

            if not change_value.messages or len(change_value.messages) == 0:
                # This is likely a status update, not a message - ignore it gracefully
                logger.debug("Received WhatsApp webhook with no messages, ignoring")
                return None

            message = change_value.messages[0]

            user_id = None
            channel_user_id = message.from_
            channel_type = "whatsapp"
            timestamp = message.timestamp_as_datetime

            metadata = {
                "idempotency_key": message.id,
                "whatsapp_message_id": message.id,
                "message_type": message.type,
                "phone_number_id": self.phone_number_id,
                "contact": {},
                "audio": {},
                "voice": {},
                "image": {},
                "video": {},
                "document": {},
            }

            if change_value.contacts:
                try:
                    contact = change_value.contacts[0]
                    metadata["contact"] = {
                        "wa_id": getattr(contact, 'wa_id', ''),
                        "profile_name": getattr(contact.profile, 'name', '') if hasattr(contact, 'profile') else '',
                    }
                except Exception as e:
                    logger.warning(f"Failed to parse contact info: {e}, continuing without contact data")
                    metadata["contact"] = {}

            binary_content = None
            content_type = ContentType.TEXT
            content = ""

            # Interactive button reply
            if message.type == "interactive" and message.interactive:
                # Button reply payload shape: {type: "button_reply", button_reply: {id, title}}
                button_reply = (
                    message.interactive.get("button_reply")
                    if isinstance(message.interactive, dict)
                    else None
                )
                if not button_reply:
                    logger.warning("Received unsupported interactive payload, ignoring")
                    return None
                content_type = ContentType.TEXT
                content = button_reply.get("title", "")
                selected_reply = SelectedQuickReply(
                    id=str(button_reply.get("id", "")),
                    text=button_reply.get("title"),
                    payload=None,
                    source_message_id=message.id,
                )
                metadata["interactive"] = message.interactive
                return CanonicalRequestMessage(
                    user_id=user_id,
                    channel_type=channel_type,
                    channel_user_id=channel_user_id,
                    content_type=content_type,
                    content=content,
                    metadata=metadata,
                    timestamp=timestamp,
                    binary_content=None,
                    selected_reply=selected_reply,
                )

            if message.type == "text" and message.text:
                content_type = ContentType.TEXT
                content = message.text.body

            elif message.type == "audio" and message.audio:
                content_type = ContentType.VOICE
                content = message.audio.id
                metadata["audio"] = {
                    "mime_type": message.audio.mime_type,
                    "file_size": message.audio.file_size,
                    "voice": message.audio.voice,
                }
                binary_content = await self._download_media(message.audio.id)

            elif message.type == "voice" and message.voice:
                content_type = ContentType.VOICE
                content = message.voice.id
                metadata["voice"] = {
                    "mime_type": message.voice.mime_type,
                    "file_size": message.voice.file_size,
                }
                binary_content = await self._download_media(message.voice.id)

            elif message.type == "image" and message.image:
                content_type = ContentType.MEDIA
                content = message.image.id
                metadata["image"] = {
                    "mime_type": message.image.mime_type,
                    "caption": message.image.caption,
                }
                binary_content = await self._download_media(message.image.id)

            elif message.type == "video" and message.video:
                content_type = ContentType.MEDIA
                content = message.video.id
                metadata["video"] = {
                    "mime_type": message.video.mime_type,
                    "caption": message.video.caption,
                }
                binary_content = await self._download_media(message.video.id)

            elif message.type == "document" and message.document:
                content_type = ContentType.DOCUMENT
                content = message.document.id
                metadata["document"] = {
                    "filename": message.document.filename,
                    "mime_type": message.document.mime_type,
                    "caption": message.document.caption,
                }
                binary_content = await self._download_media(message.document.id)

            elif message.type == "reaction":
                # Ignore reaction messages gracefully - they don't need processing
                logger.debug(f"Ignoring WhatsApp reaction message: {message.type}")
                return None
            elif message.type in ["sticker", "location", "contacts", "order", "system"]:
                # Ignore other message types that don't need processing
                logger.debug(f"Ignoring WhatsApp {message.type} message")
                return None
            else:
                # Log unsupported message types but don't fail - just ignore them
                logger.info(f"Ignoring unsupported WhatsApp message type: {message.type}")
                return None

            return CanonicalRequestMessage(
                user_id=user_id,
                channel_type=channel_type,
                channel_user_id=channel_user_id,
                content_type=content_type,
                content=content,
                metadata=metadata,
                timestamp=timestamp,
                binary_content=binary_content,
            )

        except Exception as e:
            logger.error(f"❌ Error parsing WhatsApp message: {str(e)}")
            # Instead of failing, return None to gracefully ignore problematic messages
            # This prevents WhatsApp from retrying failed webhooks
            return None

    async def send_message(
        self, channel_user_id: str, response: CanonicalResponseMessage
    ) -> bool:
        """Send message back to user through WhatsApp API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            }

            if response.content_type == ContentType.TEXT:
                # If reply options are present, send an interactive message with buttons
                if response.reply_options:
                    opts = list(response.reply_options or [])
                    buttons = [
                        {"type": "reply", "reply": {"id": opt.id, "title": opt.text}}
                        for opt in opts
                    ][
                        :3
                    ]  # WhatsApp allows up to 3 buttons
                    payload = {
                        "messaging_product": "whatsapp",
                        "to": channel_user_id,
                        "type": "interactive",
                        "interactive": {
                            "type": "button",
                            "body": {
                                "text": response.content[: self.max_message_length]
                            },
                            "action": {"buttons": buttons},
                        },
                    }
                else:
                    payload = {
                        "messaging_product": "whatsapp",
                        "to": channel_user_id,
                        "type": "text",
                        "text": {"body": response.content[: self.max_message_length]},
                    }

                async with httpx.AsyncClient() as client:
                    api_response = await client.post(
                        self.base_url, headers=headers, json=payload, timeout=30
                    )

                    if api_response.status_code == 200:
                        logger.info(
                            f"✅ WhatsApp text message sent successfully to {channel_user_id}"
                        )
                        return True
                    else:
                        logger.error(
                            f"❌ Failed to send WhatsApp text message: {api_response.status_code} - {api_response.text}"
                        )
                        return False

            elif response.content_type == ContentType.VOICE and response.binary_content:
                # Extract filename and MIME type from metadata, with defaults
                filename = (
                    response.metadata.get("filename", "voice.ogg")
                    if response.metadata
                    else "voice.ogg"
                )
                mime_type = (
                    response.metadata.get("mime_type", "audio/ogg")
                    if response.metadata
                    else "audio/ogg"
                )

                # Ensure proper file extension for voice files
                if mime_type == "audio/ogg" and not filename.lower().endswith(".ogg"):
                    filename = f"{filename}.ogg"
                elif mime_type == "audio/mp3" and not filename.lower().endswith(".mp3"):
                    filename = f"{filename}.mp3"
                elif mime_type == "audio/wav" and not filename.lower().endswith(".wav"):
                    filename = f"{filename}.wav"

                media_id = await self._upload_media(
                    response.binary_content, mime_type, filename
                )
                if not media_id:
                    return False

                payload = {
                    "messaging_product": "whatsapp",
                    "to": channel_user_id,
                    "type": "audio",
                    "audio": {"id": media_id},
                }

                async with httpx.AsyncClient() as client:
                    api_response = await client.post(
                        self.base_url, headers=headers, json=payload, timeout=30
                    )

                    if api_response.status_code == 200:
                        logger.info(
                            f"✅ WhatsApp voice message sent successfully to {channel_user_id}"
                        )
                        return True
                    else:
                        logger.error(
                            f"❌ Failed to send WhatsApp voice message: {api_response.status_code} - {api_response.text}"
                        )
                        return False

            elif (
                response.content_type == ContentType.DOCUMENT
                and response.binary_content
            ):
                # Extract filename and MIME type from metadata, with defaults
                filename = (
                    response.metadata.get("filename", "document.pdf")
                    if response.metadata
                    else "document.pdf"
                )
                mime_type = (
                    response.metadata.get("mime_type", "application/pdf")
                    if response.metadata
                    else "application/pdf"
                )

                # Ensure proper file extension for PDF files
                if mime_type == "application/pdf" and not filename.lower().endswith(
                    ".pdf"
                ):
                    filename = f"{filename}.pdf"

                # Upload document to WhatsApp
                media_id = await self._upload_media(
                    response.binary_content, mime_type, filename
                )
                if not media_id:
                    return False

                # Prepare document message payload
                document_payload = {"id": media_id, "filename": filename}

                # Add caption if provided in metadata
                if response.metadata and response.metadata.get("caption"):
                    document_payload["caption"] = response.metadata["caption"]
                elif response.content:
                    # Use main content as caption if available
                    document_payload["caption"] = response.content[
                        :1024
                    ]  # WhatsApp caption limit

                payload = {
                    "messaging_product": "whatsapp",
                    "to": channel_user_id,
                    "type": "document",
                    "document": document_payload,
                }

                async with httpx.AsyncClient() as client:
                    api_response = await client.post(
                        self.base_url, headers=headers, json=payload, timeout=30
                    )

                    if api_response.status_code == 200:
                        logger.info(
                            f"✅ WhatsApp PDF document sent successfully to {channel_user_id} (filename={filename})"
                        )
                        return True
                    else:
                        logger.error(
                            f"❌ Failed to send WhatsApp PDF document: {api_response.status_code} - {api_response.text}"
                        )
                        return False

            else:
                logger.warning(
                    f"⚠️ Unsupported WhatsApp response type: {response.content_type}"
                )
                return False

        except Exception as e:
            logger.error(f"❌ Exception sending WhatsApp message: {str(e)}")
            return False

    async def _download_media(self, media_id: str) -> Optional[bytes]:
        """Download media file from WhatsApp"""
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}

            async with httpx.AsyncClient() as client:
                media_response = await client.get(
                    f"{self.media_url}/{media_id}", headers=headers, timeout=30
                )

                if media_response.status_code != 200:
                    logger.error(
                        f"❌ Failed to get WhatsApp media URL: {media_response.status_code} - {media_response.text}"
                    )
                    return None

                media_data = media_response.json()
                download_url = media_data.get("url")

                if not download_url:
                    logger.error("❌ No download URL in WhatsApp media response")
                    return None

                download_response = await client.get(
                    download_url, headers=headers, timeout=30
                )

                if download_response.status_code == 200:
                    logger.info(
                        f"✅ WhatsApp media downloaded successfully: {media_id}"
                    )
                    return download_response.content
                else:
                    logger.error(
                        f"❌ Failed to download WhatsApp media: {download_response.status_code}"
                    )
                    return None

        except Exception as e:
            logger.error(f"❌ Exception downloading WhatsApp media: {str(e)}")
            return None

    async def _upload_media(
        self, file_content: bytes, mime_type: str, filename: str
    ) -> Optional[str]:
        """Upload media file to WhatsApp and return media ID"""
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}

            files = {
                "file": (filename, file_content, mime_type),
                "messaging_product": (None, "whatsapp"),
                "type": (None, mime_type.split("/")[0]),
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.media_url}/{self.phone_number_id}/media",
                    headers=headers,
                    files=files,
                    timeout=60,
                )

                if response.status_code == 200:
                    response_data = response.json()
                    media_id = response_data.get("id")
                    if media_id:
                        logger.info(
                            f"✅ WhatsApp media uploaded successfully: {media_id}"
                        )
                        return media_id
                    else:
                        logger.error("❌ No media ID in WhatsApp upload response")
                        return None
                else:
                    logger.error(
                        f"❌ Failed to upload WhatsApp media: {response.status_code} - {response.text}"
                    )
                    return None

        except Exception as e:
            logger.error(f"❌ Exception uploading WhatsApp media: {str(e)}")
            return None