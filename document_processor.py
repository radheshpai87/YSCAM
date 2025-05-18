#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Document Processor for SCAM Detection

This module extracts text from various file formats (PDF, DOCX, images) 
for processing by the SCAM detection system.
"""

import os
import sys
import logging
import time
from PIL import Image
import docx
import fitz  # PyMuPDF
import tempfile
import shutil

# Try to load dotenv if available
try:
    from dotenv import load_dotenv
    # Load environment variables
    load_dotenv()
    print("Environment variables loaded from .env file")
except ImportError:
    # dotenv not available, just continue
    print("dotenv module not available, using direct environment variables")
    pass

# Initialize OCR metrics and availability flag
OCR_METRICS = {
    "tesseract_version": "Unknown",
    "tesseract_path": "Unknown",
    "binary_check": "Not run",
    "import_success": False,
    "last_error": None,
    "images_processed": 0,
    "successful_extractions": 0,
    "fallback_used": 0,
    "env_checks": {
        "env_var": os.getenv('TESSERACT_AVAILABLE', 'Not set'),
        "docker_marker": os.path.exists('/.dockerenv') or os.getenv('DOCKER_DEPLOYMENT') == 'True'
    }
}

# Default to False until we can verify Tesseract is available
TESSERACT_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Document processor initializing...")

# Function to check for Tesseract - optimized for performance
def check_tesseract_availability():
    """
    Lightweight check for Tesseract OCR availability
    
    Returns:
        bool: True if Tesseract is available, False otherwise
    """
    global OCR_METRICS
    
    # Prioritize environment variables for fast startup
    env_setting = os.getenv('TESSERACT_AVAILABLE', '').lower() == 'true'
    ocr_enabled = os.getenv('OCR_ENABLED', '').lower() != 'false'
    
    # Update basic metrics
    OCR_METRICS["env_checks"] = {
        "env_var": os.getenv('TESSERACT_AVAILABLE', 'Not set'),
        "ocr_enabled": os.getenv('OCR_ENABLED', 'Not set'),
        "lightweight": os.getenv('LIGHTWEIGHT_OCR', 'Not set')
    }
    
    # If OCR is explicitly disabled via environment
    if not ocr_enabled:
        return False
    
    # Fast path: if environment says it's available and we're in lightweight mode, trust it
    if env_setting and os.getenv('LIGHTWEIGHT_OCR', '').lower() == 'true':
        logger.info("Using environment setting for Tesseract availability (lightweight mode)")
        return True
        
    # Check provided tesseract path if available
    custom_path = os.getenv('TESSERACT_CMD')
    if custom_path and os.path.exists(custom_path):
        OCR_METRICS["tesseract_path"] = custom_path
        return True
    
    # Quick check for system tesseract
    try:
        import subprocess
        result = subprocess.run(['which', 'tesseract'], 
                             capture_output=True, text=True, check=False, timeout=2)
        if result.returncode == 0 and result.stdout.strip():
            OCR_METRICS["binary_check"] = f"Found at: {result.stdout.strip()}"
            return True
    except:
        pass
    
    # Final fallback to env var
    return env_setting

# Run the check at import time
TESSERACT_AVAILABLE = check_tesseract_availability()
logger.info(f"Initial Tesseract availability check: {TESSERACT_AVAILABLE}")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("document-processor")

class DocumentProcessor:
    """Class to process various document types and extract text"""
    
    def __init__(self):
        """Initialize the document processor"""
        self.supported_extensions = {
            # Document formats
            'pdf': self.extract_text_from_pdf,
            'docx': self.extract_text_from_docx,
            'doc': self.extract_text_from_docx,  # Will warn about limited support
            'txt': self.extract_text_from_txt,
            'rtf': self.extract_text_from_txt,  # Basic RTF support
            'odt': self.extract_text_from_docx,  # Try with docx parser
            
            # Image formats
            'jpg': self.extract_text_from_image,
            'jpeg': self.extract_text_from_image,
            'png': self.extract_text_from_image,
            'bmp': self.extract_text_from_image,
            'tiff': self.extract_text_from_image,
            'tif': self.extract_text_from_image,
            'gif': self.extract_text_from_image,
        }
    
    def process_file(self, file_path):
        """
        Process a file and extract text based on its extension
        
        Args:
            file_path: Path to the file
            
        Returns:
            str: Extracted text
            
        Raises:
            ValueError: If the file format is unsupported
            FileNotFoundError: If the file doesn't exist
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        _, ext = os.path.splitext(file_path)
        ext = ext.lower().strip('.')
        
        if ext not in self.supported_extensions:
            raise ValueError(f"Unsupported file format: {ext}")
        
        # Call the appropriate extraction method
        return self.supported_extensions[ext](file_path)
    
    def process_bytes(self, file_bytes, file_type):
        """
        Process file bytes and extract text based on specified type
        
        Args:
            file_bytes: Bytes of the file
            file_type: Type of the file (pdf, docx, jpg, etc.)
            
        Returns:
            str: Extracted text
        """
        if file_type not in self.supported_extensions:
            raise ValueError(f"Unsupported file format: {file_type}")
        
        # Write bytes to a temporary file
        with tempfile.NamedTemporaryFile(suffix=f'.{file_type}', delete=False) as temp_file:
            temp_file.write(file_bytes)
            temp_path = temp_file.name
        
        try:
            # Process the temporary file
            result = self.supported_extensions[file_type](temp_path)
        finally:
            # Clean up the temporary file
            os.unlink(temp_path)
        
        return result
    
    def extract_text_from_pdf(self, pdf_path):
        """Extract text from a PDF file"""
        logger.info(f"Extracting text from PDF: {pdf_path}")
        
        try:
            text = ""
            # Open the PDF
            with fitz.open(pdf_path) as pdf:
                # Extract text from each page
                for page in pdf:
                    text += page.get_text()
            
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            return ""
    
    def extract_text_from_docx(self, docx_path):
        """Extract text from a DOCX file"""
        logger.info(f"Extracting text from DOCX: {docx_path}")
        
        _, ext = os.path.splitext(docx_path)
        if ext.lower() == '.doc':
            logger.warning("DOC format has limited support. Consider converting to DOCX.")
        
        try:
            text = ""
            # Open the document
            doc = docx.Document(docx_path)
            # Extract text from paragraphs
            for para in doc.paragraphs:
                text += para.text + "\n"
            
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting text from DOCX: {e}")
            return ""
    
    def extract_text_from_image(self, image_path):
        """Extract text from an image using lightweight OCR with optimized performance"""
        logger.info(f"Extracting text from image: {image_path}")
        global TESSERACT_AVAILABLE, OCR_METRICS
        
        # Update metrics
        OCR_METRICS["images_processed"] += 1
        
        # Check if we should use lightweight mode for free Render instances
        lightweight_mode = os.getenv('LIGHTWEIGHT_OCR', 'true').lower() == 'true'
        
        try:
            # Open the image file to get basic info
            image = Image.open(image_path)
            width, height = image.size
            format_type = image.format
            mode = image.mode
            logger.info(f"Image opened: {format_type} {width}x{height}")
            
            # Quick check for Tesseract availability
            if not TESSERACT_AVAILABLE:
                TESSERACT_AVAILABLE = os.getenv('TESSERACT_AVAILABLE', '').lower() == 'true'
            
            # Prepare fallback response
            fallback_response = (
                f"[Image: {width}x{height} {format_type}. OCR unavailable.]"
            )
            
            # If Tesseract not available or explicitly disabled, return fallback
            if not TESSERACT_AVAILABLE or os.getenv('OCR_ENABLED', '').lower() == 'false':
                OCR_METRICS["fallback_used"] += 1
                return fallback_response
            
            try:
                # Import pytesseract
                import pytesseract
                
                # Process image - resize large images for better performance
                if width > 1000 or height > 1000:
                    # Calculate new size while maintaining aspect ratio
                    ratio = min(1000/width, 1000/height)
                    new_size = (int(width * ratio), int(height * ratio))
                    image = image.resize(new_size, Image.LANCZOS)
                    logger.info(f"Resized image to {new_size} for better performance")
                
                # Convert to RGB if needed
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                
                # Set tesseract path if specified
                tesseract_path = os.getenv('TESSERACT_CMD')
                if tesseract_path:
                    pytesseract.pytesseract.tesseract_cmd = tesseract_path
                
                # Optimized approach for lightweight mode (default on free tier)
                if lightweight_mode:
                    # Single optimized OCR attempt with balanced settings
                    logger.info("Using lightweight OCR mode")
                    text = pytesseract.image_to_string(
                        image, 
                        config='--psm 3 --oem 1 -l eng', 
                        timeout=10  # Add timeout to prevent hanging
                    )
                    text = text.strip()
                else:
                    # Standard approach with one retry
                    text = pytesseract.image_to_string(image, lang='eng')
                    text = text.strip()
                    
                    # If first attempt fails, try one alternative setting
                    if not text or len(text.strip()) < 10:
                        logger.info("First OCR attempt yielded little text, trying PSM mode 3")
                        text = pytesseract.image_to_string(image, config='--psm 3', lang='eng')
                        text = text.strip()
                
                # Update metrics and return results
                if text and len(text.strip()) > 0:
                    OCR_METRICS["successful_extractions"] += 1
                    logger.info(f"OCR successful, extracted {len(text)} characters")
                    return text
                else:
                    OCR_METRICS["fallback_used"] += 1
                    return f"[Image ({width}x{height}) contains no detectable text.]"
                    
            except Exception as ocr_error:
                # Log the specific OCR error for debugging
                logger.error(f"OCR extraction failed: {ocr_error}")
                OCR_METRICS["last_error"] = str(ocr_error)
                OCR_METRICS["fallback_used"] += 1
                return fallback_response
                
        except Exception as e:
            # Handle general image processing errors
            logger.error(f"Image processing error: {e}", exc_info=True)
            OCR_METRICS["last_error"] = str(e)
            return f"[Error processing image: {str(e)}]"

    def extract_text_from_txt(self, text_path):
        """Extract text from a plain text file or simple RTF file"""
        logger.info(f"Extracting text from text file: {text_path}")
        
        try:
            with open(text_path, 'r', encoding='utf-8', errors='replace') as f:
                text = f.read()
                
            # For RTF files, do basic cleanup (remove RTF markup)
            if text_path.lower().endswith('.rtf'):
                # Very basic RTF cleanup - for better results consider using a proper RTF parser
                import re
                text = re.sub(r'[\\][a-z0-9]+\s?', ' ', text)  # Remove RTF commands
                text = re.sub(r'[\\][{}\']', '', text)  # Remove escaped braces and quotes
                text = re.sub(r'[{}]', '', text)  # Remove braces
                logger.info("Applied basic RTF markup removal")
                
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting text from text file: {e}")
            return ""


def get_document_text(file_path_or_bytes, file_type=None):
    """
    Helper function to extract text from various document types
    
    Args:
        file_path_or_bytes: Path to file or file bytes
        file_type: Optional type override for bytes input
        
    Returns:
        str: Extracted text
    """
    processor = DocumentProcessor()
    
    if isinstance(file_path_or_bytes, str):
        # Input is a file path
        return processor.process_file(file_path_or_bytes)
    else:
        # Input is bytes, file_type must be provided
        if file_type is None:
            raise ValueError("file_type must be provided when processing bytes")
        return processor.process_bytes(file_path_or_bytes, file_type)


if __name__ == "__main__":
    # Test the document processor
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        processor = DocumentProcessor()
        try:
            text = processor.process_file(file_path)
            print(f"Extracted text:\n{text[:500]}...")
            print(f"\nTotal length: {len(text)} characters")
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("Usage: python document_processor.py <file_path>")
