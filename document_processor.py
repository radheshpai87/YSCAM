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
    "service": "Lightweight OCR Service",
    "api_available": True,
    "import_success": True,
    "last_error": None,
    "images_processed": 0,
    "successful_extractions": 0,
    "fallback_used": 0,
    "env_checks": {
        "env_var": os.getenv('OCR_API_KEY', 'Not set'),
        "docker_marker": os.path.exists('/.dockerenv') or os.getenv('DOCKER_DEPLOYMENT') == 'True'
    }
}

# Default to True for our lightweight API-based OCR
OCR_AVAILABLE = True

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Document processor initializing...")

# Function to check for Lightweight OCR availability 
def check_ocr_availability():
    """
    Check for OCR availability (now using Lightweight OCR API)
    
    Returns:
        bool: True if OCR is available, False otherwise
    """
    global OCR_METRICS
    
    # Always enabled with new lightweight OCR
    ocr_enabled = os.getenv('OCR_ENABLED', 'true').lower() != 'false'
    
    # Update basic metrics
    OCR_METRICS["env_checks"] = {
        "ocr_enabled": os.getenv('OCR_ENABLED', 'true'),
        "api_key": bool(os.getenv('OCR_API_KEY', '')),
        "lightweight": "true"
    }
    
    # If OCR is explicitly disabled via environment
    if not ocr_enabled:
        return False
    
    # Check if the lightweight OCR module is available
    try:
        import lightweight_ocr
        OCR_METRICS["import_success"] = True
        OCR_METRICS["service"] = "Lightweight OCR API"
        logger.info("Lightweight OCR module is available")
        return True
    except ImportError as e:
        OCR_METRICS["import_success"] = False
        OCR_METRICS["last_error"] = str(e)
        logger.warning(f"Lightweight OCR module import failed: {e}")
    
    # Final fallback - we should always have access to lightweight OCR
    return True

# Run the check at import time
OCR_AVAILABLE = check_ocr_availability()
logger.info(f"Initial OCR availability check: {OCR_AVAILABLE}")

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
        global OCR_AVAILABLE, OCR_METRICS
        
        # Update metrics
        OCR_METRICS["images_processed"] += 1
        
        try:
            # Check if OCR is explicitly disabled
            if os.getenv('OCR_ENABLED', '').lower() == 'false':
                OCR_METRICS["fallback_used"] += 1
                return f"[Image OCR is disabled by configuration]"
            
            # Import the lightweight OCR module
            try:
                import lightweight_ocr
                
                # Use the lightweight OCR API to extract text
                text = lightweight_ocr.extract_text_from_image(image_path)
                
                # Update metrics based on result
                if text and not text.startswith("[Image analysis:"):
                    OCR_METRICS["successful_extractions"] += 1
                    logger.info(f"OCR successful, extracted {len(text)} characters")
                else:
                    OCR_METRICS["fallback_used"] += 1
                    logger.warning("OCR yielded no text, using fallback")
                
                return text
                
            except ImportError as e:
                # Log the import error
                logger.error(f"Lightweight OCR module import failed: {e}")
                OCR_METRICS["last_error"] = str(e)
                OCR_METRICS["fallback_used"] += 1
                
                # Get basic image info for fallback
                image = Image.open(image_path)
                width, height = image.size
                format_type = image.format
                
                return f"[Image: {width}x{height} {format_type}. OCR module unavailable.]"
                
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
