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

# Function to check for Tesseract - can be called multiple times if needed
def check_tesseract_availability():
    """
    Comprehensive check for Tesseract OCR availability using multiple detection methods
    
    Returns:
        bool: True if Tesseract is available, False otherwise
    """
    global OCR_METRICS
    
    # Record current time for performance tracking
    start_time = time.time()
    
    # Check for explicit environment settings (highest priority)
    env_setting = os.getenv('TESSERACT_AVAILABLE', '').lower() == 'true'
    ocr_enabled = os.getenv('OCR_ENABLED', '').lower() != 'false'  # Default to True unless explicitly set to false
    
    # Update metrics with environment checks
    OCR_METRICS["env_checks"] = {
        "env_var": os.getenv('TESSERACT_AVAILABLE', 'Not set'),
        "ocr_enabled": os.getenv('OCR_ENABLED', 'Not set'),
        "docker_marker": os.path.exists('/.dockerenv') or os.getenv('DOCKER_DEPLOYMENT') == 'True',
        "tesseract_cmd": os.getenv('TESSERACT_CMD', 'Not set')
    }
    
    # If OCR is explicitly disabled, don't even try
    if ocr_enabled is False:
        logger.info("OCR is explicitly disabled via OCR_ENABLED=False")
        return False
    
    # Method 1: Look for explicit Tesseract path in environment
    custom_path = os.getenv('TESSERACT_CMD')
    if custom_path and os.path.exists(custom_path) and os.access(custom_path, os.X_OK):
        OCR_METRICS["tesseract_path"] = custom_path
        logger.info(f"Found custom Tesseract path: {custom_path}")
        
        # Try to use this path with pytesseract
        try:
            import pytesseract
            pytesseract.pytesseract.tesseract_cmd = custom_path
            version = pytesseract.get_tesseract_version()
            OCR_METRICS["tesseract_version"] = str(version)
            OCR_METRICS["import_success"] = True
            logger.info(f"Tesseract verified via custom path: version {version}")
            return True
        except Exception as e:
            logger.warning(f"Custom Tesseract path exists but pytesseract failed: {e}")
    
    # Method 2: Try to import and check pytesseract with system default
    try:
        import pytesseract
        version = pytesseract.get_tesseract_version()
        OCR_METRICS["tesseract_version"] = str(version)
        OCR_METRICS["tesseract_path"] = pytesseract.pytesseract.tesseract_cmd
        OCR_METRICS["import_success"] = True
        logger.info(f"Tesseract found via pytesseract import: version {version}")
        return True
    except Exception as e:
        OCR_METRICS["pytesseract_error"] = str(e)
        logger.warning(f"Could not verify Tesseract via pytesseract: {e}")
    
    # Method 3: Check common binary locations directly
    tesseract_paths = [
        'tesseract',  # System PATH
        '/usr/bin/tesseract',
        '/usr/local/bin/tesseract',
        '/app/bin/tesseract'
    ]
    
    for path in tesseract_paths:
        try:
            import subprocess
            logger.info(f"Checking for Tesseract binary at: {path}")
            result = subprocess.run([path, '--version'], capture_output=True, text=True, check=False, timeout=5)
            
            if result.returncode == 0:
                OCR_METRICS["binary_check"] = f"Success at {path}: {result.stdout.strip()}"
                logger.info(f"Tesseract binary found at {path}: {result.stdout.strip()}")
                
                # Try to configure pytesseract with this path
                try:
                    import pytesseract
                    pytesseract.pytesseract.tesseract_cmd = path
                    version = pytesseract.get_tesseract_version()
                    OCR_METRICS["tesseract_version"] = str(version)
                    OCR_METRICS["tesseract_path"] = path
                    OCR_METRICS["import_success"] = True
                    
                    # Write this successful path to .env file for future use
                    try:
                        with open(".env", "a") as env_file:
                            env_file.write(f"\nTESSERACT_CMD={path}")
                    except:
                        pass  # Ignore if we can't update .env
                        
                    return True
                except Exception as config_error:
                    OCR_METRICS["config_error"] = str(config_error)
                    logger.warning(f"Found Tesseract binary at {path} but pytesseract config failed: {config_error}")
                    # Continue with other methods
        except Exception as binary_error:
            OCR_METRICS[f"binary_error_{path}"] = str(binary_error)
            # Continue trying other paths
    
    # Method 4: Check for installed package via package manager
    try:
        import subprocess
        logger.info("Checking for Tesseract via dpkg")
        result = subprocess.run(['dpkg', '-l', 'tesseract-ocr'], capture_output=True, text=True, check=False, timeout=5)
        
        if result.returncode == 0 and 'ii' in result.stdout:
            OCR_METRICS["package_check"] = "Installed via dpkg"
            logger.info("Tesseract package is installed via dpkg")
            # Package exists but we already tried the common paths
    except:
        # dpkg might not exist or other issue, ignore this check
        pass
    
    # Method 5: Final fallback - trust environment variable if all else fails
    if env_setting:
        logger.info("Using environment variable TESSERACT_AVAILABLE=True despite detection failures")
        return True
        
    # Calculate and record detection duration
    detection_duration = time.time() - start_time
    OCR_METRICS["detection_duration"] = f"{detection_duration:.2f}s"
    
    logger.warning(f"Tesseract is NOT available in this environment (detection took {detection_duration:.2f}s)")
    return False

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
        """Extract text from an image using OCR with robust fallback mechanisms"""
        logger.info(f"Extracting text from image: {image_path}")
        global TESSERACT_AVAILABLE, OCR_METRICS
        
        # Update metrics
        OCR_METRICS["images_processed"] += 1
        
        try:
            # Open the image file first to at least get some basic info
            image = Image.open(image_path)
            width, height = image.size
            format_type = image.format
            mode = image.mode
            logger.info(f"Image opened successfully: {format_type} {width}x{height} ({mode})")
            
            # Try to check for Tesseract one last time (multiple detection methods)
            if not TESSERACT_AVAILABLE:
                logger.info("Performing one final Tesseract availability check")
                TESSERACT_AVAILABLE = check_tesseract_availability()

            # If OCR is explicitly disabled via environment variable, use fallback
            ocr_enabled = os.getenv('OCR_ENABLED', '').lower()
            if ocr_enabled == 'false':
                logger.info("OCR is explicitly disabled via OCR_ENABLED environment variable")
                TESSERACT_AVAILABLE = False
            
            # Prepare fallback response in case OCR fails
            fallback_response = (
                f"[Image analysis: {width}x{height} {format_type} image. "
                f"OCR text extraction unavailable or failed. "
                f"The system will analyze other content and metadata separately.]"
            )
            
            # If Tesseract is not available, use the fallback immediately
            if not TESSERACT_AVAILABLE:
                OCR_METRICS["fallback_used"] += 1
                logger.warning("Using fallback method for image processing (Tesseract not available)")
                return fallback_response
            
            # Try multiple OCR methods with increasing robustness
            logger.info("Attempting OCR with pytesseract...")
            
            try:
                # 1. Import pytesseract dynamically
                import pytesseract
                
                # 2. Prepare image for better OCR results
                if image.mode != 'RGB':
                    logger.info(f"Converting image from {image.mode} to RGB mode")
                    image = image.convert('RGB')
                
                # 3. Try the explicit Tesseract path from env var if set
                tesseract_path = os.getenv('TESSERACT_CMD')
                if tesseract_path:
                    logger.info(f"Using custom Tesseract path: {tesseract_path}")
                    pytesseract.pytesseract.tesseract_cmd = tesseract_path
                
                # 4. First OCR attempt with standard settings
                logger.info("Running first OCR attempt with standard settings")
                text = pytesseract.image_to_string(image, lang='eng')
                text = text.strip()
                
                # 5. If first attempt fails, try with different PSM modes
                if not text or len(text.strip()) < 10:
                    logger.info("First OCR attempt yielded little text, trying PSM mode 1")
                    text = pytesseract.image_to_string(image, config='--psm 1', lang='eng')
                    text = text.strip()
                    
                    # 6. Try with even more specialized settings if still no text
                    if not text or len(text.strip()) < 10:
                        logger.info("Second OCR attempt yielded little text, trying PSM mode 11")
                        text = pytesseract.image_to_string(image, config='--psm 11', lang='eng')
                        text = text.strip()
                
                # 7. Apply image enhancements and try one last time if still no text
                if not text or len(text.strip()) < 10:
                    logger.info("All standard attempts failed, trying with image enhancement")
                    
                    # Import enhancement modules
                    try:
                        from PIL import ImageEnhance, ImageFilter
                        
                        # Enhance contrast
                        enhancer = ImageEnhance.Contrast(image)
                        enhanced_image = enhancer.enhance(2.0)
                        
                        # Sharpen the image
                        enhanced_image = enhanced_image.filter(ImageFilter.SHARPEN)
                        
                        # Try OCR on enhanced image
                        text = pytesseract.image_to_string(enhanced_image, config='--psm 6', lang='eng')
                        text = text.strip()
                    except ImportError as ie:
                        logger.warning(f"Could not import enhancement tools: {ie}")
                
                # 8. Update metrics and return results
                if text and len(text.strip()) > 0:
                    OCR_METRICS["successful_extractions"] += 1
                    logger.info(f"OCR successful, extracted {len(text)} characters")
                    return text
                else:
                    logger.warning("All OCR attempts yielded no usable text")
                    OCR_METRICS["fallback_used"] += 1
                    return f"[This image ({width}x{height}, {format_type}) appears to contain no detectable text.]"
                    
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
