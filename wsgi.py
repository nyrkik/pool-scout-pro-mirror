#!/usr/bin/env python3
"""
WSGI entry point for Pool Scout Pro
Production-ready entry point for Gunicorn
"""

import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Set production configuration
os.environ.setdefault('FLASK_ENV', 'production')

# Import the create_app function and create the app instance
from web.app import create_app

# Create the Flask app instance for WSGI
app = create_app()

if __name__ == "__main__":
    app.run()
