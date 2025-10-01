#!/usr/bin/env python3
"""
Server entry point for Luna FastAPI application.
Runs the FastAPI app using uvicorn with development-friendly settings.
"""

import logging
import sys

import uvicorn

# Configure uvicorn to use our logger
logging.getLogger("uvicorn").handlers = []
logging.getLogger("uvicorn.access").handlers = []
logging.getLogger("uvicorn.error").handlers = []


def main():
    """Run the FastAPI application using uvicorn."""
    print("Starting Luna FastAPI application...")
    
    try:
        uvicorn.run(
            "api.app:app",
            host="0.0.0.0",
            port=8000,
            reload=False,  # Enable auto-reload for development
            log_level="info",
            access_log=False,  # Disable uvicorn's built-in access logging
            log_config=None,  # Use our custom logging configuration
        )
    except Exception as e:
        print(f"Failed to start server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
