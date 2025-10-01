"""
Telegram channel handler interface for Luna.
Responsible for processing Telegram webhook messages and sending responses.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

import httpx
from fastapi import HTTPException
from pydantic import BaseModel, Field

from channels.base import ChannelHandler
from config.settings import get_settings
from utils.logger import logger
from utils.models import CanonicalRequestMessage, CanonicalResponseMessage, ContentType

settings = get_settings()


class TelegramUser(BaseModel):
    id: int
    is_bot: bool
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = None


class TelegramChat(BaseModel):
    id: int
    type: str
    title: Optional[str] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class TelegramVoice(BaseModel):
    file_id: str
    duration: int
    mime_type: Optional[str] = None
    file_size: Optional[int] = None


class TelegramMessage(BaseModel):
    message_id: int
    from_: TelegramUser = Field(..., alias="from")
    chat: TelegramChat
    date: int
    text: Optional[str] = None
    voice: Optional[TelegramVoice] = None

    class Config:
        allow_population_by_field_name = True

    @property
    def date_as_datetime(self) -> datetime:
        """Returns the message date as a datetime object (UTC)."""
        return datetime.fromtimestamp(self.date, tz=timezone.utc)


class TelegramCallbackQuery(BaseModel):
    id: str
    from_: TelegramUser = Field(..., alias="from")
    message: Optional[TelegramMessage] = None
    data: Optional[str] = None


class TelegramUpdate(BaseModel):
    update_id: int
    message: Optional[TelegramMessage] = None
    callback_query: Optional[TelegramCallbackQuery] = None


class TelegramWebhookHandler(ChannelHandler):
    def __init__(self):
        self.settings = get_settings().telegram
        self.bot_token = self.settings.bot_token
        self.max_message_length = self.settings.max_message_length
        self.webhook_secret = self.settings.webhook_secret

    def validate_webhook(self, headers: Dict[str, str], body: str) -> bool:
        # Secret-based validation: X-Telegram-Bot-Api-Secret-Token header
        # Make header name case-insensitive
        secret = None
        for k, v in headers.items():
            if k.lower() == "x-telegram-bot-api-secret-token".lower():
                secret = v
                break
        if secret == self.webhook_secret:
            return True
        else:
            logger.info(
                f"Telegram webhook secret received: {secret}, expected: {self.webhook_secret}"
            )
        return False

    async def parse_incoming_message(
        self, webhook_data: Dict[str, Any]
    ) -> CanonicalRequestMessage:
        update = TelegramUpdate(**webhook_data)

        # Handle standard messages
        if not update.message:
            raise HTTPException(status_code=400, detail="No message in update")
        msg = update.message
        user_id = None  # To be resolved by user management
        channel_user_id = str(msg.from_.id)
        channel_type = "telegram"
        timestamp = msg.date_as_datetime
        metadata = {
            "telegram_message_id": msg.message_id,
            "chat_id": msg.chat.id,
            "from": msg.from_.model_dump(),
        }
        # Provide a stable idempotency key for retries
        metadata["idempotency_key"] = f"tg:{msg.chat.id}:{msg.message_id}"
        binary_content = None
        if msg.text:
            content_type = ContentType.TEXT
            content = msg.text
        elif msg.voice:
            content_type = ContentType.VOICE
            content = msg.voice.file_id
            metadata["voice"] = msg.voice.model_dump()
            # Fetch the actual voice file binary
            file_id = msg.voice.file_id
            file_path_url = f"https://api.telegram.org/bot{self.bot_token}/getFile"
            async with httpx.AsyncClient() as client:
                file_resp = await client.get(file_path_url, params={"file_id": file_id})
                file_resp.raise_for_status()
                file_path = file_resp.json()["result"]["file_path"]
                download_url = (
                    f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}"
                )
                voice_resp = await client.get(download_url)
                voice_resp.raise_for_status()
                binary_content = voice_resp.content
        else:
            raise HTTPException(status_code=400, detail="Unsupported message type")
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

    async def send_message(
        self, channel_user_id: str, response: CanonicalResponseMessage
    ) -> bool:
        # Handle text and voice responses
        if response.content_type == ContentType.TEXT:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                "chat_id": channel_user_id,
                "text": response.content,
                "parse_mode": response.metadata.get("parse_mode", "Markdown"),
                "disable_web_page_preview": True,
            }
            # Render quick reply options as ReplyKeyboardMarkup to avoid callback wait
            options = list(response.reply_options or [])
            if options:
                keyboard = [[{"text": option.text}] for option in options]
                payload["reply_markup"] = {
                    "keyboard": keyboard,
                    "resize_keyboard": True,
                    "one_time_keyboard": True,
                    "selective": True,
                }
            if len(payload["text"]) > self.max_message_length:
                payload["text"] = payload["text"][: self.max_message_length]
            async with httpx.AsyncClient() as client:
                r = await client.post(url, json=payload)
                return r.status_code == 200
        elif response.content_type == ContentType.VOICE and response.binary_content:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendVoice"
            data = {
                "chat_id": channel_user_id,
            }

            # Extract filename and MIME type from metadata, with defaults
            filename = response.metadata.get("filename", "voice.ogg")
            mime_type = response.metadata.get("mime_type", "audio/ogg")

            # Ensure proper file extension for voice files
            if mime_type == "audio/ogg" and not filename.lower().endswith(".ogg"):
                filename = f"{filename}.ogg"
            elif mime_type == "audio/mp3" and not filename.lower().endswith(".mp3"):
                filename = f"{filename}.mp3"
            elif mime_type == "audio/wav" and not filename.lower().endswith(".wav"):
                filename = f"{filename}.wav"

            files = {"voice": (filename, response.binary_content, mime_type)}
            async with httpx.AsyncClient() as client:
                r = await client.post(url, data=data, files=files)
                return r.status_code == 200
        elif response.content_type == ContentType.DOCUMENT and response.binary_content:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendDocument"

            # Extract filename and MIME type from metadata, with defaults
            filename = response.metadata.get("filename", "document.pdf")
            mime_type = response.metadata.get("mime_type", "application/pdf")

            # Ensure proper file extension for PDF files
            if mime_type == "application/pdf" and not filename.lower().endswith(".pdf"):
                filename = f"{filename}.pdf"

            data = {
                "chat_id": channel_user_id,
            }

            # Add caption if provided
            if response.content:
                data["caption"] = response.content
                # Respect Telegram's caption length limit (1024 characters)
                if len(data["caption"]) > 1024:
                    data["caption"] = data["caption"][:1021] + "..."

            files = {"document": (filename, response.binary_content, mime_type)}

            async with httpx.AsyncClient() as client:
                r = await client.post(url, data=data, files=files)
                return r.status_code == 200
        else:
            # Unsupported type
            return False


async def register_telegram_webhook() -> None:
    settings = get_settings()
    telegram_settings = settings.telegram
    bot_token = telegram_settings.bot_token
    webhook_base_url = telegram_settings.webhook_base_url
    webhook_path = getattr(telegram_settings, "webhook_path")
    webhook_secret = telegram_settings.webhook_secret

    # Skip webhook registration if Telegram is not configured
    if not bot_token or not webhook_base_url or not webhook_secret:
        logger.info(
            "Telegram webhook not fully configured, skipping webhook registration"
        )
        return

    # Ensure webhook_url ends with the correct path
    if not webhook_base_url.endswith(webhook_path):
        if webhook_base_url.endswith("/") and webhook_path.startswith("/"):
            webhook_full_url = webhook_base_url[:-1] + webhook_path
        elif not webhook_base_url.endswith("/") and not webhook_path.startswith("/"):
            webhook_full_url = webhook_base_url + "/" + webhook_path
        else:
            webhook_full_url = webhook_base_url + webhook_path
    else:
        webhook_full_url = webhook_base_url
    set_webhook_url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
    payload = {
        "url": webhook_full_url,
        "secret_token": webhook_secret,
        "max_connections": 40,
        # "allowed_updates": ["message", "callback_query"],
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        headers = {"Content-Type": "application/json"}
        resp = await client.post(set_webhook_url, json=payload, headers=headers)
        
        # Handle HTTP errors
        if resp.status_code != 200:
            error_msg = f"HTTP {resp.status_code} error registering Telegram webhook: {resp.text}"
            logger.error(error_msg)
            raise Exception(error_msg)
            
        # Check Telegram API response
        try:
            response_data = resp.json()
        except Exception as e:
            error_msg = f"Invalid JSON response from Telegram API: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
            
        if response_data.get("ok"):
            logger.info(
                f"Telegram webhook registered: {webhook_full_url}"
            )
        else:
            error_msg = f"Failed to register Telegram webhook: {response_data.get('description', 'Unknown error')}"
            logger.error(error_msg)
            raise Exception(error_msg)
