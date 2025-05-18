#!/bin/bash
# Simple build script that installs Tesseract if not in Docker
# This is used as a fallback if Docker deployment fails

echo "===== NON-DOCKER FALLBACK BUILD SCRIPT ====="
echo "Current directory: $(pwd)"
echo "Checking if running on Render platform"

# If not in Docker, we need to install Tesseract directly
echo "Installing Tesseract OCR directly since Docker mode may not be used..."

# Try apt-get if we have sudo
if command -v sudo &> /dev/null && command -v apt-get &> /dev/null; then
    echo "Using apt-get to install Tesseract"
    sudo apt-get update
    sudo apt-get install -y tesseract-ocr tesseract-ocr-eng libtesseract-dev
    
    # Verify installation
    if command -v tesseract &> /dev/null; then
        echo "Tesseract installed successfully:"
        tesseract --version
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
