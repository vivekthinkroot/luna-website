# Luna Server Installation Guide

## 🚀 Quick Installation

### Prerequisites

- **Python 3.12+** (required)
- **PostgreSQL 12+** (database)
- **Git** (for cloning the repository)

### System Requirements

- **Memory**: Minimum 2GB RAM, Recommended 4GB+
- **Storage**: At least 1GB free space
- **Network**: Internet connection for API calls and webhooks

## 📦 Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/luna-server.git
cd luna-server
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python3.12 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install Python packages
pip install -r requirements.txt
```

### 4. Database Setup

#### Option A: Local PostgreSQL

1. Install PostgreSQL 12+ on your system
2. Create a database for Luna:

```sql
-- Connect to PostgreSQL as superuser
createdb luna_db
createuser luna_user --password

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE luna_db TO luna_user;
```

#### Option B: Docker PostgreSQL

```bash
# Run PostgreSQL in Docker
docker run --name luna-postgres \
  -e POSTGRES_DB=luna_db \
  -e POSTGRES_USER=luna_user \
  -e POSTGRES_PASSWORD=your_password \
  -p 5432:5432 \
  -d postgres:15
```

### 5. Environment Configuration

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```bash
# Database Configuration
DB_URL=postgresql://luna_user:your_password@localhost:5432/luna_db

# Telegram Bot (optional)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_WEBHOOK_SECRET=your_webhook_secret
TELEGRAM_WEBHOOK_BASE_URL=https://yourdomain.com
TELEGRAM_WEBHOOK_PATH=/webhook/telegram

# WhatsApp Business API (optional)
WHATSAPP_ACCESS_TOKEN=your_whatsapp_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_WEBHOOK_VERIFY_TOKEN=your_verify_token
WHATSAPP_WEBHOOK_SECRET=your_webhook_secret
WHATSAPP_WEBHOOK_BASE_URL=https://yourdomain.com
WHATSAPP_WEBHOOK_PATH=/webhook/whatsapp

# LLM Configuration
LLM_PROVIDER_OPENAI_API_KEY=your_openai_api_key
LLM_DEFAULT_PROVIDER=openai
LLM_DEFAULT_MODEL=gpt-4.1-mini

# Divine API (for astrology services)
DIVINE_API_KEY=your_divine_api_key
DIVINE_ACCESS_TOKEN=your_divine_access_token

# Logging
LOG_DEBUG_MODE=true
LOG_DEFAULT_LOG_LEVEL=INFO
```

### 6. Database Schema Setup

Run the database migrations:

```bash
# Load the database schema
psql -U luna_user -d luna_db -f data/model.sql

# Load initial data (optional)
python load_data.py
```

### 7. Verify Installation

Test the installation:

```bash
# Start the server
python server.py

# Or using uvicorn directly
uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload
```

Visit `http://localhost:8000/health` to verify the server is running.

## 🔧 Development Setup

### Additional Development Dependencies

For development, you may want additional tools:

```bash
# Install development dependencies
pip install pytest pytest-asyncio black isort mypy

# Pre-commit hooks (optional)
pip install pre-commit
pre-commit install
```

### IDE Configuration

#### VS Code

Recommended extensions:
- Python
- Pylance
- Python Docstring Generator
- GitLens

#### PyCharm

Configure the Python interpreter to use your virtual environment.

### Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/          # Unit tests
pytest tests/integration/   # Integration tests

# Run with coverage
pytest --cov=. --cov-report=html
```

## 🐳 Docker Installation

### Using Docker Compose

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Manual Docker Setup

```bash
# Build the image
docker build -t luna-server .

# Run the container
docker run -d \
  --name luna-server \
  -p 8000:8000 \
  --env-file .env \
  luna-server
```

## ☁️ Cloud Deployment

### AWS App Runner

See the [Deployment Guide](../deployment-guide.md) for detailed AWS App Runner deployment instructions.

### Other Cloud Providers

Luna Server can be deployed to:
- **Heroku**: Using the included `Procfile`
- **Google Cloud Run**: Using the `Dockerfile`
- **Azure Container Instances**: Using Docker deployment
- **DigitalOcean App Platform**: Using Docker or buildpack

## 🔍 Troubleshooting

### Common Issues

#### 1. Database Connection Errors

```bash
# Check PostgreSQL is running
pg_isready -h localhost -p 5432

# Test connection
psql -U luna_user -d luna_db -c "SELECT 1;"
```

#### 2. Python Version Issues

```bash
# Verify Python version
python --version  # Should be 3.12+

# If using wrong version
python3.12 -m venv venv
```

#### 3. Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>
```

#### 4. Missing Environment Variables

```bash
# Check if .env file exists and is readable
ls -la .env
cat .env
```

### Getting Help

- **Logs**: Check `logs/app.log` for detailed error information
- **Health Check**: Visit `/health` endpoint for system status
- **Debug Mode**: Set `LOG_DEBUG_MODE=true` for verbose logging

## 📈 Performance Optimization

### Production Configuration

For production deployment:

```bash
# Disable debug mode
LOG_DEBUG_MODE=false
LOG_DEFAULT_LOG_LEVEL=INFO

# Configure database connection pooling
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30

# Set appropriate worker processes
WORKERS=4
```

### Resource Monitoring

Monitor these metrics:
- Memory usage
- Database connections
- Response times
- Error rates

## 🔄 Updating Luna Server

### Standard Updates

```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt

# Run database migrations (if any)
# Check for new migration files in data/

# Restart the server
```

### Major Version Updates

Check the changelog for breaking changes and follow the migration guide for your specific version upgrade.

---

**Next Steps:**
- [Configuration Guide](configuration.md) - Detailed configuration options
- [Quick Start Tutorial](quick-start.md) - Build your first integration
- [Architecture Overview](../architecture/overview.md) - Understanding the system design
