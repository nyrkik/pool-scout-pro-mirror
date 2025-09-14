import os
import sys

# Add the project's 'src' directory to the Python path to resolve module imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

#!/usr/bin/env python3
"""
Sacramento County PDF Extractor - Pool Scout Pro
"""

import warnings
warnings.filterwarnings("ignore", message="get_text_range.*will be implicitly redirected.*", category=UserWarning)
import fitz
import re
import sqlite3
import logging
from datetime import datetime
from dateutil.parser import parse as parse_date
from core.error_handler import ErrorHandler, with_error_handling, CommonCleanup
from core.utilities import FileUtilities
from services.violation_summarizer import summarize_violation


class PDFExtractor:
    def __init__(self, db_path='data/inspection_data.db'):
        self.db_path = db_path
        self.error_handler = ErrorHandler(__name__)

    @with_error_handling("PDF extraction and save", default_return=None)
    def extract_and_save(self, pdf_path, facility_name=None, inspection_id=None, expected_date=None):
        logging.info(f"🔎 Processing: {os.path.basename(pdf_path)}")
        text = self.extract_text(pdf_path)
        if not text: return None

        data = {
            'inspection_id': inspection_id,
            'facility_name': facility_name,
            'inspection_date': self._find_date(text),
            'violations': self._extract_violations(text),
            'pdf_path': pdf_path,
        }
        return self._save_complete_data(data)

    def extract_text(self, pdf_path):
        try:
            with fitz.open(pdf_path) as doc:
                return "".join(page.get_text() for page in doc)
        except Exception as e:
            self.error_handler.log_error("PDF text extraction", e, {"pdf_path": pdf_path})
            return ""

    def _find_date(self, text):
        match = re.search(r'Date\s+Entered\s+(\d{1,2}/\d{1,2}/\d{4})', text, re.I)
        if match:
            return parse_date(match.group(1)).strftime('%Y-%m-%d')
        return None

    def _extract_violations(self, text):
        violations = []
        pattern = re.compile(r"(\d+[a-z]?)\.\s(.*?)\n\s*Observations:(.*?)(?=\n\s*Code Description:|\Z)", re.S)
        for match in pattern.finditer(text):
            obs = match.group(3).strip()
            is_major = "MAJOR VIOLATION" in obs.upper()
            violations.append({
                "violation_code": match.group(1),
                "violation_title": match.group(2).strip(),
                "observations": obs,
                "is_major_violation": is_major
            })
        return violations

    def _save_complete_data(self, data):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                facility_id = self._get_or_create_facility(cursor, data)
                
                cursor.execute("SELECT id FROM inspection_reports WHERE inspection_id = ?", (data.get('inspection_id'),))
                report = cursor.fetchone()
                if report:
                    report_id = report[0]
                else:
                    cursor.execute('INSERT INTO inspection_reports (facility_id, inspection_id, inspection_date, pdf_path) VALUES (?, ?, ?, ?)',
                                   (facility_id, data.get('inspection_id'), data.get('inspection_date'), data.get('pdf_path')))
                    report_id = cursor.lastrowid

                if data.get('violations'):
                    self._save_violations(cursor, data['violations'], report_id, facility_id)
                
                conn.commit()
                logging.info(f"🎯 Data saved for: {data.get('facility_name')}")
                return {'report_id': report_id, 'success': True}
        except Exception as e:
            self.error_handler.log_error("DB save failed", str(e), {'name': data.get('facility_name')})
            return None

    def _get_or_create_facility(self, cursor, data):
        name = data.get('facility_name', 'Unknown').title()
        cursor.execute('SELECT id FROM facilities WHERE name = ?', (name,))
        result = cursor.fetchone()
        if result: return result[0]
        cursor.execute('INSERT INTO facilities (name) VALUES (?)', (name,))
        return cursor.lastrowid

    def _save_violations(self, cursor, violations, report_id, facility_id):
        cursor.execute("DELETE FROM violations WHERE report_id = ?", (report_id,))
        for v in violations:
            summary = summarize_violation(
                v.get('violation_title'),
                v.get('violation_code'),
                cursor=cursor
            )
            cursor.execute('INSERT INTO violations (report_id, facility_id, violation_code, violation_title, observations, shorthand_summary) VALUES (?, ?, ?, ?, ?, ?)',
                           (report_id, facility_id, v.get('violation_code'), v.get('violation_title'), v.get('observations'), summary))
        logging.info(f"   ✅ Saved {len(violations)} violations with summaries.")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    pdf_to_test = '/mnt/nas/pool_scout_pro/reports/2025/20250819_INSHAPEFITNESS_649E27053AEE.pdf'
    inspection_id_to_test = '95C241D9-0BCD-4140-9C2A-649E27053AEE'
    
    if not os.path.exists(pdf_to_test):
        logging.error(f"TEST FAILED: PDF file not found at '{pdf_to_test}'")
    else:
        logging.info("--- Running Standalone Extractor Test ---")
        extractor = PDFExtractor()
        result = extractor.extract_and_save(
            pdf_path=pdf_to_test,
            facility_name="In-Shape Fitness",
            inspection_id=inspection_id_to_test
        )
        if result and result.get('success'):
            logging.info("✅ Test completed successfully!")
            # Optional: Query DB to see the new summary
            try:
                with sqlite3.connect('data/inspection_data.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT violation_title, shorthand_summary FROM violations WHERE report_id = ?", (result['report_id'],))
                    summaries = cursor.fetchall()
                    logging.info("--- VERIFICATION: Summaries saved in DB ---")
                    for row in summaries:
                        logging.info(f"'{row[0]}' -> '{row[1]}'")
            except Exception as e:
                logging.error(f"Could not verify DB results: {e}")
        else:
            logging.error("❌ Test failed. See errors above.")
