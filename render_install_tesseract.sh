#!/bin/bash
# Script to install Tesseract OCR on Render

echo "===== RENDER TESSERACT INSTALLER ====="
echo "Current directory: $(pwd)"
echo "User: $(whoami)"

# Check if we're running on Render
if [[ -z "$RENDER" ]]; then
    echo "Not running on Render platform, skipping."
    exit 0
fi

echo "Detected Render environment, attempting to install Tesseract"

# Try to install via apt-get (might not work without sudo)
if command -v apt-get &> /dev/null; then
    echo "Attempting installation via apt-get..."
    apt-get update && apt-get install -y tesseract-ocr tesseract-ocr-eng
    
    # Check if successful
    if command -v tesseract &> /dev/null; then
        echo "Tesseract successfully installed via apt-get!"
        tesseract --version
        echo "TESSERACT_AVAILABLE=True" > .env
        echo "OCR_ENABLED=True" >> .env
        exit 0
    else
        echo "apt-get installation failed."
    fi
fi

# Try using a pre-compiled binary as a fallback
echo "Attempting to download pre-compiled Tesseract binary..."
mkdir -p bin

# Download compiled tesseract binary
curl -L https://github.com/tesseract-ocr/tesseract/releases/download/5.3.0/tesseract-5.3.0-linux.tar.gz -o tesseract.tar.gz
if [[ -f tesseract.tar.gz ]]; then
    tar -xzf tesseract.tar.gz -C bin/
    chmod +x bin/tesseract
    
    # Check if extracted properly
    if [[ -x bin/tesseract ]]; then
        echo "Tesseract binary extracted"
        export PATH="$PATH:$(pwd)/bin"
        echo "PATH=$PATH" >> .env
        echo "TESSERACT_AVAILABLE=True" >> .env
        echo "OCR_ENABLED=True" >> .env
        echo "TESSERACT_CMD=$(pwd)/bin/tesseract" >> .env
        exit 0
    fi
fi

# If all methods fail, ensure application can still run
echo "All Tesseract installation methods failed."
echo "TESSERACT_AVAILABLE=False" > .env
echo "OCR_ENABLED=False" >> .env
echo "Setting up for OCR-less operation."
exit 0
