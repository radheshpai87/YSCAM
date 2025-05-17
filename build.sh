#!/usr/bin/env bash
# build.sh
set -o errexit

# Render uses Ubuntu, and we need to modify the approach for system packages
# Note: On Render, use their specific environment which should have tesseract pre-installed
# or we need to use a different approach to handle OCR

echo "Checking for Tesseract availability..."
if command -v tesseract >/dev/null 2>&1; then
  echo "Tesseract is already installed:"
  tesseract --version
else
  echo "Tesseract is not available. Will configure application to use alternative processing."
  # We'll handle the missing Tesseract in the code
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
