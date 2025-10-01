# Luna Server Deployment Architecture

## 🚀 Deployment Overview

This document outlines the deployment architecture for Luna Server, covering production deployment strategies, scaling considerations, infrastructure requirements, and operational best practices.

## 🏗️ Deployment Architecture

### **Current Architecture (Monolithic)**

```
┌─────────────────────────────────────────────────────────────────┐
│                        Load Balancer                           │
│                    (Nginx/Cloud Load Balancer)                 │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Luna Server Instance                        │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              FastAPI Application                           │ │
│  │  • Channel Handlers • Services • Workflows • DAOs         │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PostgreSQL Database                         │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  • User Data • Profiles • Conversations • Payments        │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```


## 🐳 Containerization Strategy

### **Docker Configuration**

**Current Docker Configuration:**
```dockerfile
# Use Ubuntu 24.04 for latest LTS and better Python 3.12 support
FROM ubuntu:24.04

# Set working directory
WORKDIR /app

# Install Python 3.12 and system dependencies
RUN apt-get update && \
    apt-get install -y \
    python3.12 \
    python3.12-dev \
    python3.12-venv \
    python3-pip \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install WeasyPrint system dependencies
RUN apt-get update && \
    apt-get install -y \
    libpango-1.0-0 \
    libharfbuzz0b \
    libpangoft2-1.0-0 \
    fonts-liberation \
    fonts-dejavu-core \
    fonts-noto-cjk \
    fontconfig \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python3.12 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["python", "server.py"]
```


## ☁️ Cloud Deployment

Luna Server can be deployed using Docker containers to various cloud platforms. The application includes a Dockerfile configured for production deployment.

## 🚀 Deployment Process

### **Manual Deployment**

1. **Build Docker Image:**
   ```bash
   docker build -t luna-server .
   ```

2. **Run Container:**
   ```bash
   docker run -d \
     --name luna-server \
     -p 8000:8000 \
     --env-file .env \
     luna-server
   ```

3. **Verify Deployment:**
   ```bash
   curl http://localhost:8000/health
   ```

---

This deployment guide covers the basic Docker-based deployment approach currently implemented for Luna Server. The containerized application can be deployed to various cloud platforms using standard container deployment methods.
