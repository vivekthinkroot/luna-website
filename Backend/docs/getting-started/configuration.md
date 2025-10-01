# Luna Server Configuration Guide

## 🎯 Overview

Luna Server uses a flexible configuration system based on Pydantic BaseSettings that supports multiple configuration sources:

1. **Environment Variables** - Primary configuration method
2. **JSON Configuration** - For complex deployments
3. **`.env` Files** - For local development
4. **Default Values** - Built-in fallbacks

## 📁 Configuration Structure

Configuration is organized into logical sections:

```
AppSettings
├── database          # Database connection settings
├── telegram           # Telegram bot configuration
├── whatsapp          # WhatsApp Business API settings
├── apis              # External API keys and settings
├── aws               # AWS services configuration
├── llm               # Language model provider settings
├── session           # Session management configuration
├── logging           # Logging and debugging settings
├── geolocation       # Location resolution settings
├── razorpay          # Payment gateway settings
├── scheduling        # Background task settings
└── kundli            # Astrology service settings
```

## 🔧 Configuration Methods

### Method 1: Environment Variables

Set environment variables directly:

```bash
# Database
export DB_URL="postgresql://user:password@localhost:5432/luna_db"

# Telegram
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_WEBHOOK_SECRET="your_webhook_secret"

# LLM
export LLM_PROVIDER_OPENAI_API_KEY="your_openai_key"
```

### Method 2: .env File

Create a `.env` file in the project root:

```bash
# Database Configuration
DB_URL=postgresql://user:password@localhost:5432/luna_db

# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_WEBHOOK_SECRET=your_webhook_secret
TELEGRAM_WEBHOOK_BASE_URL=https://yourdomain.com
TELEGRAM_WEBHOOK_PATH=/webhook/telegram
TELEGRAM_MAX_MESSAGE_LENGTH=4096

# WhatsApp Configuration
WHATSAPP_ACCESS_TOKEN=your_access_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_WEBHOOK_VERIFY_TOKEN=your_verify_token
WHATSAPP_WEBHOOK_SECRET=your_webhook_secret
WHATSAPP_WEBHOOK_BASE_URL=https://yourdomain.com
WHATSAPP_WEBHOOK_PATH=/webhook/whatsapp
WHATSAPP_MAX_MESSAGE_LENGTH=4096

# API Keys (no prefix)
DIVINE_API_KEY=your_divine_api_key
DIVINE_ACCESS_TOKEN=your_divine_access_token
ELEVENLABS_API_KEY=your_elevenlabs_api_key
SARVAM_API_KEY=your_sarvam_api_key

# LLM Configuration
LLM_PROVIDER_OPENAI_API_KEY=your_openai_key
LLM_PROVIDER_OPENAI_BASE_URL=https://api.openai.com/v1
LLM_DEFAULT_PROVIDER=openai
LLM_DEFAULT_MODEL=gpt-4.1-mini

# AWS Configuration
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_S3_BUCKET_NAME=your_bucket_name
AWS_REGION=us-east-1

# Session Settings
SESSION_MAX_TURNS_IN_CACHE=20
SESSION_MAX_CACHE_SIZE=10000

# Logging
LOG_DEBUG_MODE=true
LOG_DEFAULT_LOG_LEVEL=INFO

# Geolocation
GEOLOC_ENABLED=true
GEOLOC_FUZZY_MATCHING_ENABLED=true
GEOLOC_FUZZY_MATCH_THRESHOLD=0.6
GEOLOC_MAX_CANDIDATES=5

# Razorpay
RAZORPAY_API_KEY=your_razorpay_key
RAZORPAY_API_SECRET=your_razorpay_secret
RAZORPAY_BASE_URL=https://api.razorpay.com/v1
RAZORPAY_CALLBACK_BASE_URL=https://yourdomain.com

# Scheduling
SCHEDULING_PAYMENT_POLLING_INTERVAL=60
SCHEDULING_SUBSCRIPTION_CHECK_INTERVAL=86400
SCHEDULING_ENABLE_PAYMENT_POLLING=true
SCHEDULING_ENABLE_SUBSCRIPTION_CHECKS=true

# Kundli Settings
KUNDLI_SEND_PDF_TO_USER=true
```

### Method 3: JSON Configuration

For complex deployments, use JSON configuration:

```bash
export LUNA_CONFIG_JSON='{
  "database": {
    "url": "postgresql://user:password@localhost:5432/luna_db"
  },
  "telegram": {
    "bot_token": "your_bot_token",
    "webhook_secret": "your_webhook_secret",
    "webhook_base_url": "https://yourdomain.com",
    "webhook_path": "/webhook/telegram",
    "max_message_length": 4096
  },
  "llm": {
    "provider_openai_api_key": "your_openai_key",
    "default_provider": "openai",
    "default_model": "gpt-4.1-mini"
  }
}'
```

## 📋 Configuration Reference

### Database Settings

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DB_URL` | PostgreSQL connection URL | None | Yes |

**Example:**
```bash
DB_URL=postgresql://luna_user:password@localhost:5432/luna_db
```

### Telegram Settings

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `TELEGRAM_BOT_TOKEN` | Bot token from BotFather | None | For Telegram |
| `TELEGRAM_WEBHOOK_SECRET` | Webhook verification secret | None | For Telegram |
| `TELEGRAM_WEBHOOK_BASE_URL` | Base URL for webhooks | None | For Telegram |
| `TELEGRAM_WEBHOOK_PATH` | Webhook endpoint path | `/webhook/telegram` | No |
| `TELEGRAM_MAX_MESSAGE_LENGTH` | Maximum message length | 4096 | No |

### WhatsApp Settings

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `WHATSAPP_ACCESS_TOKEN` | WhatsApp Business API token | None | For WhatsApp |
| `WHATSAPP_PHONE_NUMBER_ID` | Phone number ID | None | For WhatsApp |
| `WHATSAPP_WEBHOOK_VERIFY_TOKEN` | Webhook verification token | None | For WhatsApp |
| `WHATSAPP_WEBHOOK_SECRET` | Webhook secret | None | For WhatsApp |
| `WHATSAPP_WEBHOOK_BASE_URL` | Base URL for webhooks | None | For WhatsApp |
| `WHATSAPP_WEBHOOK_PATH` | Webhook endpoint path | `/webhook/whatsapp` | No |
| `WHATSAPP_MAX_MESSAGE_LENGTH` | Maximum message length | 4096 | No |

### LLM Settings

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `LLM_PROVIDER_OPENAI_API_KEY` | OpenAI API key | None | For OpenAI |
| `LLM_PROVIDER_OPENAI_BASE_URL` | OpenAI base URL | `https://api.openai.com/v1` | No |
| `LLM_DEFAULT_PROVIDER` | Default LLM provider | `openai` | No |
| `LLM_DEFAULT_MODEL` | Default model | `gpt-4.1-mini` | No |

### External API Settings

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DIVINE_API_KEY` | Divine API key for astrology | None | For astrology |
| `DIVINE_ACCESS_TOKEN` | Divine API access token | None | For astrology |
| `ELEVENLABS_API_KEY` | ElevenLabs API key | None | For voice |
| `SARVAM_API_KEY` | Sarvam API key | None | For voice |

### AWS Settings

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `AWS_ACCESS_KEY_ID` | AWS access key | None | For AWS features |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | None | For AWS features |
| `AWS_S3_BUCKET_NAME` | S3 bucket name | None | For file storage |
| `AWS_REGION` | AWS region | `us-east-1` | No |

### Session Settings

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SESSION_MAX_TURNS_IN_CACHE` | Max conversation turns to cache | 20 | No |
| `SESSION_MAX_CACHE_SIZE` | Max cache size in characters | 10000 | No |

### Logging Settings

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `LOG_DEBUG_MODE` | Enable debug logging | `true` | No |
| `LOG_DEFAULT_LOG_LEVEL` | Default log level | `INFO` | No |
| `LOG_SQLALCHEMY_ENGINE_LEVEL` | SQLAlchemy log level | `WARNING` | No |

### Geolocation Settings

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `GEOLOC_ENABLED` | Enable geolocation service | `true` | No |
| `GEOLOC_FUZZY_MATCHING_ENABLED` | Enable fuzzy matching | `true` | No |
| `GEOLOC_FUZZY_MATCH_THRESHOLD` | Fuzzy match threshold | 0.6 | No |
| `GEOLOC_MAX_CANDIDATES` | Max location candidates | 5 | No |

### Payment Settings (Razorpay)

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `RAZORPAY_API_KEY` | Razorpay API key | None | For payments |
| `RAZORPAY_API_SECRET` | Razorpay API secret | None | For payments |
| `RAZORPAY_BASE_URL` | Razorpay base URL | `https://api.razorpay.com/v1` | No |
| `RAZORPAY_CALLBACK_BASE_URL` | Callback base URL | None | For payments |

### Scheduling Settings

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SCHEDULING_PAYMENT_POLLING_INTERVAL` | Payment polling interval (seconds) | 60 | No |
| `SCHEDULING_SUBSCRIPTION_CHECK_INTERVAL` | Subscription check interval (seconds) | 86400 | No |
| `SCHEDULING_ENABLE_PAYMENT_POLLING` | Enable payment polling | `true` | No |
| `SCHEDULING_ENABLE_SUBSCRIPTION_CHECKS` | Enable subscription checks | `true` | No |

### Kundli Settings

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `KUNDLI_SEND_PDF_TO_USER` | Send PDF documents to users | `true` | No |

## 🔒 Security Best Practices

### 1. Environment Variable Security

```bash
# Use secure values
TELEGRAM_WEBHOOK_SECRET=$(openssl rand -hex 32)
WHATSAPP_WEBHOOK_SECRET=$(openssl rand -hex 32)

# Never commit secrets to version control
echo ".env" >> .gitignore
```

### 2. Production Configuration

```bash
# Disable debug mode
LOG_DEBUG_MODE=false

# Use appropriate log levels
LOG_DEFAULT_LOG_LEVEL=WARNING

# Use secure database connections
DB_URL=postgresql://user:password@secure-host:5432/luna_db?sslmode=require
```

### 3. API Key Management

- Use environment-specific API keys
- Rotate keys regularly
- Monitor API usage
- Set up alerts for unusual activity

## 🧪 Configuration Validation

### Testing Configuration

```python
from config.settings import get_settings

# Test configuration loading
settings = get_settings()

# Check if minimal configuration is present
if settings.is_minimal_config():
    print("Warning: Running with minimal configuration")

# Validate specific settings
assert settings.database.is_configured(), "Database not configured"
assert settings.llm.provider_openai_api_key, "OpenAI API key required"
```

### Configuration Health Check

Visit `/health` endpoint to see configuration status:

```json
{
  "status": "healthy",
  "service": "Luna Server",
  "startup_status": {
    "telegram_webhook_registered": true,
    "startup_complete": true,
    "internet_connectivity": true,
    "errors": []
  }
}
```

## 🔄 Dynamic Configuration

### Runtime Configuration Updates

Configuration is cached for 1 hour. To force reload:

```python
from config.settings import clear_settings_cache

# Clear cache to reload configuration
clear_settings_cache()
```

### Environment-Specific Configuration

#### Development
```bash
LOG_DEBUG_MODE=true
LOG_DEFAULT_LOG_LEVEL=DEBUG
```

#### Staging
```bash
LOG_DEBUG_MODE=false
LOG_DEFAULT_LOG_LEVEL=INFO
```

#### Production
```bash
LOG_DEBUG_MODE=false
LOG_DEFAULT_LOG_LEVEL=WARNING
```

## 🚨 Troubleshooting

### Common Configuration Issues

#### 1. Database Connection Failed
```bash
# Check database URL format
DB_URL=postgresql://username:password@host:port/database

# Test connection
psql $DB_URL -c "SELECT 1;"
```

#### 2. Webhook Verification Failed
```bash
# Ensure webhook secrets are set
echo $TELEGRAM_WEBHOOK_SECRET
echo $WHATSAPP_WEBHOOK_SECRET
```

#### 3. LLM Provider Not Available
```bash
# Check API key is set
echo $LLM_PROVIDER_OPENAI_API_KEY

# Test API connectivity
curl -H "Authorization: Bearer $LLM_PROVIDER_OPENAI_API_KEY" \
     https://api.openai.com/v1/models
```

#### 4. Configuration Not Loading
```bash
# Check .env file exists and is readable
ls -la .env

# Verify environment variables are set
env | grep -E "(DB_|TELEGRAM_|LLM_)"
```

### Debug Mode

Enable comprehensive logging:

```bash
LOG_DEBUG_MODE=true
LOG_DEFAULT_LOG_LEVEL=DEBUG
LOG_SQLALCHEMY_ENGINE_LEVEL=INFO
```

## 📊 Configuration Examples

### Minimal Configuration (Development)

```bash
# .env file for local development
DB_URL=postgresql://luna:password@localhost:5432/luna_db
LLM_PROVIDER_OPENAI_API_KEY=your_openai_key
DIVINE_API_KEY=your_divine_key
LOG_DEBUG_MODE=true
```

### Full Configuration (Production)

```bash
# Complete production configuration
DB_URL=postgresql://luna:password@prod-db:5432/luna_db

TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_WEBHOOK_SECRET=your_webhook_secret
TELEGRAM_WEBHOOK_BASE_URL=https://api.yourdomain.com

WHATSAPP_ACCESS_TOKEN=your_whatsapp_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_id
WHATSAPP_WEBHOOK_VERIFY_TOKEN=your_verify_token
WHATSAPP_WEBHOOK_SECRET=your_webhook_secret
WHATSAPP_WEBHOOK_BASE_URL=https://api.yourdomain.com

LLM_PROVIDER_OPENAI_API_KEY=your_openai_key
LLM_DEFAULT_PROVIDER=openai
LLM_DEFAULT_MODEL=gpt-4.1-mini

DIVINE_API_KEY=your_divine_key
DIVINE_ACCESS_TOKEN=your_divine_token

AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_S3_BUCKET_NAME=luna-artifacts
AWS_REGION=us-east-1

RAZORPAY_API_KEY=your_razorpay_key
RAZORPAY_API_SECRET=your_razorpay_secret
RAZORPAY_CALLBACK_BASE_URL=https://api.yourdomain.com

LOG_DEBUG_MODE=false
LOG_DEFAULT_LOG_LEVEL=INFO

KUNDLI_SEND_PDF_TO_USER=true
```

---

**Next Steps:**
- [Quick Start Tutorial](quick-start.md) - Build your first integration
- [Architecture Overview](../architecture/overview.md) - Understanding the system design
- [Settings Guide](../settings-guide.md) - Detailed settings reference
