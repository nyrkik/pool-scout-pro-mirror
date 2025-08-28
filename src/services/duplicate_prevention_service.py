import sqlite3
from core.database_config import db_config

class DuplicatePreventionService:
    def __init__(self):
        self.db_path = db_config.inspection_db_path
    
    def is_duplicate_by_inspection_id(self, inspection_id, search_date):
        """Check if inspection_id already exists in database using exact matching"""
        if not inspection_id:
            return False
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM inspection_reports WHERE inspection_id = ?", (inspection_id,))
            count = cursor.fetchone()[0]
            conn.close()
            return count > 0
        except Exception as e:
            print(f"⚠️ Database error in duplicate check: {e}")
            return False

    def is_duplicate_by_name(self, facility_name, search_date=None):
        """More permissive name-based check - only blocks if 3+ reports exist"""
        if not facility_name or not search_date:
            return False
        try:
            # No date conversion needed; use YYYY-MM-DD directly
            conn = sqlite3.connect(self.db_path, timeout=10)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM inspection_reports ir JOIN facilities f ON ir.facility_id = f.id WHERE f.name = ? AND ir.inspection_date = ?", (facility_name, search_date))
            count = cursor.fetchone()[0]
            conn.close()
            return count >= 3  # Only block if 3+ reports exist
        except Exception as e:
            print(f"⚠️ Database error in name-based duplicate check: {e}")
            return False

    def check_facility_duplicate_status(self, facility_data, search_date):
        """
        Check if facility should be marked as saved based on inspection ID extraction.
        """
        try:
            pdf_url = facility_data.get('pdf_url') or facility_data.get('url')
            if not pdf_url:
                return False
            
            from src.core.utilities import TextUtilities
            inspection_id = TextUtilities.extract_inspection_id_from_url(pdf_url)
            
            if not inspection_id:
                facility_name = facility_data.get('name')
                return self.is_duplicate_by_name(facility_name, search_date)
            
            return self.is_duplicate_by_inspection_id(inspection_id, search_date)
            
        except Exception as e:
            print(f"⚠️ Error checking facility duplicate status: {e}")
            facility_name = facility_data.get('name')
            return self.is_duplicate_by_name(facility_name, search_date)
