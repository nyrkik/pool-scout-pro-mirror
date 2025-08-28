#!/bin/bash
# Project maintenance - run monthly

echo "Running project maintenance..."

# Remove common bloat
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null
find . -name "test_*.py" -delete 2>/dev/null
find . -name "temp_*.py" -delete 2>/dev/null
find . -name "*.log" -delete 2>/dev/null

# Report project size
echo "Current project size:"
du -sh . --exclude=.git

echo "Maintenance complete"
