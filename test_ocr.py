#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tesseract OCR Test Script for Render Environment

This script tests if Tesseract OCR is properly installed and working.
It creates a simple test image with text and tries to extract it.
"""

import sys
import os
import logging
import tempfile
import json
import subprocess
from PIL import Image, ImageDraw, ImageFont

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ocr-test")

def create_test_image(text="Testing Tesseract OCR", size=(400, 200)):
    """Create a simple test image with text"""
    logger.info(f"Creating test image with text: '{text}'")
    
    # Create a white image
    img = Image.new('RGB', size, color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to use a font, fall back to default if needed
    font = ImageFont.load_default()
    
    # Draw text in the center
    text_width = len(text) * 10  # Rough estimate of text width
    text_height = 20
    position = ((size[0] - text_width) / 2, (size[1] - text_height) / 2)
    
    # Draw black text
    draw.text(position, text, fill="black", font=font)
    
    return img

def check_tesseract_binary():
    """Check for Tesseract binary in various locations"""
    results = {}
    paths = ["tesseract", "/usr/bin/tesseract", "/usr/local/bin/tesseract"]
    
    for path in paths:
        try:
            proc = subprocess.run([path, "--version"], 
                                stdout=subprocess.PIPE, 
                                stderr=subprocess.PIPE,
                                text=True,
                                timeout=5)
            if proc.returncode == 0:
                results[path] = proc.stdout.strip()
            else:
                results[path] = f"Error: {proc.stderr.strip()}"
        except Exception as e:
            results[path] = f"Exception: {str(e)}"
    
    return results

def check_pytesseract_import():
    """Try to import pytesseract and get version"""
    result = {
        "importable": False,
        "version": None,
        "error": None
    }
    
    try:
        import pytesseract
        result["importable"] = True
        result["path"] = pytesseract.pytesseract.tesseract_cmd
        
        try:
            result["version"] = str(pytesseract.get_tesseract_version())
        except Exception as ve:
            result["version_error"] = str(ve)
            
    except Exception as e:
        result["error"] = str(e)
    
    return result

def test_ocr(image_path=None):
    """Test OCR functionality using a sample image"""
    results = {
        "system_info": {
            "python_version": sys.version,
            "env_vars": {
                "TESSERACT_AVAILABLE": os.environ.get("TESSERACT_AVAILABLE", "Not set"),
                "OCR_ENABLED": os.environ.get("OCR_ENABLED", "Not set"),
                "DOCKER_DEPLOYMENT": os.environ.get("DOCKER_DEPLOYMENT", "Not set"),
                "TESSERACT_CMD": os.environ.get("TESSERACT_CMD", "Not set"),
            },
            "in_docker": os.path.exists("/.dockerenv")
        },
        "tesseract_binary": check_tesseract_binary(),
        "pytesseract": check_pytesseract_import(),
        "ocr_test": {
            "success": False,
            "text": None,
            "error": None
        }
    }
    
    # Create test image if not provided
    test_image = None
    if not image_path:
        test_image = create_test_image("SCAM Detection OCR Test")
        # Save for inspection
        try:
            test_image.save("ocr_test_image.png")
            results["test_image"] = "ocr_test_image.png"
        except Exception as e:
            results["image_save_error"] = str(e)
    
    # Test OCR with pytesseract if available
    if results["pytesseract"]["importable"]:
        try:
            import pytesseract
            
            # Use the saved image or the provided path
            img = test_image if test_image else Image.open(image_path)
            
            # Try OCR
            text = pytesseract.image_to_string(img)
            results["ocr_test"]["text"] = text
            results["ocr_test"]["success"] = True
            
            # Try with different PSM modes if no text detected
            if not text.strip():
                results["ocr_test"]["detected_text"] = False
                for psm in [1, 6, 11]:
                    try:
                        alt_text = pytesseract.image_to_string(img, config=f'--psm {psm}')
                        if alt_text.strip():
                            results["ocr_test"][f"psm_{psm}_text"] = alt_text
                            results["ocr_test"]["detected_text"] = True
                            break
                    except:
                        pass
            else:
                results["ocr_test"]["detected_text"] = True
                
        except Exception as e:
            results["ocr_test"]["error"] = str(e)
    else:
        results["ocr_test"]["error"] = "pytesseract not importable"
    
    # Try to gather metrics from document_processor if available
    try:
        sys.path.append(os.getcwd())
        from document_processor import OCR_METRICS, TESSERACT_AVAILABLE
        results["document_processor"] = {
            "TESSERACT_AVAILABLE": TESSERACT_AVAILABLE,
            "OCR_METRICS": OCR_METRICS
        }
    except Exception as e:
        results["document_processor_error"] = str(e)
    
    return results

if __name__ == "__main__":
    logger.info("Starting OCR test script")
    
    # Run the tests
    results = test_ocr()
    
    # Print summary
    print("\n=== OCR TEST RESULTS ===")
    print(f"Python version: {results['system_info']['python_version'].split()[0]}")
    print(f"Docker container: {'Yes' if results['system_info']['in_docker'] else 'No'}")
    
    binary_found = any("version" in v and not v.startswith("Exception") and not v.startswith("Error") 
                      for k, v in results["tesseract_binary"].items())
    print(f"Tesseract binary found: {'Yes' if binary_found else 'No'}")
    
    pytesseract_ok = results["pytesseract"]["importable"]
    print(f"pytesseract importable: {'Yes' if pytesseract_ok else 'No'}")
    
    if pytesseract_ok and "version" in results["pytesseract"]:
        print(f"Tesseract version: {results['pytesseract']['version']}")
    
    ocr_successful = results["ocr_test"]["success"]
    print(f"OCR test success: {'Yes' if ocr_successful else 'No'}")
    
    if ocr_successful:
        text_detected = results["ocr_test"].get("detected_text", False)
        print(f"Text detected in image: {'Yes' if text_detected else 'No'}")
        
        if text_detected:
            print(f"Extracted text: {results['ocr_test']['text']}")
    else:
        print(f"OCR error: {results['ocr_test'].get('error', 'Unknown error')}")
    
    # Document processor status
    if "document_processor" in results:
        print(f"document_processor.TESSERACT_AVAILABLE: {results['document_processor']['TESSERACT_AVAILABLE']}")
    
    # Write complete results to JSON file
    try:
        with open("ocr_test_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        print("\nDetailed results written to: ocr_test_results.json")
        print("Test image saved as: ocr_test_image.png")
    except Exception as e:
        print(f"Failed to write results to file: {e}")
    
    # Exit with appropriate code
    sys.exit(0 if results["ocr_test"]["success"] else 1)
