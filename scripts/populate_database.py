#!/usr/bin/env python3
"""
Pool Scout Pro - Database Populator
Loads extracted report data into the Pool Scout Pro database
"""

import sqlite3
import json
import os
import sys
from datetime import datetime
from typing import Dict, List
import logging

# Add the parent directory to sys.path so we can import the extractor
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.pdf_extractor import PoolReportExtractor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabasePopulator:
    def __init__(self, db_path: str = "data/pool_scout.db"):
        self.db_path = db_path
        self.extractor = PoolReportExtractor()

    def connect_db(self):
        """Create database connection"""
        return sqlite3.connect(self.db_path)

    def populate_facility(self, conn: sqlite3.Connection, report_data: Dict) -> int:
        """
        Insert/update facility data and return facility_id
        """
        facility_info = report_data.get('facility_info', {})
        management_company = report_data.get('management_company')
        
        # Get management company ID
        mgmt_company_id = None
        if management_company:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM management_companies WHERE name = ?",
                (management_company,)
            )
            result = cursor.fetchone()
            if result:
                mgmt_company_id = result[0]
        
        # Check if facility already exists
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM pool_facilities WHERE establishment_id = ?",
            (facility_info.get('establishment_id'),)
        )
        existing = cursor.fetchone()
        
        if existing:
            # Update existing facility
            facility_id = existing[0]
            cursor.execute("""
                UPDATE pool_facilities SET
                    name = ?, address = ?, city = ?, zip_code = ?,
                    phone = ?, permit_holder = ?, permit_id = ?,
                    facility_type = ?, management_company_id = ?,
                    updated_at = ?
                WHERE id = ?
            """, (
                facility_info.get('name'),
                facility_info.get('address'),
                facility_info.get('city'),
                facility_info.get('zip'),
                facility_info.get('phone'),
                facility_info.get('permit_holder'),
                facility_info.get('permit_id'),
                facility_info.get('facility_type'),
                mgmt_company_id,
                datetime.now().isoformat(),
                facility_id
            ))
            logger.info(f"Updated facility: {facility_info.get('name')}")
        else:
            # Insert new facility
            cursor.execute("""
                INSERT INTO pool_facilities (
                    name, address, city, zip_code, phone, permit_holder,
                    permit_id, establishment_id, facility_type,
                    management_company_id, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                facility_info.get('name'),
                facility_info.get('address'),
                facility_info.get('city'),
                facility_info.get('zip'),
                facility_info.get('phone'),
                facility_info.get('permit_holder'),
                facility_info.get('permit_id'),
                facility_info.get('establishment_id'),
                facility_info.get('facility_type'),
                mgmt_company_id,
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            facility_id = cursor.lastrowid
            logger.info(f"Created new facility: {facility_info.get('name')}")
        
        conn.commit()
        return facility_id

    def populate_inspection_report(self, conn: sqlite3.Connection, facility_id: int, report_data: Dict) -> int:
        """
        Insert inspection report and return report_id
        """
        inspection_info = report_data.get('inspection_info', {})
        inspector_info = report_data.get('inspector_info', {})
        measurements = report_data.get('measurements', {})
        violation_summary = report_data.get('violation_summary', {})
        
        cursor = conn.cursor()
        
        # Check if this report already exists
        cursor.execute("""
            SELECT id FROM inspection_reports 
            WHERE facility_id = ? AND inspection_date = ? AND file_path = ?
        """, (
            facility_id,
            inspection_info.get('date_entered'),
            report_data.get('file_path')
        ))
        
        existing = cursor.fetchone()
        if existing:
            logger.info(f"Report already exists for facility {facility_id}")
            return existing[0]
        
        # Insert new inspection report
        cursor.execute("""
            INSERT INTO inspection_reports (
                facility_id, inspection_date, inspection_type,
                inspector_name, inspector_phone, 
                total_violations, major_violations, minor_violations,
                free_chlorine, ph_level, cyanuric_acid, temperature,
                file_path, raw_data, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            facility_id,
            inspection_info.get('date_entered'),
            inspection_info.get('type', 'INSPECTION'),
            inspector_info.get('name'),
            inspector_info.get('phone'),
            violation_summary.get('total_violations', 0),
            violation_summary.get('major_violations', 0),
            violation_summary.get('minor_violations', 0),
            measurements.get('free_chlorine'),
            measurements.get('ph'),
            measurements.get('cya'),
            measurements.get('temperature'),
            report_data.get('file_path'),
            json.dumps(report_data),
            datetime.now().isoformat()
        ))
        
        report_id = cursor.lastrowid
        conn.commit()
        
        logger.info(f"Created inspection report {report_id} for facility {facility_id}")
        return report_id

    def populate_violations(self, conn: sqlite3.Connection, report_id: int, violations: List[Dict]):
        """
        Insert violations for an inspection report
        """
        cursor = conn.cursor()
        
        for violation in violations:
            cursor.execute("""
                INSERT INTO inspection_violations (
                    report_id, violation_code, severity, description,
                    observations, corrective_action, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                report_id,
                violation.get('code'),
                violation.get('severity'),
                violation.get('code_description'),
                violation.get('observations'),
                None,  # Could extract corrective actions in future
                datetime.now().isoformat()
            ))
        
        conn.commit()
        logger.info(f"Added {len(violations)} violations for report {report_id}")

    def populate_single_report(self, pdf_path: str) -> bool:
        """
        Process a single PDF report and populate the database
        """
        try:
            # Extract data from PDF
            logger.info(f"Extracting data from {pdf_path}")
            report_data = self.extractor.extract_report_data(pdf_path)
            
            if not report_data:
                logger.error(f"Failed to extract data from {pdf_path}")
                return False
            
            # Connect to database
            with self.connect_db() as conn:
                # Populate facility
                facility_id = self.populate_facility(conn, report_data)
                
                # Populate inspection report
                report_id = self.populate_inspection_report(conn, facility_id, report_data)
                
                # Populate violations
                violations = report_data.get('violations', [])
                if violations:
                    self.populate_violations(conn, report_id, violations)
                
                logger.info(f"✅ Successfully populated database with {pdf_path}")
                return True
                
        except Exception as e:
            logger.error(f"Error populating database with {pdf_path}: {e}")
            return False

    def populate_all_reports(self, reports_directory: str) -> Dict:
        """
        Process all PDF reports in directory and populate database
        """
        results = {
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'failed_files': []
        }
        
        if not os.path.exists(reports_directory):
            logger.error(f"Directory {reports_directory} does not exist")
            return results
        
        pdf_files = [f for f in os.listdir(reports_directory) if f.endswith('.pdf')]
        
        if not pdf_files:
            logger.warning(f"No PDF files found in {reports_directory}")
            return results
        
        logger.info(f"Found {len(pdf_files)} PDF files to process")
        
        for filename in pdf_files:
            pdf_path = os.path.join(reports_directory, filename)
            results['processed'] += 1
            
            if self.populate_single_report(pdf_path):
                results['successful'] += 1
            else:
                results['failed'] += 1
                results['failed_files'].append(filename)
        
        return results

    def get_database_summary(self) -> Dict:
        """
        Get summary of data in the database
        """
        with self.connect_db() as conn:
            cursor = conn.cursor()
            
            # Count facilities
            cursor.execute("SELECT COUNT(*) FROM pool_facilities")
            facilities_count = cursor.fetchone()[0]
            
            # Count reports
            cursor.execute("SELECT COUNT(*) FROM inspection_reports")
            reports_count = cursor.fetchone()[0]
            
            # Count violations
            cursor.execute("SELECT COUNT(*) FROM inspection_violations")
            violations_count = cursor.fetchone()[0]
            
            # Violations by severity
            cursor.execute("""
                SELECT severity, COUNT(*) 
                FROM inspection_violations 
                GROUP BY severity
            """)
            violations_by_severity = dict(cursor.fetchall())
            
            # Facilities by management company
            cursor.execute("""
                SELECT mc.name, COUNT(pf.id)
                FROM management_companies mc
                LEFT JOIN pool_facilities pf ON mc.id = pf.management_company_id
                GROUP BY mc.name
            """)
            facilities_by_mgmt = dict(cursor.fetchall())
            
            return {
                'facilities': facilities_count,
                'reports': reports_count,
                'violations': violations_count,
                'violations_by_severity': violations_by_severity,
                'facilities_by_management_company': facilities_by_mgmt
            }
