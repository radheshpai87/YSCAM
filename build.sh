#!/usr/bin/env bash
# build.sh
set -o errexit

# Install Tesseract OCR for image text extraction
apt-get update
apt-get install -y tesseract-ocr
apt-get install -y tesseract-ocr-eng

# Echo versions for logs
tesseract --version
python --version

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Download NLTK resources
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet'); nltk.download('omw-1.4');"

echo "Build completed successfully"
