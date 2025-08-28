import sqlite3
import os
from pathlib import Path
from .settings import settings

class Database:
    def __init__(self):
        self.db_path = settings.database_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def init_schema(self):
        """Creates the final, comprehensive database schema based on the project milestone."""
        with self.get_connection() as conn:
            # Facilities table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS facilities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    street_address TEXT,
                    city TEXT,
                    state TEXT,
                    zip_code TEXT,
                    phone TEXT,
                    establishment_id TEXT,
                    permit_holder TEXT,
                    program_identifier TEXT,
                    facility_type TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Inspection Reports table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS inspection_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    facility_id INTEGER NOT NULL,
                    permit_id TEXT,
                    establishment_id TEXT,
                    inspection_date TEXT,
                    inspection_type TEXT,
                    inspection_id TEXT,
                    inspector_name TEXT,
                    inspector_phone TEXT,
                    report_recipient_name TEXT,
                    report_recipient_title TEXT,
                    report_delivery_method TEXT,
                    total_violations INTEGER DEFAULT 0,
                    major_violations INTEGER DEFAULT 0,
                    pdf_filename TEXT,
                    pdf_path TEXT,
                    report_notes TEXT,
                    equipment_details TEXT,
                    equipment_matches_emd TEXT,
                    water_chemistry_details TEXT,
                    closure_status TEXT DEFAULT 'operational',
                    closure_reason TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP,
                    FOREIGN KEY (facility_id) REFERENCES facilities(id)
                )
            """)
            
            # Violations table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS violations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_id INTEGER NOT NULL,
                    facility_id INTEGER NOT NULL,
                    violation_code TEXT,
                    violation_title TEXT,
                    observations TEXT,
                    corrective_action TEXT,
                    code_description TEXT,
                    is_major_violation BOOLEAN DEFAULT FALSE,
                    severity_level INTEGER,
                    FOREIGN KEY (report_id) REFERENCES inspection_reports(id),
                    FOREIGN KEY (facility_id) REFERENCES facilities(id)
                )
            """)
            
            conn.commit()

database = Database()
