#!/usr/bin/env python3
"""
Backfill Severity Script - Pool Scout Pro
Assigns severity levels to existing violations that don't have them.
"""
import sys
import os
import logging

# Add src path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from services.violation_severity_service import ViolationSeverityService

def main():
    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("🔍 Starting severity backfill for existing violations...")
    
    service = ViolationSeverityService()
    processed_count = service.bulk_assess_violations()
    
    if processed_count > 0:
        print(f"✅ Successfully assigned severity to {processed_count} violations")
    else:
        print("❌ No violations processed or error occurred")

if __name__ == '__main__':
    main()
