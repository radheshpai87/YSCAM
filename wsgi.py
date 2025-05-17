#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
WSGI entry point for the SCAM Detection API
"""

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
