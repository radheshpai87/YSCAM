#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Lightweight OCR module using OCRSpace API with fallback mechanisms
"""

import os
import time
import json
import logging
import base64
import hashlib
from io import BytesIO
from typing import Dict, Any, Optional, Tuple
import requests
from PIL import Image

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("lightweight-ocr")

# Constants for OCR services
# Use a placeholder key name that will be replaced with the actual key at runtime
DEFAULT_API_KEY = "OCRSAPCE_FREE_TIER_API_KEY"  # Will be set from environment variable
DEFAULT_API_ENDPOINT = "https://api.ocr.space/parse/image"
DEFAULT_LANGUAGE = "eng"
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ocr_cache")

# Create cache directory if it doesn't exist
os.makedirs(CACHE_DIR, exist_ok=True)

# Metrics for OCR usage
OCR_METRICS = {
    "api_calls": 0,
    "cache_hits": 0,
    "fallback_used": 0,
    "successful_extractions": 0,
    "errors": 0,
    "last_error": None,
}

def get_image_hash(image_path: str) -> str:
    """Generate a hash for an image file to use as cache key"""
    try:
        with open(image_path, "rb") as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
        return file_hash
    except Exception as e:
        logger.warning(f"Error generating image hash: {e}")
        # Fallback to filename-based hash
        return hashlib.md5(image_path.encode()).hexdigest()

def get_cached_result(image_hash: str) -> Optional[str]:
    """Check if OCR result is cached and return if available"""
    cache_file = os.path.join(CACHE_DIR, f"{image_hash}.json")
    
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r") as f:
                data = json.load(f)
                
            # Only use cache if it's not expired (default: 30 days)
            cache_ttl = int(os.getenv("OCR_CACHE_TTL_DAYS", "30"))
            if time.time() - data.get("timestamp", 0) < cache_ttl * 86400:
                OCR_METRICS["cache_hits"] += 1
                logger.info(f"OCR cache hit for {image_hash}")
                return data.get("text")
        except Exception as e:
            logger.warning(f"Error reading cache: {e}")
    
    return None

def save_to_cache(image_hash: str, text: str) -> None:
    """Save OCR result to cache"""
    cache_file = os.path.join(CACHE_DIR, f"{image_hash}.json")
    
    try:
        with open(cache_file, "w") as f:
            json.dump({
                "text": text,
                "timestamp": time.time()
            }, f)
    except Exception as e:
        logger.warning(f"Error saving to cache: {e}")

def get_image_info(image_path: str) -> Dict[str, Any]:
    """Get basic image information"""
    try:
        image = Image.open(image_path)
        return {
            "width": image.width,
            "height": image.height,
            "format": image.format,
            "mode": image.mode,
            "size_kb": round(os.path.getsize(image_path) / 1024, 2)
        }
    except Exception as e:
        logger.error(f"Error getting image info: {e}")
        return {
            "error": str(e)
        }

def extract_text_with_api(image_path: str) -> Tuple[bool, str]:
    """
    Extract text from image using OCRSpace API
    
    Args:
        image_path: Path to image file
        
    Returns:
        Tuple[bool, str]: (success, text)
    """
    api_key = os.getenv("OCR_API_KEY", DEFAULT_API_KEY)
    language = os.getenv("OCR_LANGUAGE", DEFAULT_LANGUAGE)
    
    # Check if API is disabled
    if os.getenv("OCR_API_DISABLED", "").lower() == "true":
        logger.info("OCR API is disabled by configuration")
        return False, "OCR API is disabled"
    
    # Check if image exists
    if not os.path.exists(image_path):
        logger.error(f"Image file not found: {image_path}")
        return False, "Image file not found"
        
    try:
        # Prepare image file
        with open(image_path, "rb") as f:
            image_data = f.read()
        
        # Check if image is too large (API limit is 1MB)
        max_size_mb = float(os.getenv("OCR_MAX_IMAGE_SIZE_MB", "1"))
        if len(image_data) > max_size_mb * 1024 * 1024:
            logger.warning(f"Image too large ({len(image_data)/1024/1024:.2f} MB), resizing")
            # Resize image to fit within limits
            image = Image.open(BytesIO(image_data))
            
            # Calculate new dimensions while maintaining aspect ratio
            ratio = (max_size_mb * 900000 / len(image_data)) ** 0.5  # Conservative estimate
            new_width = int(image.width * ratio)
            new_height = int(image.height * ratio)
            
            # Resize and convert to JPEG for better compression
            image = image.resize((new_width, new_height), Image.LANCZOS)
            buffer = BytesIO()
            image.save(buffer, format="JPEG", optimize=True, quality=85)
            image_data = buffer.getvalue()
            logger.info(f"Resized image to {new_width}x{new_height} ({len(image_data)/1024/1024:.2f} MB)")
        
        # Encode image as base64
        base64_image = base64.b64encode(image_data).decode("utf-8")
        
        # Determine the image format for mimetype
        img_format = "jpeg"  # Default to jpeg
        try:
            with Image.open(BytesIO(image_data)) as img:
                if img.format:
                    img_format = img.format.lower()
        except Exception:
            pass
            
        # Prepare payload - use file upload instead of base64
        files = {
            'file': ('image.' + img_format, image_data),
        }
        
        # Prepare data parameters
        data = {
            "language": language,
            "apikey": api_key,
            "isOverlayRequired": "false",
            "isCreateSearchablePdf": "false",
            "isSearchablePdfHideTextLayer": "false",
            "scale": "true",
            "detectOrientation": "true",
            "OCREngine": "2",  # Use the newer OCR engine
        }
        
        # Send request with timeout
        timeout = int(os.getenv("OCR_API_TIMEOUT", "30"))
        OCR_METRICS["api_calls"] += 1
        response = requests.post(
            DEFAULT_API_ENDPOINT,
            files=files,
            data=data,
            timeout=timeout
        )
        
        # Process response
        if response.status_code == 200:
            result = response.json()
            
            if result.get("IsErroredOnProcessing"):
                error = result.get("ErrorMessage", ["Unknown error"])[0]
                logger.error(f"API processing error: {error}")
                OCR_METRICS["errors"] += 1
                OCR_METRICS["last_error"] = error
                return False, f"API processing error: {error}"
            
            parsed_results = result.get("ParsedResults", [])
            if parsed_results:
                extracted_text = parsed_results[0].get("ParsedText", "")
                OCR_METRICS["successful_extractions"] += 1
                return True, extracted_text
            
            return False, "No text found in the image"
            
        else:
            error_msg = f"API request failed with status {response.status_code}: {response.text}"
            logger.error(error_msg)
            OCR_METRICS["errors"] += 1
            OCR_METRICS["last_error"] = error_msg
            return False, error_msg
            
    except requests.exceptions.Timeout:
        error_msg = f"API request timed out after {timeout} seconds"
        logger.error(error_msg)
        OCR_METRICS["errors"] += 1
        OCR_METRICS["last_error"] = error_msg
        return False, error_msg
        
    except Exception as e:
        error_msg = f"Error during OCR API request: {e}"
        logger.error(error_msg)
        OCR_METRICS["errors"] += 1
        OCR_METRICS["last_error"] = error_msg
        return False, error_msg

def extract_text_from_image(image_path: str) -> str:
    """
    Extract text from image with caching and fallback mechanisms
    
    Args:
        image_path: Path to image file
        
    Returns:
        str: Extracted text or fallback message
    """
    logger.info(f"Extracting text from image: {image_path}")
    
    # Get image information
    image_info = get_image_info(image_path)
    width = image_info.get("width", 0)
    height = image_info.get("height", 0)
    img_format = image_info.get("format", "unknown")
    
    # Generate hash for caching
    image_hash = get_image_hash(image_path)
    
    # Check cache first
    cached_text = get_cached_result(image_hash)
    if cached_text:
        return cached_text
    
    # Try API extraction
    success, text = extract_text_with_api(image_path)
    
    if success and text:
        # Save successful result to cache
        save_to_cache(image_hash, text)
        return text
    
    # If API fails or returns no text, use fallback
    OCR_METRICS["fallback_used"] += 1
    fallback_text = (
        f"[Image analysis: {width}x{height} {img_format} image. "
        f"No text detected or OCR service unavailable. "
        f"Image metadata has been analyzed instead.]"
    )
    
    return fallback_text

def ocr_status() -> Dict[str, Any]:
    """
    Get OCR service status and metrics
    
    Returns:
        Dict[str, Any]: Status information and metrics
    """
    return {
        "service": "Lightweight OCR Service",
        "api_endpoint": DEFAULT_API_ENDPOINT,
        "using_api_key": bool(os.getenv("OCR_API_KEY")),
        "language": os.getenv("OCR_LANGUAGE", DEFAULT_LANGUAGE),
        "cache_enabled": True,
        "cache_location": CACHE_DIR,
        "cache_entries": len(os.listdir(CACHE_DIR)) if os.path.exists(CACHE_DIR) else 0,
        "metrics": OCR_METRICS,
    }

# For direct testing
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        print(f"Testing OCR on {image_path}")
        
        text = extract_text_from_image(image_path)
        print(f"Extracted text:")
        print(text)
        
        print("\nOCR Status:")
        print(json.dumps(ocr_status(), indent=2))
    else:
        print("Usage: python lightweight_ocr.py <image_path>")
