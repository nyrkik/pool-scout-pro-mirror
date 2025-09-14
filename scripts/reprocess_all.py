import sqlite3
import sys
import os
import logging

# Add the project's 'src' directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from services.pdf_extractor import PDFExtractor

# --- Configuration ---
DB_PATH = 'data/inspection_data.db'
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def reprocess_all_pdfs():
    """
    Finds all PDFs in the database and re-processes them to backfill new data.
    """
    logging.info("Starting re-processing of all PDFs in the database...")
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row # Allows accessing columns by name
            cursor = conn.cursor()
            
            # Get all reports that have a valid PDF path
            cursor.execute("""
                SELECT ir.pdf_path, ir.inspection_id, f.name AS facility_name
                FROM inspection_reports ir
                JOIN facilities f ON ir.facility_id = f.id
                WHERE ir.pdf_path IS NOT NULL AND ir.pdf_path != ''
            """)
            
            reports_to_process = cursor.fetchall()
    except sqlite3.Error as e:
        logging.error(f"Failed to fetch reports from the database: {e}")
        return

    if not reports_to_process:
        logging.warning("No reports found in the database to re-process.")
        return

    logging.info(f"Found {len(reports_to_process)} reports to re-process. Beginning extraction...")
    
    extractor = PDFExtractor(db_path=DB_PATH)
    success_count = 0
    fail_count = 0

    for i, report in enumerate(reports_to_process):
        pdf_path = report['pdf_path']
        logging.info(f"--- Processing {i+1}/{len(reports_to_process)}: {os.path.basename(pdf_path)} ---")
        
        if not os.path.exists(pdf_path):
            logging.warning(f"Skipping: PDF file not found at '{pdf_path}'")
            fail_count += 1
            continue

        # The extract_and_save function now handles the full update logic
        result = extractor.extract_and_save(
            pdf_path=pdf_path,
            facility_name=report['facility_name'],
            inspection_id=report['inspection_id']
        )

        if result and result.get('success'):
            success_count += 1
        else:
            fail_count += 1
            logging.error(f"Failed to process {os.path.basename(pdf_path)}")

    logging.info("--- Re-processing Complete ---")
    logging.info(f"Successfully processed: {success_count}")
    logging.info(f"Failed or skipped: {fail_count}")

if __name__ == '__main__':
    reprocess_all_pdfs()
