#!/usr/bin/env python3
"""
Pool Scout Pro - Application Entry Point
Proper entry point with correct Python path setup
"""
import sys
import os
from pathlib import Path

# Add src to Python path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

if __name__ == "__main__":
    from web.app import create_app
    app = create_app()
    app.run(host='0.0.0.0', port=7001, debug=True)
