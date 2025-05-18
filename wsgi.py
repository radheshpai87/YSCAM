#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
WSGI entry point for the SCAM Detection API
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("wsgi")

# Try to load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("Environment variables loaded from .env file")
except ImportError:
    logger.info("python-dotenv not installed, using system environment variables")

# Log environment information
logger.info(f"Starting application with Python {sys.version}")
logger.info(f"Working directory: {os.getcwd()}")
logger.info(f"OCR_ENABLED: {os.getenv('OCR_ENABLED', 'Not set')}")
logger.info(f"OCR_ENABLED: {os.getenv('OCR_ENABLED', 'Not set')}")
logger.info(f"DOCKER_DEPLOYMENT: {os.getenv('DOCKER_DEPLOYMENT', 'Not set')}")

# Import application components
from api import app, initialize_models, model, vectorizer
from file_api import register_file_blueprint

# Initialize model
success = initialize_models()
if not success:
    print("Failed to initialize models. API may not function correctly.")

# Register the file API blueprint
register_file_blueprint(app, model, vectorizer)

# This is the gunicorn entry point
if __name__ == "__main__":
    app.run(host='0.0.0.0')
