# Channel Integration Guide

## 🎯 Overview

Luna Server supports multiple messaging channels through a unified architecture that abstracts platform-specific implementations behind a common interface. This guide covers how to integrate new messaging platforms and understand the existing channel implementations.

## 🏗️ Channel Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    External Platforms                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌──────┐  │
│  │  Telegram   │  │  WhatsApp   │  │     Web     │  │ API  │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └──────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Channel Handlers                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌──────┐  │
│  │ TelegramWH  │  │ WhatsAppWH  │  │ WebHandler  │  │ API  │  │
│  │   Handler   │  │   Handler   │  │             │  │Handler│ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └──────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                Message Canonicalization                        │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │           CanonicalRequestMessage                           │ │
│  │  • user_id • channel_type • content • metadata             │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Channels Service                             │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  • User Management • Message Processing • Response Routing │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Base Channel Interface

All channel handlers implement the `ChannelHandler` abstract base class:

```python
class ChannelHandler(ABC):
    @abstractmethod
    async def parse_incoming_message(
        self, webhook_data: Dict[str, Any]
    ) -> CanonicalRequestMessage:
        """Convert platform-specific message to canonical format."""
        pass

    @abstractmethod
    async def send_message(
        self, channel_user_id: str, response: CanonicalResponseMessage
    ) -> bool:
        """Send message back to user through the channel."""
        pass

    @abstractmethod
    def validate_webhook(self, headers: Dict[str, str], body: str) -> bool:
        """Validate webhook authenticity."""
        pass
```

## 📱 Existing Channel Implementations

### 1. Telegram Integration

**File**: `channels/telegram.py`

**Features**:
- Full webhook integration with Telegram Bot API
- Support for text messages and quick reply buttons
- Webhook signature validation
- Automatic webhook registration
- Message formatting with HTML support

**Configuration**:
```bash
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_WEBHOOK_SECRET=your_webhook_secret
TELEGRAM_WEBHOOK_BASE_URL=https://yourdomain.com
TELEGRAM_WEBHOOK_PATH=/webhook/telegram
TELEGRAM_MAX_MESSAGE_LENGTH=4096
```

**Webhook Endpoint**: `POST /webhook/telegram`

**Message Flow**:
```
Telegram → Webhook → TelegramWebhookHandler → CanonicalRequestMessage → ChannelsService
```

### 2. WhatsApp Integration

**File**: `channels/whatsapp.py`

**Features**:
- WhatsApp Business API integration
- Support for text messages and interactive buttons
- Webhook verification with Meta's signature validation
- Status update handling
- Message formatting with WhatsApp-specific features

**Configuration**:
```bash
WHATSAPP_ACCESS_TOKEN=your_access_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_WEBHOOK_VERIFY_TOKEN=your_verify_token
WHATSAPP_WEBHOOK_SECRET=your_webhook_secret
WHATSAPP_WEBHOOK_BASE_URL=https://yourdomain.com
WHATSAPP_WEBHOOK_PATH=/webhook/whatsapp
WHATSAPP_MAX_MESSAGE_LENGTH=4096
```

**Webhook Endpoints**:
- `POST /webhook/whatsapp` - Message handling
- `GET /webhook/whatsapp` - Webhook verification

**Message Flow**:
```
WhatsApp → Webhook → WhatsAppWebhookHandler → CanonicalRequestMessage → ChannelsService
```

### 3. Web Interface

**File**: `channels/web.py`

**Status**: Stub implementation (not yet functional)

**Current State**: Contains placeholder methods that raise `NotImplementedError`

### 4. API Interface

**File**: `channels/api.py`

**Status**: Stub implementation (not yet functional)

**Current State**: Contains placeholder methods that raise `NotImplementedError`

## 🔧 Creating a New Channel Integration

### Step 1: Implement Channel Handler

Create a new file in the `channels/` directory:

```python
# channels/discord.py
from typing import Any, Dict
from channels.base import ChannelHandler
from utils.models import CanonicalRequestMessage, CanonicalResponseMessage, ContentType, ChannelType
from config.settings import get_settings
import httpx

class DiscordWebhookHandler(ChannelHandler):
    def __init__(self):
        self.settings = get_settings().discord  # Add DiscordSettings to config
        self.bot_token = self.settings.bot_token
        self.webhook_secret = self.settings.webhook_secret
        self.base_url = "https://discord.com/api/v10"
        
    async def parse_incoming_message(
        self, webhook_data: Dict[str, Any]
    ) -> CanonicalRequestMessage:
        """Parse Discord webhook data into canonical format."""
        
        # Extract message data from Discord webhook
        message_data = webhook_data.get("d", {})
        author = message_data.get("author", {})
        
        # Skip bot messages
        if author.get("bot", False):
            return None
            
        return CanonicalRequestMessage(
            user_id="",  # Will be resolved by ChannelsService
            channel_type=ChannelType.DISCORD,
            channel_user_id=author.get("id"),
            content=message_data.get("content", ""),
            content_type=ContentType.TEXT,
            metadata={
                "discord_channel_id": message_data.get("channel_id"),
                "discord_guild_id": message_data.get("guild_id"),
                "discord_message_id": message_data.get("id"),
                "username": author.get("username"),
                "discriminator": author.get("discriminator")
            }
        )
    
    async def send_message(
        self, channel_user_id: str, response: CanonicalResponseMessage
    ) -> bool:
        """Send message back to Discord user."""
        try:
            # Get DM channel with user
            dm_channel = await self._get_or_create_dm_channel(channel_user_id)
            
            headers = {
                "Authorization": f"Bot {self.bot_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "content": response.content
            }
            
            # Add components for quick replies if present
            if response.reply_options:
                components = self._build_discord_components(response.reply_options)
                payload["components"] = components
            
            async with httpx.AsyncClient() as client:
                discord_response = await client.post(
                    f"{self.base_url}/channels/{dm_channel['id']}/messages",
                    headers=headers,
                    json=payload
                )
                
            return discord_response.status_code == 200
            
        except Exception as e:
            logger.error(f"Failed to send Discord message: {e}")
            return False
    
    def validate_webhook(self, headers: Dict[str, str], body: str) -> bool:
        """Validate Discord webhook signature."""
        signature = headers.get("X-Signature-Ed25519")
        timestamp = headers.get("X-Signature-Timestamp")
        
        if not signature or not timestamp:
            return False
            
        # Implement Discord's Ed25519 signature validation
        # This is Discord-specific cryptographic validation
        return self._verify_discord_signature(signature, timestamp, body)
    
    async def _get_or_create_dm_channel(self, user_id: str) -> Dict[str, Any]:
        """Get or create DM channel with user."""
        # Implementation for Discord DM channel creation
        pass
    
    def _build_discord_components(self, reply_options) -> List[Dict[str, Any]]:
        """Build Discord message components from reply options."""
        # Convert Luna reply options to Discord components
        pass
    
    def _verify_discord_signature(self, signature: str, timestamp: str, body: str) -> bool:
        """Verify Discord webhook signature using Ed25519."""
        # Implementation for Discord signature verification
        pass
```

### Step 2: Add Configuration Settings

Add Discord settings to `config/settings.py`:

```python
class DiscordSettings(BaseSettings):
    """Discord bot configuration settings."""
    
    bot_token: Optional[str] = None
    webhook_secret: Optional[str] = None
    webhook_base_url: Optional[str] = None
    webhook_path: str = "/webhook/discord"
    max_message_length: int = 2000
    
    model_config = SettingsConfigDict(env_prefix="DISCORD_", extra="ignore")

# Add to AppSettings
class AppSettings(BaseSettings):
    # ... existing settings ...
    discord: DiscordSettings = Field(default_factory=lambda: DiscordSettings())
```

### Step 3: Add Channel Type

Add the new channel type to `data/models.py`:

```python
class ChannelType(str, Enum):
    TELEGRAM = "telegram"
    WHATSAPP = "whatsapp"
    DISCORD = "discord"  # Add this
    PHONE = "phone"
    EMAIL = "email"
    SMS = "sms"
```

### Step 4: Register Channel Handler

Update `services/channels.py` to include your new handler:

```python
class ChannelsService:
    def __init__(self):
        self.user_dao = UserDAO()
        self.conversation_dao = ConversationDAO()
        self.channel_handlers = {
            "telegram": TelegramWebhookHandler(),
            "whatsapp": WhatsAppWebhookHandler(),
            "discord": DiscordWebhookHandler(),  # Add this
        }
        # ... rest of initialization
```

### Step 5: Add Webhook Endpoint

Add the webhook endpoint to `api/app.py`:

```python
from channels.discord import DiscordWebhookHandler

discord_handler = DiscordWebhookHandler()

@app.post("/webhook/discord", tags=["Discord"])
async def discord_webhook(request: Request):
    body = await request.body()
    headers = dict(request.headers)
    
    # Validate webhook
    if not discord_handler.validate_webhook(headers, body.decode()):
        logger.warning("Invalid Discord webhook signature.")
        return JSONResponse(
            status_code=403,
            content={"error": "Invalid webhook signature"},
        )
    
    try:
        payload = await request.json()
        logger.debug(f"Received Discord webhook call: {payload}")
        
        canonical_msg = await discord_handler.parse_incoming_message(payload)
        
        if canonical_msg is None:
            return JSONResponse(content={"success": True})
        
        # Process through channels service
        await channels_service.enqueue_incoming_message(canonical_msg)
        return JSONResponse(content={"ok": True, "scheduled": True})
        
    except Exception as e:
        logger.error(f"Error processing Discord webhook: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})
```

### Step 6: Update Channel Registry

Add your handler to `channels/__init__.py`:

```python
from .discord import DiscordWebhookHandler

__all__ = [
    "ChannelHandler",
    "APIHandler",
    "TelegramWebhookHandler",
    "WebHandler",
    "WhatsAppWebhookHandler",
    "DiscordWebhookHandler",  # Add this
    "register_telegram_webhook",
]
```

## 🔄 Message Flow Architecture

### Incoming Message Processing

```
1. External Platform → Webhook Endpoint
   ↓
2. Channel Handler → parse_incoming_message()
   ↓
3. CanonicalRequestMessage Creation
   ↓
4. ChannelsService → enqueue_incoming_message()
   ↓
5. User Resolution/Creation
   ↓
6. Router Service → Intent Classification
   ↓
7. Workflow Engine → Business Logic
   ↓
8. Response Generation
```

### Outgoing Message Processing

```
1. Workflow/Service → CanonicalResponseMessage
   ↓
2. ChannelsService → send_message()
   ↓
3. Channel Handler → send_message()
   ↓
4. Platform-Specific Formatting
   ↓
5. External Platform API Call
   ↓
6. Delivery Confirmation
```

## 📊 Message Canonicalization

### CanonicalRequestMessage

```python
class CanonicalRequestMessage(BaseModel):
    user_id: str                    # Internal user identifier
    channel_type: ChannelType       # Platform identifier
    channel_user_id: str            # Platform-specific user ID
    content: str                    # Message content
    content_type: ContentType       # TEXT, VOICE, IMAGE, etc.
    metadata: Dict[str, Any] = {}   # Platform-specific data
    selected_reply: Optional[QuickReplyOption] = None  # Selected quick reply
```

### CanonicalResponseMessage

```python
class CanonicalResponseMessage(BaseModel):
    user_id: str                    # Target user
    channel_type: ChannelType       # Target platform
    content: str                    # Response content
    content_type: ContentType       # Response type
    reply_options: Optional[List[QuickReplyOption]] = None  # Quick replies
    metadata: Dict[str, Any] = {}   # Additional data
```

## 🎨 Platform-Specific Features

### Quick Reply Buttons

Different platforms handle interactive elements differently:

**Telegram**:
```python
# Inline keyboard buttons
inline_keyboard = [
    [{"text": "Yes", "callback_data": "workflow:generate_kundli:yes"}],
    [{"text": "No", "callback_data": "workflow:generate_kundli:no"}]
]
```

**WhatsApp**:
```python
# Interactive buttons (max 3)
buttons = [
    {"type": "reply", "reply": {"id": "yes", "title": "Yes"}},
    {"type": "reply", "reply": {"id": "no", "title": "No"}}
]
```

**Discord**:
```python
# Message components
components = [
    {
        "type": 1,  # Action Row
        "components": [
            {
                "type": 2,  # Button
                "style": 1,  # Primary
                "label": "Yes",
                "custom_id": "workflow:generate_kundli:yes"
            }
        ]
    }
]
```

### Message Formatting

Each platform supports different formatting:

**Telegram**: HTML and Markdown
```python
content = "<b>Bold text</b> and <i>italic text</i>"
```

**WhatsApp**: Limited formatting
```python
content = "*Bold text* and _italic text_"
```

**Discord**: Markdown
```python
content = "**Bold text** and *italic text*"
```

## 🔒 Security Considerations

### Webhook Validation

Each platform has its own webhook validation mechanism:

**Telegram**: HMAC-SHA256 with secret token
**WhatsApp**: HMAC-SHA256 with app secret
**Discord**: Ed25519 signature verification

### Best Practices

1. **Always validate webhooks** - Never trust incoming data
2. **Use HTTPS** - Encrypt all webhook communications
3. **Implement rate limiting** - Protect against abuse
4. **Log security events** - Monitor for suspicious activity
5. **Rotate secrets regularly** - Update webhook secrets periodically

## 🧪 Testing Channel Integrations

### Unit Testing

```python
import pytest
from channels.discord import DiscordWebhookHandler

class TestDiscordHandler:
    @pytest.fixture
    def handler(self):
        return DiscordWebhookHandler()
    
    @pytest.mark.asyncio
    async def test_parse_incoming_message(self, handler):
        webhook_data = {
            "d": {
                "id": "message_id",
                "content": "Hello Luna",
                "author": {
                    "id": "user_id",
                    "username": "testuser",
                    "bot": False
                },
                "channel_id": "channel_id"
            }
        }
        
        result = await handler.parse_incoming_message(webhook_data)
        
        assert result.content == "Hello Luna"
        assert result.channel_type == ChannelType.DISCORD
        assert result.channel_user_id == "user_id"
```

### Integration Testing

```python
@pytest.mark.asyncio
async def test_discord_message_flow():
    """Test complete message flow through Discord channel."""
    
    # Simulate webhook payload
    webhook_data = create_discord_webhook_data()
    
    # Process through channel handler
    handler = DiscordWebhookHandler()
    canonical_msg = await handler.parse_incoming_message(webhook_data)
    
    # Process through channels service
    channels_service = ChannelsService()
    response = await channels_service.process_incoming_message(canonical_msg)
    
    # Verify response
    assert response is not None
    assert response.content is not None
```

### Manual Testing

Use tools like ngrok for local webhook testing:

```bash
# Expose local server
ngrok http 8000

# Update webhook URL in platform settings
# Test by sending messages through the platform
```

## 📊 Monitoring and Analytics

### Channel Metrics

Track important metrics for each channel:

```python
class ChannelMetrics:
    def track_message_received(self, channel_type: ChannelType):
        """Track incoming message count."""
        pass
    
    def track_message_sent(self, channel_type: ChannelType, success: bool):
        """Track outgoing message success/failure."""
        pass
    
    def track_response_time(self, channel_type: ChannelType, duration: float):
        """Track message processing time."""
        pass
```

### Health Monitoring

Monitor channel health:

```python
@app.get("/health/channels")
async def channels_health():
    """Check health of all channel integrations."""
    health_status = {}
    
    for channel_name, handler in channels_service.channel_handlers.items():
        try:
            # Test channel connectivity
            health_status[channel_name] = await test_channel_health(handler)
        except Exception as e:
            health_status[channel_name] = {"status": "unhealthy", "error": str(e)}
    
    return health_status
```

## 🚀 Current Architecture Features

### Multi-Channel User Support

The system currently supports users having accounts across different channels, with each channel maintaining its own user ID mapping to the internal Luna user system.

### Channel-Specific Message Handling

The workflow system adapts message formatting and interaction options based on the channel capabilities:

- **Telegram**: Supports rich HTML formatting and inline keyboard buttons
- **WhatsApp**: Supports limited formatting and interactive buttons (max 3)
- **Web/API**: Stub implementations for future development

---

This channel integration guide provides a comprehensive framework for adding new messaging platforms to Luna Server while maintaining consistency and reliability across all channels. The modular architecture ensures that each channel can leverage platform-specific features while providing a unified user experience.
