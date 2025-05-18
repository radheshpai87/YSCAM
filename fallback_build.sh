#!/bin/bash
# Simple build script that installs Tesseract if not in Docker
# This is used as a fallback if Docker deployment fails

echo "===== NON-DOCKER FALLBACK BUILD SCRIPT ====="
echo "Current directory: $(pwd)"
echo "Setting up lightweight OCR"

# We don't need Tesseract anymore, just set up our API-based OCR
echo "Setting up lightweight OCR API environment..."

# Create OCR cache directory
mkdir -p ocr_cache
echo "Created OCR cache directory"

# Set up environment variables
echo "Setting up OCR environment variables"
echo "OCR_ENABLED=True" > .env
echo "OCR_API_KEY=${OCR_API_KEY:-K87589515488957}" >> .env
        echo "TESSERACT_AVAILABLE=True" > .env
    else
        echo "Failed to install Tesseract with apt-get"
    fi
# Try different package managers as fallbacks
elif command -v brew &> /dev/null; then
    echo "Using Homebrew to install Tesseract"
    brew install tesseract
elif command -v yum &> /dev/null; then
    echo "Using yum to install Tesseract"
    sudo yum install -y tesseract
fi

# Create a .env file to configure application behavior
echo "Creating .env file"
echo "TESSERACT_AVAILABLE=$(command -v tesseract >/dev/null 2>&1 && echo 'True' || echo 'False')" > .env

echo "===== BUILD SCRIPT COMPLETED ====="
