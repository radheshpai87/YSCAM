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
import pytesseract
import docx
import fitz  # PyMuPDF
import tempfile

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
        
        try:
            # Check if tesseract is installed
            tesseract_version = pytesseract.get_tesseract_version()
            logger.info(f"Using Tesseract version: {tesseract_version}")
            
            # Open the image
            image = Image.open(image_path)
            
            # Convert to RGB mode if needed (some images have alpha channels)
            if image.mode != 'RGB':
                logger.info(f"Converting image from {image.mode} to RGB mode")
                image = image.convert('RGB')
                
            logger.info(f"Image size: {image.size}, mode: {image.mode}")
            
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
            text = pytesseract.image_to_string(
                image,
                config='--psm 6',  # Assume a single block of text
                lang='eng'         # Use English language
            )
            
            text = text.strip()
            
            if not text:
                logger.warning(f"No text extracted from image. Trying with different settings.")
                # Try again with different settings
                text = pytesseract.image_to_string(
                    image,
                    config='--psm 1',  # Auto-detect orientation and script
                    lang='eng'
                )
                text = text.strip()
            
            logger.info(f"Extracted text length: {len(text)}")
            if len(text) > 50:
                logger.info(f"Sample text: {text[:50]}...")
            else:
                logger.info(f"Full text: {text}")
                
            return text
        except Exception as e:
            logger.error(f"Error extracting text from image: {e}", exc_info=True)
            return ""

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
