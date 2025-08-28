#!/usr/bin/env python3
"""
Violation Severity Assessment Service
"""
import sqlite3
import re
import logging
import sys
import os
from core.database_config import db_config

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class ViolationSeverityService:
    def __init__(self):
        self.db_path = db_config.inspection_db_path
        self.logger = logging.getLogger(__name__)
        
    def _match_reference_table(self, violation_text):
        """Match violation against reference table patterns"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT category_number, short_phrase, severity_reasoning, finding_pattern
                FROM violation_severity_reference
                ORDER BY category_number
            """)
            
            patterns = cursor.fetchall()
            conn.close()
            
            violation_lower = violation_text.lower()
            
            for category, phrase, reasoning, pattern in patterns:
                if re.search(pattern, violation_lower, re.IGNORECASE):
                    self.logger.info(f"Matched pattern '{pattern}' -> Severity {category}")
                    return {
                        'severity_level': category,
                        'short_phrase': phrase,
                        'reasoning': reasoning,
                        'matched_pattern': pattern,
                        'source': 'reference_table'
                    }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error matching reference table: {e}")
            return None

    # ... (rest of the class methods are unchanged)
