#!/bin/bash
# Universal startup script for SCAM API

echo "===== SCAM API STARTUP ====="
echo "Current directory: $(pwd)"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
echo "Start time: $TIMESTAMP"

# Check environment
echo "Checking environment..."
ENV_TYPE="unknown"
if [ -f "/.dockerenv" ]; then
    echo "Running in Docker environment"
    ENV_TYPE="docker"
elif [ "$RENDER" == "true" ]; then
    echo "Running on Render platform"
    ENV_TYPE="render"
else
    echo "Running in standard environment"
    ENV_TYPE="standard"
fi

# Ensure .env file exists with defaults
if [ ! -f ".env" ]; then
    echo "Creating default .env file"
    echo "TESSERACT_AVAILABLE=False" > .env
    echo "OCR_ENABLED=False" >> .env
fi

# Try to detect tesseract
if command -v tesseract &> /dev/null; then
    echo "Tesseract found in PATH:"
    tesseract --version
    echo "TESSERACT_AVAILABLE=True" > .env
    echo "OCR_ENABLED=True" >> .env
else
    echo "Tesseract not found in PATH"
    if [ "$ENV_TYPE" == "docker" ]; then
        echo "In Docker environment - Tesseract should be installed"
        echo "Attempting workaround..."
        for path in /usr/bin/tesseract /usr/local/bin/tesseract; do
            if [ -f "$path" ] && [ -x "$path" ]; then
                echo "Found Tesseract at $path"
                echo "TESSERACT_CMD=$path" >> .env
                echo "TESSERACT_AVAILABLE=True" > .env
                echo "OCR_ENABLED=True" >> .env
            fi
        done
    fi
fi

# On Render, try to run the installer if not in Docker
if [ "$ENV_TYPE" == "render" ] && [ "$ENV_TYPE" != "docker" ]; then
    echo "On Render but not in Docker - attempting to install Tesseract"
    bash ./render_install_tesseract.sh
fi

# Start the application
echo "Starting application..."
if [ "$PORT" == "" ]; then
    export PORT=10000
    echo "PORT not set, defaulting to $PORT"
fi

# Source .env file if it exists
if [ -f ".env" ]; then
    echo "Loading environment from .env file"
    source .env
fi

echo "Environment loaded:"
echo "TESSERACT_AVAILABLE: $TESSERACT_AVAILABLE"
echo "OCR_ENABLED: $OCR_ENABLED"
echo "Starting gunicorn server on port $PORT"
gunicorn --bind 0.0.0.0:$PORT --workers=2 --timeout=120 wsgi:app --log-level=debug
