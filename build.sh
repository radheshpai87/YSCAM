#!/usr/bin/env bash
# build.sh
set -o errexit

# This script runs in both Docker and non-Docker environments
# In Docker, Tesseract is installed by the Dockerfile
# For non-Docker, we need to check and handle appropriately

echo "Checking for Tesseract availability..."

# Check if we're in Docker (presence of marker file)
if [ -f "/tesseract_installed" ]; then
  echo "Running in Docker environment with Tesseract pre-installed"
  echo "TESSERACT_AVAILABLE=True" > .env
  tesseract --version
  exit 0
fi

# For non-Docker environments
if command -v tesseract >/dev/null 2>&1; then
  echo "Tesseract is already installed:"
  tesseract --version
  echo "TESSERACT_AVAILABLE=True" > .env
else
  echo "Tesseract is not available. Will configure application to use alternative processing."
  echo "TESSERACT_AVAILABLE=False" > .env
fi

# Echo Python version for logs
python --version

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Download NLTK resources
echo "Downloading NLTK resources..."
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet'); nltk.download('omw-1.4');"

# Create empty directory for temporary files if it doesn't exist
mkdir -p ./tmp

echo "Build completed successfully"
