import os
from datetime import datetime, timezone
from typing import List

import pytest

from channels.telegram import TelegramWebhookHandler
from channels.whatsapp import WhatsAppWebhookHandler
from config.settings import get_settings
from utils.models import CanonicalResponseMessage, ContentType, QuickReplyOption

# Replace these placeholders before running the tests
TELEGRAM_TEST_CHAT_ID = "1363094917"
WHATSAPP_TEST_USER_ID = "REPLACE_919611104285"


def _build_quick_reply_response(
    channel_type: str, channel_user_id: str
) -> CanonicalResponseMessage:
    reply_options: List[QuickReplyOption] = [
        QuickReplyOption(id="qr_confirm", text="Confirm"),
        QuickReplyOption(id="qr_edit", text="Edit"),
    ]
    return CanonicalResponseMessage(
        user_id="test_user_quick_replies",
        channel_type=channel_type,
        channel_user_id=channel_user_id,
        content_type=ContentType.TEXT,
        content="Choose an option:",
        metadata={},
        timestamp=datetime.now(tz=timezone.utc),
        reply_options=reply_options,
    )


@pytest.mark.asyncio
async def test_telegram_send_quick_replies():
    settings = get_settings().telegram
    if not settings.bot_token:
        pytest.skip("Telegram bot token not configured; skipping send test")
    if TELEGRAM_TEST_CHAT_ID.startswith("REPLACE_"):
        pytest.skip("Telegram chat id not set; replace placeholder to enable test")

    handler = TelegramWebhookHandler()
    response = _build_quick_reply_response("telegram", TELEGRAM_TEST_CHAT_ID)
    ok = await handler.send_message(TELEGRAM_TEST_CHAT_ID, response)
    assert ok is True


@pytest.mark.asyncio
async def test_whatsapp_send_quick_replies():
    settings = get_settings().whatsapp
    if not settings.access_token or not settings.phone_number_id:
        pytest.skip("WhatsApp credentials not configured; skipping send test")
    if WHATSAPP_TEST_USER_ID.startswith("REPLACE_"):
        pytest.skip("WhatsApp user id not set; replace placeholder to enable test")

    handler = WhatsAppWebhookHandler()
    response = _build_quick_reply_response("whatsapp", WHATSAPP_TEST_USER_ID)
    ok = await handler.send_message(WHATSAPP_TEST_USER_ID, response)
    assert ok is True


@pytest.mark.asyncio
async def test_telegram_parse_reply_keyboard_text():
    handler = TelegramWebhookHandler()
    # Minimal Telegram message payload from ReplyKeyboard (text-only)
    webhook_data = {
        "update_id": 123,
        "message": {
            "message_id": 42,
            "from": {"id": 999000111, "is_bot": False, "first_name": "User"},
            "chat": {"id": 999000111, "type": "private"},
            "date": int(datetime.now(tz=timezone.utc).timestamp()),
            "text": "Confirm",
        },
    }

    msg = await handler.parse_incoming_message(webhook_data)
    assert msg is not None
    assert msg.channel_type == "telegram"
    assert msg.content == "Confirm"
    # For ReplyKeyboardMarkup, we don't set selected_reply; it's plain text
    assert msg.selected_reply is None


@pytest.mark.asyncio
async def test_whatsapp_parse_quick_reply_interactive():
    handler = WhatsAppWebhookHandler()
    # Minimal WhatsApp interactive button reply payload
    webhook_data = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "dummy_biz_id",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {},
                            "contacts": [
                                {
                                    "profile": {"name": "Test"},
                                    "wa_id": "1234567890",
                                }
                            ],
                            "messages": [
                                {
                                    "id": "wamid.test",
                                    "from": "1234567890",
                                    "timestamp": str(
                                        int(datetime.now(tz=timezone.utc).timestamp())
                                    ),
                                    "type": "interactive",
                                    "interactive": {
                                        "type": "button_reply",
                                        "button_reply": {
                                            "id": "qr_confirm",
                                            "title": "Confirm",
                                        },
                                    },
                                }
                            ],
                        },
                        "field": "messages",
                    }
                ],
            }
        ],
    }

    msg = await handler.parse_incoming_message(webhook_data)
    assert msg is not None
    assert msg.selected_reply is not None
    assert msg.selected_reply.id == "qr_confirm"
    assert msg.channel_type == "whatsapp"
