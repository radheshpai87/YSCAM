#!/bin/bash
# Script to verify Docker environment on Render

echo "======================================"
echo "DOCKER ENVIRONMENT VERIFICATION SCRIPT"
echo "======================================"

echo -e "\n1. SYSTEM INFO"
echo "--------------"
echo "Date: $(date)"
echo "Hostname: $(hostname)"
echo "OS: $(uname -a)"
echo "User: $(whoami)"

echo -e "\n2. ENVIRONMENT VARIABLES"
echo "-----------------------"
echo "PORT: $PORT"
echo "TESSERACT_AVAILABLE: $TESSERACT_AVAILABLE"
echo "PYTHONPATH: $PYTHONPATH"
echo "PATH: $PATH"

echo -e "\n3. TESSERACT VERIFICATION"
echo "------------------------"
echo "Tesseract binary path:"
which tesseract || echo "Tesseract binary not found"

echo "Tesseract version:"
tesseract --version || echo "Failed to get Tesseract version"

echo "Tesseract languages:"
tesseract --list-langs || echo "Failed to list Tesseract languages"

echo -e "\n4. PYTHON PACKAGES"
echo "-----------------"
pip list | grep -i "tesseract\|pillow\|pytesseract"

echo -e "\n5. FILESYSTEM"
echo "------------"
echo "Working directory: $(pwd)"
echo "Contents of /app:"
ls -la /app || echo "Failed to list /app directory"

echo "Models directory:"
ls -la /app/models || echo "Failed to list models directory"

echo -e "\n6. PYTHON TESSERACT TEST"
echo "----------------------"
python -c "
import sys
print('Python version:', sys.version)
try:
    import pytesseract
    print('Pytesseract version:', pytesseract.__version__)
    print('Tesseract path:', pytesseract.pytesseract.tesseract_cmd)
    print('Tesseract version:', pytesseract.get_tesseract_version())
    print('Tesseract test PASSED')
except Exception as e:
    print('Tesseract test FAILED:', str(e))
" || echo "Failed to run Python Tesseract test"

echo -e "\n======================================"
echo "VERIFICATION COMPLETE"
echo "======================================"
