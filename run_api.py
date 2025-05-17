#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import argparse

def run_development():
    """Run the API in development mode using Flask's built-in server"""
    from api import app, initialize_models, model, vectorizer
    from file_api import register_file_blueprint
    
    # Initialize model
    success = initialize_models()
    if not success:
        print("Failed to initialize models. API may not function correctly.")
        return
    
    # Register the file API blueprint
    register_file_blueprint(app, model, vectorizer)
    
    # Get port from environment or use default
    port = int(os.environ.get("PORT", 5000))
    
    # Run Flask app in debug mode
    app.run(host='0.0.0.0', port=port, debug=True)

def run_production(workers=4):
    """Run the API in production mode using gunicorn"""
    # Get port from environment or use default
    port = int(os.environ.get("PORT", 5000))
    
    # Create a wrapper module for gunicorn
    with open("wsgi.py", "w") as f:
        f.write("""
from api import app, initialize_models, model, vectorizer
from file_api import register_file_blueprint

# Initialize model
success = initialize_models()
if not success:
    print("Failed to initialize models. API may not function correctly.")

# Register the file API blueprint
register_file_blueprint(app, model, vectorizer)
        """)
    
    # Build gunicorn command
    cmd = f"gunicorn --bind 0.0.0.0:{port} --workers {workers} wsgi:app"
    
    # Execute gunicorn
    os.system(cmd)

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run the SCAM Detection API')
    parser.add_argument('--production', action='store_true', help='Run in production mode with gunicorn')
    parser.add_argument('--workers', type=int, default=4, help='Number of gunicorn workers (only for production mode)')
    args = parser.parse_args()
    
    if args.production:
        run_production(workers=args.workers)
    else:
        run_development()

if __name__ == "__main__":
    main()
