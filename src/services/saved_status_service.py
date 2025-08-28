import sqlite3
from core.error_handler import ErrorHandler
from core.database_config import db_config

class SavedStatusService:
    def __init__(self):
        self.db_path = db_config.inspection_db_path
        self.error_handler = ErrorHandler(__name__)

    def get_saved_count_for_date(self, search_date):
        """Get count of saved reports for a specific date."""
        try:
            # No date conversion needed; use YYYY-MM-DD directly
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = '''
                SELECT COUNT(*) 
                FROM inspection_reports 
                WHERE inspection_date = ?
            '''
            
            cursor.execute(query, (search_date,))
            result = cursor.fetchone()
            count = result[0] if result else 0
            conn.close()
            
            print(f"📊 Found {count} saved reports for {search_date}")
            return count
        except Exception as e:
            self.error_handler.log_error("Get saved count", e, {'search_date': search_date})
            return 0

    def get_saved_reports_for_date(self, search_date):
        """Get ALL saved reports for a specific date."""
        try:
            # No date conversion needed; use YYYY-MM-DD directly
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = """
                SELECT f.name, ir.inspection_date, ir.pdf_filename, f.street_address,
                       ir.id, ir.inspection_id
                FROM inspection_reports ir
                JOIN facilities f ON ir.facility_id = f.id
                WHERE ir.inspection_date = ?
                ORDER BY f.name, ir.id
            """
            
            cursor.execute(query, (search_date,))
            results = cursor.fetchall()
            conn.close()
            
            facilities = []
            for row in results:
                facilities.append({
                    "name": row[0],
                    "inspection_date": search_date,
                    "pdf_filename": row[2],
                    "display_address": row[3] or "Address not available",
                    "saved": True,
                    "pdf_url": None,
                    "report_id": row[4],
                    "inspection_id": row[5],
                    "index": len(facilities)
                })
            
            print(f"📊 Retrieved {len(facilities)} saved reports for {search_date}")
            return facilities
        except Exception as e:
            self.error_handler.log_error("Get saved reports", e, {"search_date": search_date})
            return []

    def check_saved_status_for_facilities(self, facilities, search_date):
        """Check saved status for a list of facilities using inspection_id."""
        try:
            if not facilities:
                return facilities
            
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
            from services.duplicate_prevention_service import DuplicatePreventionService
            
            duplicate_service = DuplicatePreventionService()
            saved_count = 0
            
            for facility in facilities:
                try:
                    inspection_id = None
                    pdf_url = facility.get('pdf_url')
                    if pdf_url:
                        import re
                        pattern = r'inspectionID=([A-F0-9\-]{36})'
                        match = re.search(pattern, pdf_url, re.IGNORECASE)
                        if match:
                            full_id = match.group(1)
                            inspection_id = full_id.split('-')[-1]
                    
                    if inspection_id:
                        is_saved = duplicate_service.is_duplicate_by_inspection_id(inspection_id, search_date)
                    else:
                        is_saved = duplicate_service.is_duplicate_by_name(facility.get('name', ''), search_date)
                    
                    facility['saved'] = is_saved
                    if is_saved:
                        saved_count += 1
                        
                except Exception as e:
                    print(f"Error checking facility {facility.get('name', 'unknown')}: {e}")
                    facility['saved'] = False
            
            print(f"📊 Checked {len(facilities)} facilities: {saved_count} saved, {len(facilities) - saved_count} new")
            return facilities
            
        except Exception as e:
            self.error_handler.log_error("Check saved status", e)
            for facility in facilities:
                facility['saved'] = False
            return facilities
