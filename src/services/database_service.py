import sqlite3
import sys
import os

# Adjust the path to ensure core modules can be found
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core.database_config import db_config

class DatabaseService:
    def __init__(self):
        self.db_config = db_config
    
    def _row_to_dict(self, cursor, row):
        """Converts a sqlite3.Row object to a dictionary."""
        if row is None:
            return None
        return dict(zip([col[0] for col in cursor.description], row))

    def get_reports_by_date(self, date_str):
        """
        Fetches all inspection reports for a specific date.
        The incoming date_str is in YYYY-MM-DD format, which matches the database.
        """
        with self.db_config.get_inspection_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM inspection_reports WHERE inspection_date = ?",
                (date_str,)
            )
            rows = cursor.fetchall()
            return [self._row_to_dict(cursor, row) for row in rows]

    def get_facility_by_id(self, facility_id):
        """Fetches a single facility by its primary key ID."""
        with self.db_config.get_inspection_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM facilities WHERE id = ?", (facility_id,))
            row = cursor.fetchone()
            return self._row_to_dict(cursor, row)

    def get_equipment_for_report(self, report_id):
        """Fetches equipment data for a specific inspection report."""
        with self.db_config.get_inspection_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM equipment WHERE report_id = ?", (report_id,))
            row = cursor.fetchone()
            return self._row_to_dict(cursor, row)

    def save_equipment_data(self, equipment_data):
        """Save equipment data to the equipment table."""
        with self.db_config.get_inspection_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO equipment 
                (report_id, facility_id, pool_capacity_gallons, flow_rate_gpm,
                 filter_type, filter_make, filter_model, filter_capacity_gpm,
                 pump_make, pump_model, pump_hp, sanitizer_details,
                 main_drain_details, equalizer_details, equipment_matches_emd)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                equipment_data.get('report_id'),
                equipment_data.get('facility_id'),
                equipment_data.get('pool_capacity_gallons'),
                equipment_data.get('flow_rate_gpm'),
                equipment_data.get('filter_type'),
                equipment_data.get('filter_make'),
                equipment_data.get('filter_model'),
                equipment_data.get('filter_capacity_gpm'),
                equipment_data.get('pump_make'),
                equipment_data.get('pump_model'),
                equipment_data.get('pump_hp'),
                equipment_data.get('sanitizer_details'),
                equipment_data.get('main_drain_details'),
                equipment_data.get('equalizer_details'),
                equipment_data.get('equipment_matches_emd')
            ))
            return cursor.lastrowid

    # --- Other functions updated for new schema ---
    def get_facilities_with_bad_addresses(self):
        with self.db_config.get_inspection_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM facilities WHERE city IS NULL OR city = ''")
            rows = cursor.fetchall()
            return [self._row_to_dict(cursor, row) for row in rows]

    def get_latest_report_for_facility(self, facility_id):
        with self.db_config.get_inspection_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT inspection_date FROM inspection_reports WHERE facility_id = ? ORDER BY inspection_date DESC LIMIT 1",
                (facility_id,)
            )
            row = cursor.fetchone()
            return self._row_to_dict(cursor, row)
            
    def update_facility_address(self, facility_id, address_data):
        with self.db_config.get_inspection_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE facilities SET street_address = ?, city = ?, state = ?, zip_code = ? WHERE id = ?", (
                address_data.get('street'), address_data.get('city'), address_data.get('state', 'CA'),
                address_data.get('zip'), facility_id
            ))

    def upsert_facility(self, name, program_identifier, street_address, city, state, zip_code, facility_id, permit_holder, phone):
        with self.db_config.get_inspection_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM facilities WHERE name = ?", (name,))
            result = cursor.fetchone()
            if result:
                db_facility_id = result[0]
                cursor.execute("""UPDATE facilities SET 
                    street_address = ?, city = ?, state = ?, zip_code = ?, 
                    program_identifier = ?, facility_id = ?, permit_holder = ?, phone = ? 
                    WHERE id = ?""",
                    (street_address, city, state, zip_code, program_identifier, 
                     facility_id, permit_holder, phone, db_facility_id))
            else:
                cursor.execute("""INSERT INTO facilities 
                    (name, street_address, city, state, zip_code, program_identifier, 
                     facility_id, permit_holder, phone) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (name, street_address, city, state, zip_code, program_identifier, 
                     facility_id, permit_holder, phone))
                db_facility_id = cursor.lastrowid
            return db_facility_id

    def get_facility_by_permit_id(self, permit_id):
        with self.db_config.get_inspection_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM facilities WHERE permit_id = ?", (permit_id,))
            return self._row_to_dict(cursor, cursor.fetchone())

    def get_violations_for_report(self, report_id):
        """
        Fetches all violations for a specific inspection report.
        """
        with self.db_config.get_inspection_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM violations WHERE report_id = ?", (report_id,))
            rows = cursor.fetchall()
            return [self._row_to_dict(cursor, row) for row in rows]
