#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test script for the lightweight OCR module
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test-lightweight-ocr")

def main():
    """
    Perform basic verification of the lightweight OCR environment
    """
    logger.info("=== Lightweight OCR Test ===")
    
    # Check if the OCR is enabled in environment
    ocr_enabled = os.getenv("OCR_ENABLED", "False").lower() == "true"
    logger.info(f"OCR_ENABLED: {ocr_enabled}")
    
    # Check for the environment marker file
    has_marker = os.path.exists("/lightweight_ocr_enabled")
    logger.info(f"Marker file exists: {has_marker}")
    
    # Import the lightweight OCR module and check its availability
    try:
        import lightweight_ocr
        logger.info(f"Successfully imported lightweight_ocr module: {lightweight_ocr.__file__}")
        logger.info(f"OCR module version: {getattr(lightweight_ocr, '__version__', 'undefined')}")
        logger.info("Lightweight OCR configuration appears valid")
    except ImportError as e:
        logger.error(f"Failed to import lightweight_ocr module: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        logger.info("Lightweight OCR test completed successfully")
        sys.exit(0)
    else:
        logger.error("Lightweight OCR test failed")
        sys.exit(1)
