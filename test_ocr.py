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
from PIL import Image, ImageDraw, ImageFont
import tempfile
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ocr-test")

def create_test_image(text="Testing Tesseract OCR", size=(400, 200)):
    """Create a simple test image with text"""
    logger.info("Creating test image")
    
    # Create a white image
    img = Image.new('RGB', size, color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to use a system font or default to built-in
    try:
        # Try common system font paths
        font_paths = [
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',  # Linux
            '/System/Library/Fonts/Helvetica.ttc',              # macOS
            'C:\\Windows\\Fonts\\arial.ttf',                    # Windows
            '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',  # Common Linux
        ]
        
        font = None
        for path in font_paths:
            if os.path.exists(path):
                try:
                    font = ImageFont.truetype(path, 24)
                    break
                except Exception:
                    continue
        
        if font is None:
            # Use default
            font = ImageFont.load_default()
            
    except Exception as e:
        logger.warning(f"Could not load system font: {e}, using default")
        font = ImageFont.load_default()
    
    # Draw text
    text_width = draw.textlength(text, font=font) if hasattr(draw, 'textlength') else 300
    text_position = ((size[0] - text_width) // 2, size[1] // 2)
    draw.text(text_position, text, fill='black', font=font)
    
    # Save to a temporary file
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp:
        temp_path = temp.name
        img.save(temp_path)
        logger.info(f"Test image saved to {temp_path}")
    
    return temp_path

def test_tesseract():
    """Test if Tesseract OCR is working correctly"""
    logger.info("Starting Tesseract OCR test")
    results = {
        "tesseract_found": False,
        "import_success": False,
        "version": None,
        "cmd_path": None,
        "test_image_ocr": None,
        "extraction_success": False,
        "errors": []
    }
    
    # Step 1: Try to import pytesseract
    try:
        logger.info("Importing pytesseract")
        import pytesseract
        results["import_success"] = True
        
        # Step 2: Check tesseract version
        try:
            version = pytesseract.get_tesseract_version()
            results["version"] = str(version)
            results["tesseract_found"] = True
            results["cmd_path"] = pytesseract.pytesseract.tesseract_cmd
            logger.info(f"Tesseract version: {version}")
        except Exception as e:
            error_msg = f"Error getting Tesseract version: {str(e)}"
            results["errors"].append(error_msg)
            logger.error(error_msg)
            
            # Try to use system command to locate tesseract
            try:
                import subprocess
                process = subprocess.run(['which', 'tesseract'], 
                                        capture_output=True, text=True, check=False)
                if process.returncode == 0:
                    tesseract_path = process.stdout.strip()
                    logger.info(f"Found tesseract at: {tesseract_path}")
                    results["cmd_path"] = tesseract_path
                    pytesseract.pytesseract.tesseract_cmd = tesseract_path
                    results["tesseract_found"] = True
            except Exception as e2:
                results["errors"].append(f"Failed to locate tesseract: {str(e2)}")
    except ImportError as e:
        error_msg = f"Failed to import pytesseract: {str(e)}"
        results["errors"].append(error_msg)
        logger.error(error_msg)
        return results
    
    # Step 3: Test OCR with a generated image
    if results["tesseract_found"]:
        try:
            # Create test image
            test_image_path = create_test_image()
            
            # Try OCR on the image
            logger.info("Running OCR on test image")
            text = pytesseract.image_to_string(Image.open(test_image_path))
            results["test_image_ocr"] = text.strip()
            
            # Check if text was successfully extracted
            if "Testing Tesseract OCR" in text:
                results["extraction_success"] = True
                logger.info("OCR test successful! Text was correctly extracted.")
            else:
                logger.warning(f"OCR test partial success. Expected 'Testing Tesseract OCR' but got: {text}")
            
            # Clean up
            try:
                os.unlink(test_image_path)
            except:
                pass
            
        except Exception as e:
            error_msg = f"Error during OCR test: {str(e)}"
            results["errors"].append(error_msg)
            logger.error(error_msg)
    
    return results

def check_system_config():
    """Check system configuration for OCR dependencies"""
    logger.info("Checking system configuration")
    results = {
        "system_info": {},
        "tesseract_check": {},
        "python_packages": {},
        "environment_vars": {}
    }
    
    # System info
    try:
        import platform
        results["system_info"] = {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "processor": platform.processor(),
            "architecture": platform.architecture(),
            "python_version": platform.python_version()
        }
    except Exception as e:
        results["system_info"]["error"] = str(e)
    
    # Check for Tesseract binary
    try:
        import subprocess
        process = subprocess.run(['tesseract', '--version'], 
                               capture_output=True, text=True, check=False)
        results["tesseract_check"]["binary_found"] = (process.returncode == 0)
        results["tesseract_check"]["version_output"] = process.stdout if process.returncode == 0 else process.stderr
        
        # Check for Tesseract languages
        if results["tesseract_check"]["binary_found"]:
            lang_process = subprocess.run(['tesseract', '--list-langs'],
                                       capture_output=True, text=True, check=False)
            results["tesseract_check"]["languages"] = lang_process.stdout.strip().split("\n")[1:]  # Skip header line
    except Exception as e:
        results["tesseract_check"]["error"] = str(e)
    
    # Python packages
    try:
        import pkg_resources
        packages_to_check = ['pytesseract', 'Pillow', 'numpy', 'flask', 'gunicorn']
        for package in packages_to_check:
            try:
                version = pkg_resources.get_distribution(package).version
                results["python_packages"][package] = version
            except pkg_resources.DistributionNotFound:
                results["python_packages"][package] = "Not installed"
    except Exception as e:
        results["python_packages"]["error"] = str(e)
    
    # Environment variables
    env_vars_to_check = ['TESSERACT_AVAILABLE', 'PATH', 'PYTHONPATH', 'PORT']
    for var in env_vars_to_check:
        results["environment_vars"][var] = os.environ.get(var, "Not set")
    
    return results

if __name__ == "__main__":
    print("=== Tesseract OCR Test Script ===")
    
    # Run tests
    ocr_results = test_tesseract()
    system_config = check_system_config()
    
    # Combine results
    all_results = {
        "ocr_test": ocr_results,
        "system_config": system_config,
        "timestamp": __import__('datetime').datetime.now().isoformat()
    }
    
    # Output as JSON
    print(json.dumps(all_results, indent=2))
    
    # Summary
    print("\n=== Test Summary ===")
    if ocr_results["extraction_success"]:
        print("✅ OCR TEST PASSED: Tesseract is working correctly")
    elif ocr_results["tesseract_found"]:
        print("⚠️ OCR TEST PARTIAL: Tesseract found but text extraction failed")
    else:
        print("❌ OCR TEST FAILED: Tesseract not found or not working")
    
    # Save results to file for debugging
    with open('ocr_test_results.json', 'w') as f:
        json.dump(all_results, f, indent=2)
    print("\nDetailed results saved to ocr_test_results.json")
    
    # Exit with appropriate code
    sys.exit(0 if ocr_results["extraction_success"] else 1)
