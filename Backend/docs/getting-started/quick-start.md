# Luna Server Quick Start Tutorial

## 🚀 Build Your First Integration in 10 Minutes

This tutorial will get you up and running with Luna Server quickly, walking you through setting up a basic astrology assistant that can generate kundli reports.

## 📋 Prerequisites

Before starting, ensure you have:

- Python 3.12+ installed
- PostgreSQL running locally or in Docker
- An OpenAI API key
- A Divine API key (for astrology services)

## ⚡ Quick Setup

### Step 1: Clone and Install

```bash
# Clone the repository
git clone https://github.com/your-org/luna-server.git
cd luna-server

# Create and activate virtual environment
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Database Setup

Using Docker (recommended for quick start):

```bash
# Start PostgreSQL in Docker
docker run --name luna-postgres \
  -e POSTGRES_DB=luna_db \
  -e POSTGRES_USER=luna_user \
  -e POSTGRES_PASSWORD=quickstart123 \
  -p 5432:5432 \
  -d postgres:15

# Wait for database to start (about 10 seconds)
sleep 10

# Create database schema
psql -U luna_user -h localhost -d luna_db -f data/model.sql
```

### Step 3: Basic Configuration

Create a `.env` file with minimal configuration:

```bash
cat > .env << EOF
# Database
DB_URL=postgresql://luna_user:quickstart123@localhost:5432/luna_db

# LLM (required for intent classification)
LLM_PROVIDER_OPENAI_API_KEY=your_openai_api_key_here

# Astrology API (required for kundli generation)
DIVINE_API_KEY=your_divine_api_key_here
DIVINE_ACCESS_TOKEN=your_divine_access_token_here

# Logging
LOG_DEBUG_MODE=true
LOG_DEFAULT_LOG_LEVEL=INFO
EOF
```

**Replace the placeholder values:**
- `your_openai_api_key_here` - Get from [OpenAI API Keys](https://platform.openai.com/api-keys)
- `your_divine_api_key_here` - Get from [Divine API](https://divineapi.com)
- `your_divine_access_token_here` - Your Divine API access token

### Step 4: Start the Server

```bash
# Start Luna Server
python server.py
```

You should see:
```
Starting Luna FastAPI application...
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 5: Verify Installation

Open another terminal and test the health endpoint:

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "Luna Server",
  "startup_status": {
    "startup_complete": true,
    "internet_connectivity": true,
    "errors": []
  }
}
```

## 🧪 Test Your Installation

### Basic Web Interface Testing

Luna Server includes a simple web interface for testing:

1. Open your browser and go to `http://localhost:8000`
2. You should see a simple "Hello World, from Luna!" message

### Health Check Testing

Test the health endpoint:

```bash
# Check server health
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "Luna Server",
  "startup_status": {
    "startup_complete": true,
    "internet_connectivity": true,
    "errors": []
  }
}
```

## 🎯 Testing with Messaging Channels

Luna Server is designed to work with messaging platforms like Telegram and WhatsApp. The core functionality is accessed through these channels rather than direct API calls.

## 📱 Telegram Bot Integration

To test with Telegram (optional):

### 1. Create a Telegram Bot

1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot` and follow instructions
3. Save the bot token

### 2. Configure Telegram

Add to your `.env` file:

```bash
# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_WEBHOOK_SECRET=my_secret_webhook_key
TELEGRAM_WEBHOOK_BASE_URL=https://your-domain.com
TELEGRAM_WEBHOOK_PATH=/webhook/telegram
```

### 3. Set Up Ngrok (for local testing)

```bash
# Install ngrok (if not already installed)
# Then expose your local server
ngrok http 8000
```

Update your `.env` with the ngrok URL:
```bash
TELEGRAM_WEBHOOK_BASE_URL=https://abc123.ngrok.io
```

Restart the server, and your bot should be ready for testing on Telegram!

## 🔍 Understanding the System

### Key Components You Just Used

1. **API Layer** (`api/app.py`) - Handles HTTP requests and webhooks
2. **Router Service** (`services/router.py`) - Classifies user intents using LLM
3. **Workflow Engine** (`services/workflows/`) - Manages multi-step conversations
4. **Domain Services** (`kundli/`, `qna/`) - Provides astrology functionality
5. **Data Layer** (`dao/`, `data/`) - Manages user profiles and conversations

### Workflow Architecture

Your test interaction used these workflows:

```
User Message → Intent Classification → Workflow Selection → Step Execution → Response
```

For profile creation:
```
"I want to create a profile" → add_profile intent → AddProfileStep workflow → Collect user data
```

For kundli generation:
```
"Generate my kundli" → generate_kundli intent → GenerateKundliStep workflow → Astrological analysis
```

## 🛠️ Understanding the System

### Key Components

1. **API Layer** (`api/app.py`) - Handles HTTP requests and webhooks
2. **Router Service** (`services/router.py`) - Classifies user intents using LLM
3. **Workflow Engine** (`services/workflows/`) - Manages multi-step conversations
4. **Domain Services** (`kundli/`, `qna/`) - Provides astrology functionality
5. **Data Layer** (`dao/`, `data/`) - Manages user profiles and conversations

### Current Workflows

The system includes these working workflows:
- **Add Profile**: Collects user birth information
- **Generate Kundli**: Creates astrological reports
- **Profile QnA**: Answers astrology questions
- **Main Menu**: Provides navigation options

## 📊 Monitoring and Debugging

### View Logs

```bash
# View application logs
tail -f logs/app.log

# View LLM interaction logs
tail -f logs/llm.jsonl
```

### Debug Mode

Enable detailed debugging:

```bash
# In .env file
LOG_DEBUG_MODE=true
LOG_DEFAULT_LOG_LEVEL=DEBUG
```

### Health Monitoring

Check system status:

```bash
# Basic health check
curl http://localhost:8000/health

# Test internet connectivity
curl -X POST http://localhost:8000/admin/check-internet-connectivity
```

## 🚀 Next Steps

Now that you have Luna Server running:

1. **Explore the Documentation**:
   - [Architecture Overview](../architecture/overview.md) - Understand the system design
   - [Workflow Development](../guides/workflow-development.md) - Build custom workflows
   - [Intent Management](../guides/intent-management.md) - Add new intents

2. **Set Up Additional Channels**:
   - Configure WhatsApp Business API
   - Set up webhook endpoints
   - Test multi-channel functionality

3. **Customize for Your Use Case**:
   - Modify existing workflows
   - Add new domain services
   - Integrate additional APIs

4. **Deploy to Production**:
   - Follow the [Deployment Guide](../deployment-guide.md)
   - Set up monitoring and alerts
   - Configure production security

## 🆘 Troubleshooting

### Common Issues

#### Server Won't Start
```bash
# Check Python version
python --version  # Should be 3.12+

# Check database connection
psql $DB_URL -c "SELECT 1;"
```

#### API Calls Fail
```bash
# Check environment variables
env | grep -E "(LLM_|DIVINE_)"

# Test API keys
curl -H "Authorization: Bearer $LLM_PROVIDER_OPENAI_API_KEY" \
     https://api.openai.com/v1/models
```

#### Profile Creation Fails
- Ensure Divine API credentials are correct
- Check that the database schema is loaded
- Verify geolocation service is working

### Getting Help

- **Logs**: Check `logs/app.log` for detailed error information
- **Health Check**: Visit `/health` endpoint for system status
- **Debug Mode**: Enable debug logging for verbose output

---

**Congratulations!** 🎉 You now have Luna Server running and understand the basics of how it works. You're ready to build sophisticated astrology applications with conversational AI!

**Next recommended reading:**
- [Architecture Overview](../architecture/overview.md) - Deep dive into system design
- [Workflow Development Guide](../guides/workflow-development.md) - Build custom conversational flows
- [Channel Integration Guide](../guides/channel-integration.md) - Add new messaging platforms
