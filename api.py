#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, request, jsonify
import pickle
import numpy as np
import time
import os
from detect_message import load_model, has_high_risk_signals, get_prediction
import logging
import sys
from document_processor import get_document_text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("api.log")
    ]
)
logger = logging.getLogger("scam-api")

# Initialize Flask app
app = Flask(__name__)

# Enable CORS for API access with specific configuration
from flask_cors import CORS
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# Global variables to store model and vectorizer
model = None
vectorizer = None

def initialize_models():
    """Initialize models on startup"""
    global model, vectorizer
    
    logger.info("Initializing logistic regression model")
    
    try:
        model_path = f"models/logistic_regression_model.pkl"
                
        if not os.path.exists(model_path):
            logger.error(f"Model file does not exist: {model_path}")
            logger.error(f"Working directory: {os.getcwd()}")
            logger.error(f"Files in models directory: {os.listdir('models')}")
            return False
        
        logger.info(f"Loading model from: {model_path}")
        model, vectorizer = load_model(model_path)
                
        # Validate that we have what we need
        if model is None:
            logger.error(f"Failed to load model: {model_path}")
            return False
        if vectorizer is None:
            logger.error("Vectorizer not available")
            return False
                
        logger.info("Logistic regression model successfully loaded")
        logger.info(f"Using vectorizer: {vectorizer is not None}")
        return True
    except Exception as e:
        logger.error(f"Error initializing models: {str(e)}", exc_info=True)
        return False

@app.route('/health', methods=['GET', 'HEAD'])
def health():
    """Health check endpoint"""
    return jsonify({
        "service": "SCAM Detection API",
        "status": "ok",
        "timestamp": time.time()
    })

@app.route('/ocr-status', methods=['GET'])
def ocr_status():
    """Checks Tesseract OCR availability and status"""
    import os
    from document_processor import TESSERACT_AVAILABLE
    
    # Try to import and test pytesseract directly
    tesseract_version = "Not available"
    test_output = "Failed"
    
    try:
        import pytesseract
        tesseract_version = str(pytesseract.get_tesseract_version())
        test_output = "Successful"
    except Exception as e:
        test_output = f"Failed: {str(e)}"
    
    # Check for tesseract binary
    tesseract_binary = "Not found"
    try:
        import subprocess
        result = subprocess.run(['which', 'tesseract'], 
                           capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            tesseract_binary = result.stdout.strip()
        else:
            tesseract_binary = "Not found in PATH"
    except Exception as e:
        tesseract_binary = f"Error checking: {str(e)}"
    
    return jsonify({
        "ocr_status": {
            "tesseract_available": TESSERACT_AVAILABLE,
            "tesseract_version": tesseract_version,
            "tesseract_binary": tesseract_binary,
            "test_import": test_output,
            "env_var": os.getenv('TESSERACT_AVAILABLE', 'Not set')
        },
        "timestamp": time.time()
    })

@app.route('/', methods=['GET', 'HEAD'])
def root():
    """Root endpoint for health checks"""
    return jsonify({
        "service": "SCAM Detection API",
        "status": "ok",
        "timestamp": time.time()
    })

@app.route('/detect', methods=['POST'])
def detect_scam():
    """Main endpoint for scam detection"""
    try:
        # Get request data
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided. Please send JSON with 'message' field or file data."}), 400
        
        # Extract message from text or document
        message = None
        
        # Case 1: Direct text message
        if 'message' in data:
            message = data['message']
            logger.info(f"Processing text message: {message[:50]}...")
        
        # Case 2: File content as base64
        elif 'file_content' in data and 'file_type' in data:
            import base64
            
            try:
                file_content = base64.b64decode(data['file_content'])
                file_type = data['file_type'].lower()
                logger.info(f"Processing file of type: {file_type}")
                
                # Extract text from the document
                message = get_document_text(file_content, file_type)
                
                if not message:
                    return jsonify({"error": f"Could not extract text from the {file_type} file."}), 400
                
                logger.info(f"Extracted text from {file_type}: {message[:50]}...")
            except Exception as e:
                logger.error(f"Error processing file: {str(e)}", exc_info=True)
                return jsonify({"error": f"Error processing file: {str(e)}"}), 400
        
        # No valid input provided
        if not message:
            return jsonify({"error": "No message or file provided. Please send JSON with 'message' field or file content."}), 400
        
        # Ensure model is initialized
        if model is None:
            logger.error("Model not initialized")
            return jsonify({"error": "Model not initialized. Please try again."}), 500
            
        # Log available resources
        logger.info("Using model: logistic_regression")
        logger.info(f"Vectorizer available: {vectorizer is not None}")
        
        # Check for high-risk signals
        risk_signals = has_high_risk_signals(message)
        
        # Get model prediction
        try:
            # Get prediction from logistic regression model
            label, confidence, important_features = get_prediction(model, message, vectorizer)
        except Exception as e:
            logger.error(f"Prediction error: {str(e)}", exc_info=True)
            return jsonify({"error": str(e)}), 500
        
        # Override prediction if high-risk signals are found and confidence is not high
        if risk_signals and label == "real" and confidence < 0.75:
            label = "scam"
            confidence = max(confidence, 0.85)  # Set minimum confidence to 85%
        
        # Prepare response
        response = {
            "message": message,
            "classification": label,
            "confidence": float(confidence),
            "confidence_percentage": f"{confidence:.2%}"
        }
        
        # Add high-risk signals if found
        if risk_signals:
            response["high_risk_signals"] = risk_signals
        
        # Add important features if available
        if important_features:
            # Convert numpy arrays to Python native types for JSON serialization
            formatted_features = [{
                "term": str(word),
                "indicator_type": "Scam indicator" if float(importance) > 0 else "Legitimate indicator",
                "weight": float(abs(importance))
            } for word, importance in important_features]
            
            response["important_features"] = formatted_features
            
            # Add explanation summary
            scam_indicators = [word for word, imp in important_features if float(imp) > 0]
            legitimate_indicators = [word for word, imp in important_features if float(imp) < 0]
            
            explanations = []
            if label == "scam" and scam_indicators:
                explanations.append(f"This message was classified as a scam primarily because it contains suspicious terms like: {', '.join(scam_indicators[:5])}")
                
                # Check for common scam patterns
                message_lower = message.lower()
                if any(term in message_lower for term in ["registration fee", "registration", "fee", "fees", "payment", "pay"]):
                    explanations.append("Requesting upfront payment or registration fees is a common tactic in job and loan scams.")
                
                if any(term in message_lower for term in ["free", "guarantee", "guaranteed", "immediate", "urgent", "today", "risk-free"]):
                    explanations.append("Promises of guaranteed or instant approvals are often used in loan scams.")
                
                if any(term in message_lower for term in ["lottery", "prize", "won", "winner", "selected", "lucky"]):
                    explanations.append("Claims about winning prizes or being specially selected are classic scam techniques.")
                
                if any(term in message_lower for term in ["aadhar", "pan", "kyc", "bank details", "card details", "otp", "password", "verify"]):
                    explanations.append("Requesting identity documents or financial information via messages is risky.")
                
                if any(term in message_lower for term in ["no interview", "without interview", "work from home", "earn from home"]):
                    explanations.append("Job offers without proper interviews or promising easy work-from-home income are often scams.")
            
            elif label == "real" and legitimate_indicators:
                explanations.append(f"This message was classified as legitimate primarily because it contains trusted terms like: {', '.join(legitimate_indicators[:5])}")
                
                if any(term in message.lower() for term in ["official", "portal", "verified", "customer service", "helpline"]):
                    explanations.append("The message references official channels or verified services.")
                
                if any(bank in message.lower() for bank in ["sbi", "hdfc", "icici", "axis", "pnb", "kotak", "rbi"]):
                    explanations.append("The message mentions established banking institutions.")
                
                if any(company in message.lower() for company in ["tcs", "infosys", "wipro", "cognizant", "tech mahindra"]):
                    explanations.append("The message mentions reputable companies.")
            
            response["explanations"] = explanations
            
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors gracefully"""
    return jsonify({
        "error": "Endpoint not found",
        "status": "error",
        "message": "The requested endpoint does not exist. Please check the API documentation."
    }), 404

if __name__ == "__main__":
    # Initialize models at startup
    success = initialize_models()
    
    if not success:
        logger.error("Failed to initialize models. API may not function correctly.")
        print("ERROR: Failed to initialize models. API may not function correctly.")
    else:
        logger.info("API ready with logistic regression model")
        print("API initialized successfully with logistic regression model")
    
    # Default to port 5000 but allow override from environment variable
    port = int(os.environ.get("PORT", 5000))
    
    # Run the Flask application
    app.run(host='0.0.0.0', port=port, debug=False)
