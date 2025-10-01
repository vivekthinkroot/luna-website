# Use Ubuntu 24.04 for latest LTS and better Python 3.12 support
FROM ubuntu:24.04

# Set working directory
WORKDIR /app

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

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

# Install WeasyPrint system dependencies as recommended in official docs
# Install packages for virtualenv installation with wheels support
RUN apt-get update && \
    apt-get install -y \
    libpango-1.0-0 \
    libharfbuzz0b \
    libpangoft2-1.0-0 \
    libharfbuzz-subset0 \
    fonts-liberation \
    fonts-dejavu-core \
    fonts-noto-cjk \
    fontconfig \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Configure fontconfig for better font handling
RUN fc-cache -fv

# Create and activate virtual environment
RUN python3.12 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV VIRTUAL_ENV="/opt/venv"

# Upgrade pip and install wheel
RUN pip install --upgrade pip setuptools wheel

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Ensure virtual environment is activated for the app user
ENV PATH="/opt/venv/bin:$PATH"
ENV VIRTUAL_ENV="/opt/venv"

# Expose port 8000
EXPOSE 8000

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["python", "server.py"]
