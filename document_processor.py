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
except ImportError:
    # dotenv not available, just continue
    pass

# Check for Tesseract availability - read from environment or file
TESSERACT_AVAILABLE = os.getenv('TESSERACT_AVAILABLE', 'True').lower() != 'false'

# Additional metrics for diagnostics
OCR_METRICS = {
    "tesseract_version": "Unknown",
    "tesseract_path": "Unknown",
    "binary_check": "Not run",
    "import_success": False,
    "last_error": None,
    "images_processed": 0,
    "successful_extractions": 0,
    "fallback_used": 0
}

try:
    import pytesseract
    # Test if tesseract is actually accessible
    tesseract_version = pytesseract.get_tesseract_version()
    OCR_METRICS["tesseract_version"] = str(tesseract_version)
    OCR_METRICS["import_success"] = True
    print(f"Tesseract OCR detected, version: {tesseract_version}")
    
    # Check if tesseract binary is available in PATH
    tesseract_cmd = pytesseract.pytesseract.tesseract_cmd
    OCR_METRICS["tesseract_path"] = tesseract_cmd
    print(f"Tesseract command path: {tesseract_cmd}")
    
    # Try to execute tesseract directly using subprocess
    import subprocess
    try:
        result = subprocess.run(['tesseract', '--version'], 
                                capture_output=True, text=True, timeout=5)
        binary_output = result.stdout.strip()
        OCR_METRICS["binary_check"] = "Success: " + binary_output
        print(f"Tesseract binary check: {binary_output}")
    except Exception as sub_e:
        OCR_METRICS["binary_check"] = f"Failed: {str(sub_e)}"
        print(f"Could not execute tesseract binary: {sub_e}")
        TESSERACT_AVAILABLE = False
        
except (ImportError, Exception) as e:
    TESSERACT_AVAILABLE = False
    OCR_METRICS["import_success"] = False
    OCR_METRICS["last_error"] = str(e)
    print(f"Warning: Tesseract OCR not available: {e}")
    print("Image text extraction will be limited.")

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
        """Extract text from an image using OCR"""
        logger.info(f"Extracting text from image: {image_path}")
        global TESSERACT_AVAILABLE, OCR_METRICS
        
        # Update metrics
        OCR_METRICS["images_processed"] += 1
        
        # Open the image
        try:
            # Check Tesseract availability first with more detailed logging
            if not TESSERACT_AVAILABLE:
                logger.warning("Tesseract OCR is not available in this environment")
                try:
                    # Try to locate tesseract using multiple methods
                    import subprocess
                    # Method 1: Using 'which' command
                    result = subprocess.run(['which', 'tesseract'], 
                                           capture_output=True, text=True, check=False)
                    tesseract_path = result.stdout.strip()
                    
                    # Method 2: Try common system locations
                    if not tesseract_path:
                        common_paths = [
                            '/usr/bin/tesseract',
                            '/usr/local/bin/tesseract',
                            '/opt/homebrew/bin/tesseract',
                            '/app/bin/tesseract'
                        ]
                        for path in common_paths:
                            if os.path.exists(path) and os.access(path, os.X_OK):
                                tesseract_path = path
                                break
                    
                    if tesseract_path:
                        logger.info(f"Tesseract binary found at: {tesseract_path}")
                        # Try to update the pytesseract command path
                        try:
                            import pytesseract
                            pytesseract.pytesseract.tesseract_cmd = tesseract_path
                            logger.info("Updated pytesseract command path")
                            # Test if it works
                            tesseract_version = pytesseract.get_tesseract_version()
                            logger.info(f"Tesseract version: {tesseract_version}")
                            TESSERACT_AVAILABLE = True
                            OCR_METRICS["tesseract_path"] = tesseract_path
                            OCR_METRICS["tesseract_version"] = str(tesseract_version)
                        except Exception as e:
                            logger.error(f"Failed to update pytesseract command: {e}")
                            OCR_METRICS["last_error"] = str(e)
                    else:
                        logger.warning("Tesseract binary not found in any standard location")
                except Exception as e:
                    logger.error(f"Error checking for tesseract: {e}")
                    OCR_METRICS["last_error"] = str(e)
            
            # Open the image file
            image = Image.open(image_path)
            logger.info(f"Image opened successfully: {image.format} {image.size}")
            
            # If Tesseract is still not available, extract basic info about the image
            if not TESSERACT_AVAILABLE:
                width, height = image.size
                format_type = image.format
                mode = image.mode
                
                # Create a placeholder message with image metadata
                placeholder = (
                    f"[This is an image with dimensions {width}x{height} ({format_type}, {mode}). "
                    f"OCR text extraction is not available in this environment. "
                    f"The system will analyze the image metadata and any text you provide separately.]"
                )
                
                OCR_METRICS["fallback_used"] += 1
                logger.warning("Using fallback method for image processing (no OCR)")
                return placeholder
            
            # Check if tesseract is installed
            try:
                import pytesseract
                tesseract_version = pytesseract.get_tesseract_version()
                logger.info(f"Using Tesseract version: {tesseract_version}")
            except Exception as e:
                logger.error(f"Error getting Tesseract version: {e}")
                OCR_METRICS["last_error"] = str(e)
                
                # Fall back to system command to check tesseract
                try:
                    import subprocess
                    result = subprocess.run(['tesseract', '--version'], 
                                          capture_output=True, text=True, check=False)
                    if result.returncode == 0:
                        logger.info(f"Tesseract version from system: {result.stdout.strip()}")
                        
                        # Try to recover by setting the tesseract command path
                        which_result = subprocess.run(['which', 'tesseract'], 
                                              capture_output=True, text=True, check=False)
                        if which_result.returncode == 0:
                            tesseract_path = which_result.stdout.strip()
                            logger.info(f"Found tesseract at: {tesseract_path}")
                            pytesseract.pytesseract.tesseract_cmd = tesseract_path
                        else:
                            logger.error("Could not find tesseract path")
                            return "[OCR ERROR: Could not locate Tesseract executable]"
                    else:
                        logger.error(f"Tesseract not found: {result.stderr.strip()}")
                        return "[OCR ERROR: Tesseract not installed or not in PATH]"
                except Exception as sub_e:
                    logger.error(f"Failed to check tesseract version from system: {sub_e}")
                    OCR_METRICS["last_error"] = str(sub_e)
                    return "[OCR ERROR: Could not verify Tesseract installation]"
            
            # Convert to RGB mode if needed (some images have alpha channels)
            if image.mode != 'RGB':
                logger.info(f"Converting image from {image.mode} to RGB mode")
                image = image.convert('RGB')
                
            logger.info(f"Image ready for OCR: size={image.size}, mode={image.mode}")
            
            # Enhance image for better OCR results
            from PIL import ImageEnhance, ImageFilter
            
            # Apply image enhancements
            # 1. Increase contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)
            
            # 2. Sharpen the image
            image = image.filter(ImageFilter.SHARPEN)
            
            # Use pytesseract with explicit configuration
            logger.info("Performing OCR with Tesseract")
            try:
                # First attempt with standard settings
                text = pytesseract.image_to_string(
                    image,
                    config='--psm 6',  # Assume a single block of text
                    lang='eng'         # Use English language
                )
                
                text = text.strip()
                
                if not text or len(text) < 10:  # If no text or very little text was extracted
                    logger.warning(f"No or minimal text extracted from image. Trying with different settings.")
                    
                    # Try again with different settings for mixed content
                    text = pytesseract.image_to_string(
                        image,
                        config='--psm 1',  # Auto-detect orientation and script
                        lang='eng'
                    )
                    text = text.strip()
                    
                    # If still no text, try one more setting for sparse text
                    if not text or len(text) < 10:
                        logger.warning("Still minimal text. Trying with sparse text settings.")
                        text = pytesseract.image_to_string(
                            image,
                            config='--psm 11',  # Sparse text - Find as much text as possible
                            lang='eng'
                        )
                        text = text.strip()
                
                # Update metrics
                OCR_METRICS["successful_extractions"] += 1
                
                logger.info(f"Extracted text length: {len(text)}")
                if len(text) > 50:
                    logger.info(f"Sample text: {text[:50]}...")
                else:
                    logger.info(f"Full text: {text}")
                    
                # If still no text, provide a helpful message rather than empty string
                if not text:
                    text = "[OCR completed but no text was detected in this image]"
                    
                return text
                
            except Exception as ocr_e:
                logger.error(f"Error during OCR processing: {ocr_e}")
                OCR_METRICS["last_error"] = str(ocr_e)
                return f"[OCR ERROR: {str(ocr_e)}]"
                
        except Exception as e:
            logger.error(f"Error extracting text from image: {e}", exc_info=True)
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
