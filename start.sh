#!/bin/bash
# Lightweight startup script for SCAM API optimized for free tier

echo "===== SCAM API STARTUP - LIGHTWEIGHT MODE ====="
echo "Starting at $(date)"

# Quick environment check
ENV_TYPE="standard"
[ -f "/.dockerenv" ] && ENV_TYPE="docker"
[ "$RENDER" == "true" ] && ENV_TYPE="render"
echo "Environment: $ENV_TYPE"

# Create optimized .env file for free tier
echo "Setting up optimized configuration for free tier"
{
    echo "TESSERACT_AVAILABLE=True"
    echo "OCR_ENABLED=True"
    echo "LIGHTWEIGHT_OCR=true"
    echo "PYTHONUNBUFFERED=1"
    echo "GUNICORN_WORKERS=1"
    echo "GUNICORN_THREADS=2"
    echo "GUNICORN_TIMEOUT=30"
    echo "LOG_LEVEL=warning"
} > .env

# Quick check for tesseract (fast path)
if command -v tesseract &> /dev/null; then
    echo "Tesseract found"
    echo "TESSERACT_CMD=$(which tesseract)" >> .env
    echo "OCR_ENABLED=True" >> .env
else
    echo "Tesseract not immediately found"
    echo "OCR_ENABLED=False" >> .env
fi

# Set default port
[ -z "$PORT" ] && export PORT=10000

# Load and apply environment settings
source .env

# Print minimal config information
echo "TESSERACT_AVAILABLE: $TESSERACT_AVAILABLE"
echo "OCR_ENABLED: $OCR_ENABLED"
echo "LIGHTWEIGHT_OCR: $LIGHTWEIGHT_OCR"

# Use optimized gunicorn settings for free tier
echo "Starting optimized server on port $PORT"
WORKERS=${GUNICORN_WORKERS:-1}  # Default to 1 worker on free tier
THREADS=${GUNICORN_THREADS:-2}  # Use threading instead of multiple processes
TIMEOUT=${GUNICORN_TIMEOUT:-30} # Shorter timeout for better responsiveness
LOG_LEVEL=${LOG_LEVEL:-warning} # Less verbose logging

# Start server with optimized settings
gunicorn --bind 0.0.0.0:$PORT \
  --workers=$WORKERS \
  --threads=$THREADS \
  --timeout=$TIMEOUT \
  --log-level=$LOG_LEVEL \
  --preload \
  --max-requests=100 \
  --max-requests-jitter=10 \
  wsgi:app
