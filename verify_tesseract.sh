#!/bin/bash
# Script to verify Tesseract OCR installation

echo "==== Verifying Tesseract Installation ===="
echo "1. Checking binary:"
which tesseract
if [ $? -ne 0 ]; then
  echo "ERROR: Tesseract binary not found in PATH"
else
  echo "SUCCESS: Tesseract binary found"
fi

echo "2. Checking version:"
tesseract --version

echo "3. Checking available languages:"
tesseract --list-langs

echo "4. Checking if Python can access Tesseract:"
python -c "import pytesseract; print(f'Tesseract version via Python: {pytesseract.get_tesseract_version()}')"

echo "5. Testing image processing with a sample:"
# Create a simple test image with text
python -c '
from PIL import Image, ImageDraw, ImageFont
import pytesseract
import os

# Create a test image with text
img = Image.new("RGB", (200, 50), color=(255, 255, 255))
d = ImageDraw.Draw(img)
d.text((10,10), "Test Tesseract OCR", fill=(0,0,0))
img_path = "test_tesseract.png"
img.save(img_path)
print(f"Created test image: {img_path}")

# Try OCR on the test image
try:
    text = pytesseract.image_to_string(img)
    print(f"OCR Result: {text}")
    if "Test Tesseract OCR" in text:
        print("SUCCESS: OCR detected the text correctly")
    else:
        print("WARNING: OCR detected text but might not be accurate")
except Exception as e:
    print(f"ERROR: OCR failed with: {e}")

# Clean up
os.remove(img_path)
'

echo "==== Verification Complete ===="
