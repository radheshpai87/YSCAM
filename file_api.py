#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
File Upload API Endpoints for SCAM Detection

This module extends the API with endpoints that handle file uploads for PDF, DOCX, and images.
"""

from flask import Blueprint, request, jsonify
import os
import logging
from document_processor import get_document_text
from detect_message import load_model, has_high_risk_signals, get_prediction

# Configure logging
logger = logging.getLogger("scam-api-file")

# Create a blueprint
file_blueprint = Blueprint('file_api', __name__)

# Store model references
model = None
vectorizer = None

def register_file_blueprint(app, loaded_model=None, loaded_vectorizer=None):
    """Register the file blueprint with the Flask app"""
    global model, vectorizer
    
    model = loaded_model
    vectorizer = loaded_vectorizer
    
    app.register_blueprint(file_blueprint)
    logger.info("File API blueprint registered")
    
    return True

@file_blueprint.route('/upload', methods=['POST'])
def upload_and_detect():
    """
    Upload endpoint for file-based scam detection
    
    Accepts multipart form data with a file and returns scam detection results
    """
    # Check if a file was uploaded
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    
    # Check if the file is empty
    if file.filename == '':
        return jsonify({"error": "Empty file name"}), 400
    
    # Get file extension
    _, ext = os.path.splitext(file.filename)
    ext = ext.lower().strip('.')
    
    # Check supported extensions
    supported_extensions = ['pdf', 'docx', 'doc', 'jpg', 'jpeg', 'png', 'bmp', 'tiff']
    if ext not in supported_extensions:
        return jsonify({
            "error": f"Unsupported file format. Supported formats: {', '.join(supported_extensions)}"
        }), 400
    
    # Process the file to extract text
    try:
        # Save file to temporary location first
        temp_path = f"temp_upload_{os.getpid()}.{ext}"
        file.save(temp_path)
        
        # Read file content
        with open(temp_path, 'rb') as f:
            file_content = f.read()
        
        # Delete temporary file
        os.remove(temp_path)
        
        # Extract text from the document
        text = get_document_text(file_content, ext)
        
        # Check if text extraction was successful
        if not text:
            logger.error(f"Failed to extract text from {file.filename} of type {ext}")
            return jsonify({
                "error": f"Could not extract text from the {ext} file.",
                "details": "The image may not contain readable text, or there might be issues with the OCR system. Try with a clearer image."
            }), 400
            
        # Check if we got the OCR not available placeholder
        if "[OCR not available in this environment]" in text:
            logger.warning(f"OCR not available for {file.filename} - providing limited functionality")
            
            # For image files, provide a special message
            if ext.lower() in ['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'tif', 'gif']:
                return jsonify({
                    "warning": "OCR is not available in this deployment environment",
                    "filename": file.filename,
                    "text": text,
                    "suggestion": "For image processing, please try using the direct text input instead, or use the command-line version with Tesseract installed."
                }), 200
        
        # Get model and vectorizer if not already loaded
        global model, vectorizer
        if model is None or vectorizer is None:
            logger.info("Loading model for file upload request")
            model, vectorizer = load_model("models/logistic_regression_model.pkl")
            
            if model is None or vectorizer is None:
                logger.error("Failed to load model or vectorizer")
                return jsonify({"error": "Failed to initialize model. Please try again."}), 500
        
        # Check for high-risk signals
        risk_signals = has_high_risk_signals(text)
        
        # Get model prediction
        label, confidence, important_features = get_prediction(model, text, vectorizer)
        
        # Override prediction if high-risk signals are found
        if risk_signals and label == "real" and confidence < 0.75:
            label = "scam"
            confidence = max(confidence, 0.85)
        
        # Prepare response
        response = {
            "filename": file.filename,
            "text": text,
            "classification": label,
            "confidence": float(confidence),
            "confidence_percentage": f"{confidence:.2%}"
        }
        
        # Add high-risk signals if found
        if risk_signals:
            response["high_risk_signals"] = risk_signals
            
        # Add important features if available
        if important_features:
            # Convert values to standard Python types for JSON serialization
            formatted_features = [{
                "term": str(word),
                "indicator_type": "Scam indicator" if float(importance) > 0 else "Legitimate indicator",
                "weight": float(abs(importance))
            } for word, importance in important_features]
            
            response["important_features"] = formatted_features
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error processing file upload: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500
