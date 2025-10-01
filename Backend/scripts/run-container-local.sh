#!/bin/bash

# Simple Local Container Runner
# Runs the container with environment variables from .env file

set -e

CONTAINER_NAME="luna-dev-01"
IMAGE_NAME="luna-server:local"
PORT=8000

echo "🚀 Running Luna Server container locally..."

# Check if container already exists and remove it
if docker ps -a --format "table {{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
    echo "🗑️  Removing existing container: $CONTAINER_NAME"
    docker rm -f $CONTAINER_NAME > /dev/null 2>&1
fi

# Check if --rebuild flag is passed
REBUILD=false
if [[ "$1" == "--rebuild" ]]; then
    REBUILD=true
    echo "🔨 Force rebuild requested..."
fi

# Build the image if it doesn't exist or if rebuild is requested
if [[ "$REBUILD" == "true" ]] || ! docker images --format "table {{.Repository}}:{{.Tag}}" | grep -q "^${IMAGE_NAME}$"; then
    echo "🔨 Building Docker image..."
    echo "   This may take a few minutes on first build..."
    
    # Remove existing image if rebuilding
    if [[ "$REBUILD" == "true" ]]; then
        docker rmi $IMAGE_NAME > /dev/null 2>&1 || true
    fi
    
    if docker build -t $IMAGE_NAME .; then
        echo "✅ Docker image built successfully!"
    else
        echo "❌ Docker build failed!"
        exit 1
    fi
else
    echo "📦 Using existing Docker image: $IMAGE_NAME"
fi

# Run the container with JSON config
echo "🚀 Starting container..."
if [ -f luna-config.json ]; then
    echo "📄 Using luna-config.json for configuration"
    
    # Read the JSON config and convert localhost to host.docker.internal for Docker
    CONFIG_JSON=$(cat luna-config.json)
    
    # Check if config contains localhost and replace with host.docker.internal
    if echo "$CONFIG_JSON" | grep -q "localhost"; then
        echo "🔄 Converting localhost to host.docker.internal in config for Docker container..."
        DOCKER_CONFIG_JSON=$(echo "$CONFIG_JSON" | sed 's/localhost/host.docker.internal/g')
        docker run -d --name $CONTAINER_NAME -p $PORT:8000 -e LUNA_CONFIG_JSON="$DOCKER_CONFIG_JSON" $IMAGE_NAME
    else
        docker run -d --name $CONTAINER_NAME -p $PORT:8000 -e LUNA_CONFIG_JSON="$CONFIG_JSON" $IMAGE_NAME
    fi
else
    echo "⚠️  No luna-config.json file found. Running with minimal environment."
    echo "   Note: Some features may not work without proper configuration."
    docker run -d --name $CONTAINER_NAME -p $PORT:8000 $IMAGE_NAME
fi

# Wait a moment for container to start
sleep 2

CONTAINER_ID=$(docker ps --filter "name=$CONTAINER_NAME" --format "{{.ID}}")

if [ -n "$CONTAINER_ID" ]; then
    echo "✅ Container started successfully!"
    echo "   Container ID: $CONTAINER_ID"
    echo "   Health check: http://localhost:$PORT/health"
    echo "   Root endpoint: http://localhost:$PORT/"
    echo ""
    echo "🔍 View logs: docker logs $CONTAINER_NAME"
    echo "🛑 Stop container: docker stop $CONTAINER_NAME"
    echo "🗑️  Remove container: docker rm $CONTAINER_NAME"
    echo ""
    echo "💡 To rebuild the image, run: $0 --rebuild"
else
    echo "❌ Failed to start container"
    echo "🔍 Check container logs: docker logs $CONTAINER_NAME"
    exit 1
fi
