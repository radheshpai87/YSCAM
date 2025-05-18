#!/usr/bin/env bash
# build.sh
set -o errexit

# This script runs in both Docker and non-Docker environments
# We use OCR API so no need to check for Tesseract

echo "Setting up lightweight OCR environment..."

# Create environment file with correct settings
echo "OCR_ENABLED=True" > .env
echo "OCR_API_KEY=${OCR_API_KEY:-K87589515488957}" >> .env

# Create OCR cache directory
mkdir -p ocr_cache
echo "Created OCR cache directory"

# Echo Python version for logs
python --version

echo "Build completed successfully"
exit 0
