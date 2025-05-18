#!/usr/bin/env python3
"""Simple OCR test script for Render"""

import sys
import os
import logging
import subprocess
from PIL import Image, ImageDraw, ImageFont

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ocr-test")

def create_test_image(text="Testing Tesseract OCR"):
    """Create a test image with text"""
    img = Image.new('RGB', (400, 200), color='white')
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    draw.text((50, 50), text, fill='black', font=font)
    return img

def check_tesseract():
    """Check if Tesseract is available"""
    # Check environment variable
    if os.environ.get("TESSERACT_AVAILABLE") == "True":
        print("TESSERACT_AVAILABLE environment variable is True")
    
    # Try to run tesseract command
    try:
        result = subprocess.run(['tesseract', '--version'], 
                             stdout=subprocess.PIPE, 
                             stderr=subprocess.PIPE, 
                             text=True)
        if result.returncode == 0:
            print(f"Tesseract binary found: {result.stdout.strip()}")
            return True
        else:
            print(f"Tesseract binary check failed: {result.stderr.strip()}")
    except Exception as e:
        print(f"Error running tesseract command: {e}")
    
    # Try pytesseract
    try:
        import pytesseract
        version = pytesseract.get_tesseract_version()
        print(f"pytesseract reports Tesseract version: {version}")
        return True
    except Exception as e:
        print(f"pytesseract error: {e}")
    
    print("Tesseract not found")
    return False

def test_ocr():
    """Run basic OCR test"""
    # Create test image
    print("Creating test image...")
    image = create_test_image("SCAM Detection OCR Test")
    image.save("ocr_test_image.png")
    print("Test image saved as ocr_test_image.png")
    
    # Check if tesseract is available
    if not check_tesseract():
        print("Tesseract not available, OCR test will fail")
        return False
    
    # Try OCR
    try:
        import pytesseract
        print("Running OCR on test image...")
        text = pytesseract.image_to_string(image)
        print(f"OCR result: {text}")
        
        if text and text.strip():
            print("OCR successful!")
            return True
        else:
            print("OCR did not detect any text")
            return False
            
    except Exception as e:
        print(f"OCR test failed: {e}")
        return False

if __name__ == "__main__":
    print("=== OCR TEST SCRIPT ===")
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    print(f"In Docker: {os.path.exists('/.dockerenv')}")
    
    # Check environment variables
    for var in ["TESSERACT_AVAILABLE", "OCR_ENABLED", "DOCKER_DEPLOYMENT", "PATH"]:
        print(f"{var}: {os.environ.get(var, 'Not set')}")
    
    # Run test
    success = test_ocr()
    sys.exit(0 if success else 1)
