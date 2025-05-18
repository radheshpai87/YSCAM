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
    echo "OCR_ENABLED=True"
    echo "PYTHONUNBUFFERED=1"
    echo "GUNICORN_WORKERS=1"
    echo "GUNICORN_THREADS=2"
    echo "GUNICORN_TIMEOUT=30"
    echo "LOG_LEVEL=warning"
    # OCRSpace API key
    echo "OCR_API_KEY=${OCR_API_KEY:-K87589515488957}"
} > .env

# Ensure OCR cache directory exists
mkdir -p ocr_cache
echo "Created OCR cache directory"
echo "OCR_ENABLED=True" >> .env

# Ensure models directory exists
mkdir -p models
echo "Created models directory (if it doesn't exist)"

# Check if model file exists, if not train the model
if [ ! -f "models/logistic_regression_model.pkl" ]; then
    echo "Model not found, training now..."
    python train_model_docker.py
    if [ $? -ne 0 ]; then
        echo "ERROR: Model training failed. Please check the logs."
    else
        echo "Model trained and saved successfully."
    fi
else
    echo "Found existing trained model in models/logistic_regression_model.pkl"
fi

# Set default port
[ -z "$PORT" ] && export PORT=10000

# Load and apply environment settings
source .env

# Print minimal config information
echo "OCR_ENABLED: $OCR_ENABLED"
echo "OCR API Key configured: $(if [ -n "$OCR_API_KEY" ]; then echo "Yes"; else echo "No"; fi)"
echo "Using lightweight OCR API"

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
