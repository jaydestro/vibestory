#!/usr/bin/env bash
"""
Startup script for VibeStory application
Starts the application using Gunicorn with Uvicorn workers
"""

# Ensure the script is being run in the correct environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "❌ This script must be run within a virtual environment"
    echo "Please activate your virtual environment and try again"
    exit 1
fi

# Set default values for environment variables if not already set
export PORT=${PORT:-8000}

# Print startup information
echo "🚀 Starting VibeStory application..."
echo "📱 Application will be available at: http://localhost:${PORT}"
echo "Press Ctrl+C to stop the server"

# Execute Gunicorn with Uvicorn worker
# -k uvicorn.workers.UvicornWorker: Use Uvicorn as the worker class
# -w 1: Number of worker processes (set to 1 for simplicity)
# -b 0.0.0.0:${PORT}: Bind to all interfaces on the specified port
# main:app: The application callable (FastAPI instance) is named "app" in the "main" module
exec gunicorn -k uvicorn.workers.UvicornWorker -w 1 -b 0.0.0.0:${PORT} main:app