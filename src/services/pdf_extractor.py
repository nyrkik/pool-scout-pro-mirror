import os
#!/usr/bin/env python3
"""
Sacramento County PDF Extractor - Pool Scout Pro
MULTILINE VERSION: Equipment parsing handles multi-line data
"""

import warnings
warnings.filterwarnings("ignore", message="get_text_range.*will be implicitly redirected.*", category=UserWarning)
import fitz  # pymupdf
import re
import sqlite3
from datetime import datetime, date
from dateutil.parser import parse as parse_date
from core.error_handler import ErrorHandler, with_error_handling, CommonCleanup
from core.utilities import FileUtilities, NameUtilities


class PDFExtractor:
    def __init__(self, db_path='data/inspection_data.db'):
        self.db_path = db_path
        self.error_handler = ErrorHandler(__name__)

    def _find_value_for_key(self, text, key):
        """Generic helper to find a value on the same line following a key."""
        try:
            pattern = re.compile(f"^{re.escape(key)}\\s+(.*)$", re.MULTILINE | re.IGNORECASE)
            match = pattern.search(text)
            if match:
                return match.group(1).strip()
        except Exception:
            return None
        return None

    @with_error_handling("PDF extraction and save", default_return=None)
    def extract_and_save(self, pdf_path, facility_name=None, inspection_id=None, expected_date=None):
        """Extract complete data from Sacramento County PDFs with date verification"""
        print(f"🔎 Processing: {os.path.basename(pdf_path)}")

        text = self.extract_text(pdf_path)
        if not text:
            return None

        print(f"📄 Extracted {len(text)} characters")

        # Extract actual inspection date from PDF
        actual_inspection_date = self._find_date(text)

        # Verify date if expected date provided
        date_verified = None
        if expected_date and actual_inspection_date:
            date_verified = self._verify_date_match(actual_inspection_date, expected_date)
            if not date_verified:
                print(f"⚠️  Date mismatch: PDF has {actual_inspection_date}, expected {expected_date}")

        # Use actual inspection date for filename if available
        filename_date = actual_inspection_date if actual_inspection_date else expected_date

        # Generate new filename with actual inspection date
        if filename_date and facility_name and inspection_id:
            new_filename = FileUtilities.generate_inspection_filename(
                facility_name, inspection_id, filename_date
            )

            # Rename PDF file to use actual date
            old_path = pdf_path
            new_path = os.path.join(os.path.dirname(pdf_path), new_filename)

            if old_path != new_path:
                try:
                    os.rename(old_path, new_path)
                    print(f"🏷️  Renamed: {os.path.basename(old_path)} → {new_filename}")
                    pdf_path = new_path
                except Exception as e:
                    print(f"⚠️  Could not rename file: {e}")

        # Ensure date is normalized before saving to the database
        normalized_date = self._normalize_date_for_comparison(actual_inspection_date or expected_date)

        data = {
            'inspection_id': inspection_id,
            'facility_name': facility_name,
            'permit_id': self._find_permit_id(text),
            'establishment_id': self._find_establishment_id(text),
            'inspection_date': normalized_date,
            'expected_date': expected_date,
            'date_verified': date_verified,
            'program_identifier': self._find_program_identifier(text),
            'raw_address': self._extract_address(text),
            'permit_holder': self._extract_permit_holder(text),
            'phone': self._extract_phone(text),
            'inspection_type': self._extract_inspection_type(text),
            'pdf_filename': os.path.basename(pdf_path),
            'pdf_path': pdf_path,
            'inspector_name': self._extract_inspector_name(text),
            'inspector_phone': self._extract_inspector_phone(text),
            'report_recipient': self._extract_report_recipient(text),
            'barcode_data': self._extract_barcode_data(text),
            'reinspection_required': self._extract_reinspection_required(text),
            'closure_suspension_required': self._extract_closure_suspension_required(text),
            'violations': self._extract_violations(text),
            'equipment': self._extract_equipment_comprehensive(text),
            'water_chemistry': self._extract_water_chemistry(text),
            'report_notes': self._extract_report_notes(text),
            '_full_text': text  # Pass full text for facility type detection
        }

        return self._save_complete_data(data)

    def extract_text(self, pdf_path):
        """Extract text using pymupdf with basic error handling"""
        try:
            doc = fitz.open(pdf_path)
            text_parts = []

            for page_num in range(min(10, len(doc))):
                page = doc[page_num]
                text = page.get_text()
                text_parts.append(text)

            doc.close()
            return "\n".join(text_parts)

        except Exception as e:
            self.error_handler.log_error("PDF text extraction", e, {"pdf_path": pdf_path})
            return ""

    def _verify_date_match(self, actual_date, expected_date):
        """Verify if actual inspection date matches expected search date"""
        try:
            if actual_date and expected_date:
                actual_normalized = self._normalize_date_for_comparison(actual_date)
                expected_normalized = self._normalize_date_for_comparison(expected_date)
                return actual_normalized == expected_normalized
        except Exception as e:
            self.error_handler.log_warning("Date verification", f"Could not verify dates: {e}")
            return None
        return False

    def _normalize_date_for_comparison(self, date_str):
        """Normalize various date string formats to the standard 'YYYY-MM-DD'."""
        if not date_str:
            return None
        try:
            date_obj = parse_date(date_str)
            return date_obj.strftime('%Y-%m-%d')
        except (ValueError, TypeError):
            self.error_handler.log_warning("Date Normalization", f"Could not parse date: '{date_str}'")
            return None

    def _find_date(self, text):
        """Extract inspection date from PDF - enhanced for Sacramento County format"""
        # Look for "Date Entered MM/DD/YYYY" pattern first (most reliable)
        date_entered_pattern = r'Date\s+Entered\s+(\d{1,2}/\d{1,2}/\d{4})'
        match = re.search(date_entered_pattern, text, re.IGNORECASE)
        if match:
            found_date = match.group(1)
            print(f"🗓️  Found 'Date Entered': {found_date}")
            return self._normalize_date_for_comparison(found_date)

        # Fallback to other date patterns
        patterns = [
            r'(?:Inspection|Date)[:\s]*(\d{1,2}/\d{1,2}/\d{4})',
            r'(\d{1,2}/\d{1,2}/\d{4})',
            r'(\d{4}-\d{2}-\d{2})'
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                found_date = matches[0]
                print(f"🗓️  Found date pattern: {found_date}")
                return self._normalize_date_for_comparison(found_date)

        print("⚠️  No date found in PDF")
        return None


    def _determine_facility_type(self, text, program_identifier):
        """Determine if facility is Pool or Spa based on multiple indicators"""

        # Only check facility name, not entire document
        facility_name_match = re.search(r'Facility Name\s+([^\n]+)', text, re.IGNORECASE)
        facility_name = facility_name_match.group(1) if facility_name_match else ""

        # Check for explicit spa indicators in facility name only
        if any(word in facility_name.upper() for word in ['HOT TUB', 'JACUZZI', 'WHIRLPOOL', 'SPA ']):
            return 'SPA'

        # Check program identifier for spa-specific programs
        if program_identifier and 'SPA' in program_identifier and 'SPRAY' not in program_identifier:
            return 'SPA'

        # Check for jet pump equipment (spa indicator)
        if 'jet pump' in text.lower() or 'spa jet' in text.lower():
            return 'SPA'

        # Default to POOL for recreational facilities
        print(f"Defaulting to POOL for facility: {facility_name}")
        return 'POOL'

    def _save_complete_data(self, data):
        """Save extracted data to database with new equipment schema"""
        if not data.get('inspection_date'):
            self.error_handler.log_error("Database Save Blocked", "Inspection date is null after normalization.", {
                'facility_name': data.get('facility_name'),
                'pdf_filename': data.get('pdf_filename')
            })
            return None

        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            facility_id = self._get_or_create_facility(cursor, data)

            # FIXED: Move variable definitions before debug lines
            violations = data.get('violations', [])
            total_violations = len(violations) if violations else 0
            major_violations = sum(1 for v in violations if v.get('is_major_violation')) if violations else 0

            print(f"🗃️  DB DEBUG: total_violations={total_violations}, major_violations={major_violations}")
            print(f"🗃️  DB DEBUG: pool_capacity_gallons={data.get('equipment', {}).get('pool_capacity_gallons')}")
            print(f"🗃️  DB DEBUG: flow_rate_gpm={data.get('equipment', {}).get('flow_rate_gpm')}")

            cursor.execute('''
                INSERT INTO inspection_reports
                (facility_id, permit_id, inspection_date, inspection_type,
                 inspector_name, inspector_phone, report_recipient,
                 total_violations, major_violations,
                 pdf_filename, pdf_path, report_notes,
                 reinspection_required, closure_suspension_required,
                 barcode_data, pool_capacity_gallons, pool_flow_rate_gpm,
                 water_chemistry_details, inspection_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(inspection_id) DO NOTHING
            ''', (
                facility_id,
                data.get('permit_id'),
                data.get('inspection_date'),
                data.get('inspection_type'),
                data.get('inspector_name'),
                data.get('inspector_phone'),
                data.get('report_recipient'),
                total_violations, major_violations,
                data.get('pdf_filename'), data.get('pdf_path'), data.get('report_notes'),
                data.get('reinspection_required'), data.get('closure_suspension_required'),
                data.get('barcode_data'),
                data.get('equipment', {}).get('pool_capacity_gallons'),
                data.get('equipment', {}).get('flow_rate_gpm'),
                str(data.get('water_chemistry')) if data.get('water_chemistry') else None,
                data.get('inspection_id'),
                datetime.utcnow().isoformat(timespec='seconds')
            ))

            report_id = cursor.lastrowid

            # Log date verification results
            if data.get('date_verified') is not None:
                if data['date_verified']:
                    print(f"✅ Date verified: {data['inspection_date']} matches expected")
                else:
                    print(f"⚠️  Date mismatch: {data['inspection_date']} vs expected {data.get('expected_date')}")

            print(f"✅ Saved inspection report: ID {report_id}")
            print(f"   🗓️  Inspection date: {data['inspection_date']}")
            print(f"    pelanggaran: {total_violations} total, {major_violations} major")

            if violations:
                self._save_violations(cursor, violations, report_id, facility_id)

            # Save comprehensive equipment data to new schema
            if data.get('equipment'):
                self._save_equipment_comprehensive(cursor, data.get('equipment'), report_id, facility_id)

            conn.commit()

            print(f"🎯 Complete data saved for: {data.get('facility_name', 'Unknown')}")
            return {
                'facility_id': facility_id,
                'report_id': report_id,
                'total_violations': total_violations,
                'major_violations': major_violations,
                'actual_inspection_date': data['inspection_date'],
                'date_verified': data.get('date_verified'),
                'success': True
            }

        except Exception as e:
            self.error_handler.log_error("Database save failed", str(e), {
                'facility_name': data.get('facility_name'),
                'pdf_filename': data.get('pdf_filename')
            })
            return None
        finally:
            CommonCleanup.close_database_connection(conn)

    def _get_or_create_facility(self, cursor, data):
        """Create or retrieve facility with simplified field mapping"""
        # FIXED: Apply title case to facility name before saving
        facility_name = (data.get('facility_name') or "Unknown Facility").title()
        address_data = data.get('raw_address', {})

        # Determine facility type using extracted text
        program_identifier = data.get('program_identifier')
        facility_type = self._determine_facility_type(
            data.get('_full_text', ''), program_identifier
        )

        try:
            cursor.execute('SELECT id FROM facilities WHERE name = ?', (facility_name,))
            result = cursor.fetchone()
            if result:
                facility_id = result[0]
                if address_data.get('street_address'):
                    cursor.execute('''UPDATE facilities SET
                                      street_address = ?, city = ?, zip_code = ?,
                                      facility_id = ?, permit_holder = ?, phone = ?
                                      WHERE id = ?''',
                                   (address_data.get('street_address'),
                                    address_data.get('city'),
                                    address_data.get('zip_code'),
                                    data.get('establishment_id'),
                                    data.get('permit_holder'),
                                    data.get('phone'),
                                    facility_id))
                return facility_id

            # Create new facility
            cursor.execute('''
                INSERT INTO facilities (name, program_identifier, facility_type, street_address, city, state, zip_code,
                                      facility_id, permit_holder, phone)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                facility_name,
                program_identifier,
                facility_type,
                address_data.get('street_address'),
                address_data.get('city'),
                'CA',
                address_data.get('zip_code'),
                data.get('establishment_id'),
                data.get('permit_holder'),
                data.get('phone')
            ))

            facility_id = cursor.lastrowid
            print(f"✅ Created new facility {facility_id}: {facility_name}")
            return facility_id

        except Exception as e:
            self.error_handler.log_error("Facility creation/retrieval", e, {'facility_name': facility_name})
            raise

    def _save_violations(self, cursor, violations, report_id, facility_id):
        """Save violations with aligned field names"""
        if not violations:
            return

        saved_violations = 0
        for i, violation in enumerate(violations):
            try:
                cursor.execute('''
                    INSERT INTO violations
                    (report_id, facility_id, violation_code, violation_title,
                     observations, code_description, is_major_violation,
                     corrective_action, severity_level)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    report_id, facility_id,
                    violation.get('violation_code'),
                    violation.get('violation_title'),
                    violation.get('observations'),
                    violation.get('code_description'),
                    violation.get('is_major_violation', False),
                    violation.get('corrective_action'),
                    violation.get('severity_level', 1)
                ))
                saved_violations += 1
            except Exception as e:
                self.error_handler.log_warning("Violation save", f"Failed to save violation {i+1}", {
                    'violation_code': violation.get('violation_code'),
                    'error': str(e)
                })

        if saved_violations > 0:
            print(f"   ✅ Saved {saved_violations}/{len(violations)} violations")

    def _save_equipment_comprehensive(self, cursor, equipment_data, report_id, facility_id):
        """
        Drift-proof insert into equipment table.
        Includes new *_notes columns; leaves them NULL if not provided.
        """
        if not equipment_data:
            return

        # Keep this order aligned to SQLite schema (PRAGMA table_info order, minus id/created_at).
        colnames = [
            "report_id","facility_id",
            "pool_capacity_gallons","flow_rate_gpm",
            "filter_pump_1_make","filter_pump_1_model","filter_pump_1_hp",
            "filter_pump_2_make","filter_pump_2_model","filter_pump_2_hp",
            "filter_pump_3_make","filter_pump_3_model","filter_pump_3_hp",
            "jet_pump_1_make","jet_pump_1_model","jet_pump_1_hp",
            "jet_pump_2_make","jet_pump_2_model","jet_pump_2_hp",
            "filter_1_type","filter_1_make","filter_1_model","filter_1_capacity_gpm",
            "filter_2_type","filter_2_make","filter_2_model","filter_2_capacity_gpm",
            "sanitizer_1_type","sanitizer_1_details",
            "sanitizer_2_type","sanitizer_2_details",
            "main_drain_type","main_drain_model","main_drain_install_date",
            "equalizer_model","equalizer_install_date",
            "equipment_matches_emd",
            # --- new note fields ---
            "filter_notes","pump_notes","jet_pump_notes","sanitizer_notes",
            "main_drain_notes","equalizer_notes","equipment_notes",
        ]

        values = [
            report_id, facility_id,
            equipment_data.get("pool_capacity_gallons"),
            equipment_data.get("flow_rate_gpm"),
            equipment_data.get("filter_pump_1_make"),
            equipment_data.get("filter_pump_1_model"),
            equipment_data.get("filter_pump_1_hp"),
            equipment_data.get("filter_pump_2_make"),
            equipment_data.get("filter_pump_2_model"),
            equipment_data.get("filter_pump_2_hp"),
            equipment_data.get("filter_pump_3_make"),
            equipment_data.get("filter_pump_3_model"),
            equipment_data.get("filter_pump_3_hp"),
            equipment_data.get("jet_pump_1_make"),
            equipment_data.get("jet_pump_1_model"),
            equipment_data.get("jet_pump_1_hp"),
            equipment_data.get("jet_pump_2_make"),
            equipment_data.get("jet_pump_2_model"),
            equipment_data.get("jet_pump_2_hp"),
            equipment_data.get("filter_1_type"),
            equipment_data.get("filter_1_make"),
            equipment_data.get("filter_1_model"),
            equipment_data.get("filter_1_capacity_gpm"),
            equipment_data.get("filter_2_type"),
            equipment_data.get("filter_2_make"),
            equipment_data.get("filter_2_model"),
            equipment_data.get("filter_2_capacity_gpm"),
            equipment_data.get("sanitizer_1_type"),
            equipment_data.get("sanitizer_1_details"),
            equipment_data.get("sanitizer_2_type"),
            equipment_data.get("sanitizer_2_details"),
            equipment_data.get("main_drain_type"),
            equipment_data.get("main_drain_model"),
            equipment_data.get("main_drain_install_date"),
            equipment_data.get("equalizer_model"),
            equipment_data.get("equalizer_install_date"),
            True,
            # --- notes ---
            equipment_data.get("filter_notes"),
            equipment_data.get("pump_notes"),
            equipment_data.get("jet_pump_notes"),
            equipment_data.get("sanitizer_notes"),
            equipment_data.get("main_drain_notes"),
            equipment_data.get("equalizer_notes"),
            equipment_data.get("equipment_notes"),
        ]

        assert len(colnames) == len(values), f"Column/value mismatch: {len(colnames)} vs {len(values)}"

        placeholders = ", ".join(["?"] * len(colnames))
        cols_sql = ", ".join(colnames)
        sql = f"INSERT INTO equipment ({cols_sql}) VALUES ({placeholders})"

        try:
            cursor.execute(sql, values)
            print("   ✅ Saved comprehensive equipment data")
        except Exception as e:
            self.error_handler.log_warning("Equipment save", f"Failed to save equipment data: {e}")

    # --- EXTRACTION METHODS ---
    def _find_permit_id(self, text):
        pattern = r"Permit ID\s+([A-Z0-9]+)"
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else None

    def _find_establishment_id(self, text):
        pattern = r"Establishment ID\s+([A-Z0-9]+)"
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else None

    def _extract_address(self, text):
        """Extract facility address details from the text."""
        return {
            'street_address': re.search(r"Facility Address\s+([^\n]+?)\s+Facility City", text, re.IGNORECASE).group(1).strip() if re.search(r"Facility Address\s+([^\n]+?)\s+Facility City", text, re.IGNORECASE) else None,
            'city': re.search(r"Facility City\s+([^\n]+?)\s+Facility ZIP", text, re.IGNORECASE).group(1).strip() if re.search(r"Facility City\s+([^\n]+?)\s+Facility ZIP", text, re.IGNORECASE) else None,
            'zip_code': re.search(r"Facility ZIP\s+(\d{5})", text, re.IGNORECASE).group(1).strip() if re.search(r"Facility ZIP\s+(\d{5})", text, re.IGNORECASE) else None,
            'state': 'CA',
            'county': 'Sacramento'
        }

    def _extract_permit_holder(self, text):
        pattern = r"Permit Holder\s+([^\n]+)"
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else None

    def _extract_phone(self, text):
        return self._find_value_for_key(text, "Phone Number")

    def _extract_facility_name(self, text):
        """Extract actual facility name from PDF"""
        pattern = r"Facility Name\s+([^\n]+)"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            # Clean up the name - title case with proper spacing
            if name.isupper():
                name = name.title()
            return name
        return None

    def _extract_inspection_type(self, text):
        type_match = re.search(r"Type\s+([A-Z]+)", text, re.IGNORECASE)
        purpose_match = re.search(r"Purpose\s+([A-Z]+)", text, re.IGNORECASE)
        return type_match.group(1).strip() if type_match else (purpose_match.group(1).strip() if purpose_match else None)

    def _extract_barcode_data(self, text):
        """Extract barcode data from PDF."""
        pattern = r"(EMD\d+\+DA\d+\+\d{2}-\d{2}-\d{4})"
        match = re.search(pattern, text)
        return match.group(1) if match else None

    def _extract_reinspection_required(self, text):
        """Extract reinspection requirement."""
        return "Reinspection Required" in text

    def _extract_closure_suspension_required(self, text):
        """Extract closure/suspension requirement."""
        return "Suspension of Health Permit" in text

    def _extract_report_recipient(self, text):
        """Extract report recipient information - single field with method included"""
        pattern = r"Reviewed\s+(.+)"
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else None

    def _extract_inspector_name(self, text):
        """Extract inspector name only"""
        lines = text.split("\n")
        for i, line in enumerate(lines):
            if "Inspector" in line and i+1 < len(lines):
                return lines[i+1].strip()
        return None

    def _extract_inspector_phone(self, text):
        """Extract inspector phone only"""
        return self._find_value_for_key(text, "Insp Phone")

    def _extract_violations(self, text):
        """Extract violations with aligned field names"""
        violations = []
        lines = text.split("\n")

        for i, line in enumerate(lines):
            violation_match = re.match(r"^(\d+[a-z]?)\. (.+)$", line.strip())

            if violation_match:
                violation_code = violation_match.group(1)
                violation_title = violation_match.group(2).strip()

                # Find observations on next lines
                observations = ""
                j = i + 1
                while j < len(lines) and not re.match(r"^\d+[a-z]?\.", lines[j].strip()):
                    if "Observations:" in lines[j]:
                        obs_text = lines[j].split("Observations:", 1)[1].strip()
                        observations += obs_text
                        j += 1
                        while j < len(lines) and "Code Description:" not in lines[j] and not re.match(r"^\d+[a-z]?\.", lines[j].strip()):
                            observations += " " + lines[j].strip()
                            j += 1
                        break
                    j += 1

                # Extract code description with strict boundary detection
                code_description = ""
                j = i + 1
                while j < len(lines):
                    if "Code Description:" in lines[j]:
                        desc_text = lines[j].split("Code Description:", 1)[1].strip()
                        code_description += desc_text
                        j += 1
                        while j < len(lines):
                            next_line = lines[j].strip()
                            # Stop at next violation, page breaks, or form fields
                            if (re.match(r"^\d+[a-z]?\.", next_line) or
                                next_line.startswith("Pag ") or
                                next_line.startswith("Date Entered") or
                                next_line.startswith("Recreational Health") or
                                next_line.startswith("Permit Holder") or
                                next_line.startswith("Facility") or
                                next_line.startswith("Phone Number") or
                                next_line.startswith("RP Gauge") or
                                next_line.startswith("Pool Equipment") or
                                len(next_line) == 0):
                                break
                            # Clean page artifacts from line before adding
                            cleaned_line = re.sub(r'\s*Pag\s+\d+.*$', '', next_line)
                            code_description += " " + cleaned_line
                            j += 1
                        break
                    j += 1

                # Detect major violations
                is_major = "MAJOR VIOLATION" in observations.upper()

                violations.append({
                    "violation_code": violation_code,
                    "violation_title": violation_title,
                    "observations": observations.strip(),
                    "code_description": code_description.strip(),
                    "is_major_violation": is_major,
                    "corrective_action": None,
                    "severity_level": 3 if is_major else 1,
                    "correction_deadline_days": self._extract_deadline_days(observations.strip())
                })

        return violations

    def _extract_deadline_days(self, observations):
        """Extract correction deadline from violation observations"""
        if not observations:
            return None

        deadline_patterns = [
            r'correct(?:ed?)? (?:in|within) (\d+) days?',
            r'fix(?:ed?)? (?:in|within) (\d+) days?',
            r'repair(?:ed?)? (?:in|within) (\d+) days?',
            r'within (\d+) days'
        ]

        for pattern in deadline_patterns:
            matches = re.findall(pattern, observations, re.IGNORECASE)
            if matches:
                try:
                    return int(matches[0])
                except (ValueError, IndexError):
                    pass
        return None

    def _find_program_identifier(self, text):
        """Extract program identifier from PDF"""
        # Look for specific program identifier patterns
        patterns = [
            r'Prog\s+Identifier\s+([A-Z\s]+?)\s*(?:Pag|$)',
            r'Program\s+(?:Identifier|ID)\s*[:\-]?\s*([A-Z\s]+?)\s*(?:Pag|$)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                program_id = match.group(1).strip().upper()
                print(f"Found program identifier: {program_id}")
                return program_id

        print("No program identifier found")
        return None

    def _extract_equipment_comprehensive(self, text):
        """
        Robust equipment extractor with sectionizer + gazetteer.
        - Populates standard fields (capacity, flow, filter, pumps, sanitizer, MD/EQ).
        - Captures oddities into *_notes fields instead of polluting models/types.
        - Conservative: avoids breaking if formats vary; everything optional.
        """
        import re
        from datetime import date

        # ---------------------------- helpers ----------------------------
        def clean(s):
            return re.sub(r"\s+", " ", s).strip(" ,;:") if s else None

        def norm_make(s):
            if not s:
                return None
            s = s.strip()
            # normalize common OCR/casing variants
            s = (s
                 .replace("Sta Rite", "Sta-Rite")
                 .replace("Sta-rite", "Sta-Rite")
                 .replace("starite", "Sta-Rite")
                 .replace("Starite", "Sta-Rite"))
            # canonical forms
            s = s.replace("Sta-Rite", "StaRite")
            s = (s
                 .replace("rolachem", "RolaChem").replace("Rolachem", "RolaChem")
                 .replace("aquastar", "AquaStar").replace("Aquastar", "AquaStar")
                 .replace("pacfab", "PACFAB").replace("Pacfab", "PACFAB"))
            if s != "PACFAB":
                s = " ".join(w.capitalize() for w in s.split())
            return s

        def norm_model(s):
            return clean(s)

        def normalize_date(mmddyy):
            # Reuse project-wide normalizer if it exists on self
            try:
                return self._normalize_date(mmddyy)  # if your class already has it
            except Exception:
                pass
            # Fallback: mm/dd/yyyy or mm/dd/yy → ISO
            m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{2,4})", mmddyy)
            if not m:
                return None
            mm, dd, yyyy = int(m.group(1)), int(m.group(2)), int(m.group(3))
            if yyyy < 100:  # yy → 20yy heuristic
                yyyy += 2000
            try:
                return f"{yyyy:04d}-{mm:02d}-{dd:02d}"
            except Exception:
                return None

        def section(label, blob):
            # find a section that starts with LABEL (loose) and ends before another known label
            labels = ["FILTER", "PUMP", "SAN", "MD", "MAIN DRAIN", "EQ", "EQU", "EQUALIZER"]
            # anchor start
            start = re.search(rf"\b{label}\b[^:\n]*[:\-]?", blob, re.I)
            if not start:
                return None
            start_idx = start.start()
            # find next label after start
            tail = blob[start_idx + 1 :]
            end_idx = None
            for lab in labels:
                m = re.search(rf"\b{lab}\b[^:\n]*[:\-]?", tail, re.I)
                if m:
                    cand = m.start()
                    if cand > 0:
                        end_idx = cand
                        break
            if end_idx is None:
                chunk = blob[start_idx:]
            else:
                chunk = blob[start_idx : start_idx + 1 + end_idx]
            return chunk

        # ---------------------------- regex/gazetteers ----------------------------
        # Makes (longest first keeps "Crystal Water")
        MAKES = [
            "Crystal Water", "AquaStar", "Waterway", "Sta-Rite", "Sta Rite", "RolaChem",
            "Pentair", "Hayward", "PACFAB", "Jandy", "StaRite"
        ]
        makes_sorted = sorted(set(MAKES), key=len, reverse=True)
        MAKE_RE = re.compile(r"\b(" + "|".join(
            [re.sub(r"\s+", r"[ -]?", re.escape(m)) for m in makes_sorted]
        ) + r")\b", re.I)

        MODEL_FAMILIES = [
            r"CCP\d{2,3}", r"TR-?\d{2,3}", r"S8D\d{3}", r"570-\d{4,5}",
            r"FSH-\d{3}", r"VSF\b", r"RC\d{3}SC\b", r"HC\d{4,5}\b",
            r"PE5E-125L\b", r"10AVR\b", r"10AV\b", r"FNSP?\d*\b", r"WFE-\d+\b",
            r"INTELLIFLO3?\b", r"SUPERFLO\b", r"DE6020\b", r"SYSTEM-3\b",
            r"P6E6E\b", r"VS-?SVRS\b", r"WFK-\d+\b", r"TRITON\b", r"WHISPERFLO\b",
            r"S8M\d{3}\b", r"CC520\b", r"TR140C\b", r"S310\b", r"PE5F-126L\b",
            r"VSS?HP270DV2A?S?\b"
        ]
        MODEL_RE = re.compile(r"\b(" + "|".join(MODEL_FAMILIES) + r")\b", re.I)

        TYPE_MAP = [
            (re.compile(r"\bDE\b", re.I), "DE"),
            (re.compile(r"\bcartr?idge\b", re.I), "Cartridge"),
            (re.compile(r"\bsand\b", re.I), "Sand"),
        ]

        CAP_RE   = re.compile(r"\b(\d{1,3}(?:,\d{3})*)\s*gal\b", re.I)
        FLOW_RE  = re.compile(r"\b(\d{2,4})\s*gpm\b", re.I)
        HP_RE    = re.compile(r"\b(\d+(?:\.\d+)?)\s*hp\b", re.I)
        DATE_RE  = re.compile(r"\b(\d{1,2}/\d{1,2}/\d{2,4})\b")
        COUNT_RE = re.compile(r"\(x?\s*(\d+)\)", re.I)
        SUPP_RE  = re.compile(r"\bSUPPLEMENTAL(?:\s+ONLY)?\b", re.I)
        GPD_RE   = re.compile(r"\b\d+(?:\.\d+)?\s*GPD\b", re.I)
        # Feed-rate variants: lbs/day, lb/day, OCR 'ls/day', and 'per day'
        FEED_LBS_RE = re.compile(
            r"\b\d+(?:\.\d+)?\s*(?:l[b]?\s*s?|lb?s?)\s*(?:/|\bper\b)\s*day\b",
            re.I
        )
        PUMP_OR_FILTER_FAMS = re.compile(
            r"\b(?:INTELLIFLO3?|SUPERFLO|WFE-\d+|WFK-\d+|CCP\d{2,3}|TR-?\d{2,3}|FNS)\b",
            re.I
        )

        # ---------------------------- initialize outputs ----------------------------
        data = {
            "pool_capacity_gallons": None,
            "flow_rate_gpm": None,
            "filter_pump_1_make": None, "filter_pump_1_model": None, "filter_pump_1_hp": None,
            "filter_pump_2_make": None, "filter_pump_2_model": None, "filter_pump_2_hp": None,
            "filter_pump_3_make": None, "filter_pump_3_model": None, "filter_pump_3_hp": None,
            "jet_pump_1_make": None, "jet_pump_1_model": None, "jet_pump_1_hp": None,
            "jet_pump_2_make": None, "jet_pump_2_model": None, "jet_pump_2_hp": None,
            "filter_1_type": None, "filter_1_make": None, "filter_1_model": None, "filter_1_capacity_gpm": None,
            "filter_2_type": None, "filter_2_make": None, "filter_2_model": None, "filter_2_capacity_gpm": None,
            "sanitizer_1_type": None, "sanitizer_1_details": None,
            "sanitizer_2_type": None, "sanitizer_2_details": None,
            "main_drain_type": None, "main_drain_model": None, "main_drain_install_date": None,
            "equalizer_model": None, "equalizer_install_date": None,
        }
        notes = {
            "filter_notes": [],
            "pump_notes": [],
            "jet_pump_notes": [],
            "sanitizer_notes": [],
            "main_drain_notes": [],
            "equalizer_notes": [],
            "equipment_notes": [],
        }

        equip_text = text  # keep simple & safe; your caller already passes the right slice

        # ---------------------------- global basics ----------------------------
        cap = CAP_RE.search(equip_text)
        if cap:
            try:
                gallons = int(cap.group(1).replace(",", ""))
                data["pool_capacity_gallons"] = gallons
            except Exception:
                pass

        flow = FLOW_RE.search(equip_text)
        if flow:
            try:
                data["flow_rate_gpm"] = int(flow.group(1))
            except Exception:
                pass

        # ---------------------------- FILTER block ----------------------------
        fil = section("FILTER", equip_text) or equip_text
        if fil:
            # type
            for rx, tname in TYPE_MAP:
                if rx.search(fil):
                    data["filter_1_type"] = tname
                    break
            # make/model
            mk = MAKE_RE.search(fil)
            if mk:
                data["filter_1_make"] = norm_make(mk.group(1))
            mdl = MODEL_RE.search(fil)
            if mdl:
                data["filter_1_model"] = norm_model(mdl.group(1))
            # capacity gpm (often appears near filter)
            capg = re.search(r"\b(\d{2,4})\s*(?:gpm|GPM)\b", fil)
            if capg:
                try:
                    data["filter_1_capacity_gpm"] = int(capg.group(1))
                    if data["filter_1_capacity_gpm"] and data["filter_1_capacity_gpm"] > 400:
                        notes["filter_notes"].append(
                            f"Suspicious capacity filter_1_capacity_gpm={data['filter_1_capacity_gpm']}; retained"
                        )
                except Exception:
                    pass

        # ---------------------------- PUMP block (filter pumps) ----------------------------
        pmp = section("PUMP", equip_text) or equip_text
        if pmp:
            # Capture first three pump makes/models/hp conservatively
            pump_hits = []
            for m in re.finditer(MAKE_RE, pmp):
                mk = norm_make(m.group(1))
                # model nearby
                mo = MODEL_RE.search(pmp, m.end())
                hp = HP_RE.search(pmp, m.end(), m.end() + 40)  # short window for HP
                pump_hits.append((mk, norm_model(mo.group(1)) if mo else None, float(hp.group(1)) if hp else None))
                if len(pump_hits) >= 3:
                    break
            # assign
            if pump_hits:
                for idx, (mk, mo, hp) in enumerate(pump_hits, start=1):
                    data[f"filter_pump_{idx}_make"] = mk or data.get(f"filter_pump_{idx}_make")
                    data[f"filter_pump_{idx}_model"] = mo or data.get(f"filter_pump_{idx}_model")
                    data[f"filter_pump_{idx}_hp"] = hp or data.get(f"filter_pump_{idx}_hp")
            # multiplicity e.g. (x2)
            mult = COUNT_RE.search(pmp)
            if mult and pump_hits:
                notes["pump_notes"].append(f"Detected multiple pumps: x{mult.group(1)}")
            if SUPP_RE.search(pmp):
                notes["pump_notes"].append("SUPPLEMENTAL ONLY in pump section")

        # ---------------------------- JET PUMP (simple heuristic) ----------------------------
        jet = section("JET", equip_text)
        if jet:
            mk = MAKE_RE.search(jet)
            if mk:
                data["jet_pump_1_make"] = norm_make(mk.group(1))
            mdl = MODEL_RE.search(jet)
            if mdl:
                data["jet_pump_1_model"] = norm_model(mdl.group(1))
            hp = HP_RE.search(jet)
            if hp:
                try:
                    data["jet_pump_1_hp"] = float(hp.group(1))
                except Exception:
                    pass

        # ---------------------------- SAN (sanitizer) block ----------------------------
        san = section("SAN", equip_text) or equip_text
        if san:
            # try to capture details string (kept loose)
            # common tokens like RC103SC, feed rates, etc.
            det_m = re.search(r"(RC\d{3}SC\b|\d+(?:\.\d+)?\s*(?:GPD|l[b]?\s*s?|lb?s?)\s*(?:/|\bper\b)\s*day\b)", san, re.I)
            if det_m:
                data["sanitizer_1_details"] = clean(det_m.group(1))

            # Infer sanitizer type from common keywords if not set yet
            if not data.get("sanitizer_1_type"):
                if re.search(r"\b(liq|liquid|feeder|rc103sc)\b", san, re.I):
                    data["sanitizer_1_type"] = "Liquid"
                elif re.search(r"\b(tablet|tabs?)\b", san, re.I):
                    data["sanitizer_1_type"] = "Tablet"
                elif re.search(r"\b(cal(?:cium)?\s*hypo)\b", san, re.I):
                    data["sanitizer_1_type"] = "Cal Hypo"
                elif re.search(r"\b(gas|chlorine\s*gas)\b", san, re.I):
                    data["sanitizer_1_type"] = "Gas"
                elif re.search(r"\b(salt|swg|chlorinator)\b", san, re.I):
                    data["sanitizer_1_type"] = "Salt"

            # Move feed-rates into notes; clear details
            if data.get("sanitizer_1_details"):
                det = data["sanitizer_1_details"]
                moved = False
                if GPD_RE.search(det):
                    notes["sanitizer_notes"].append(f"Feed rate noted: {det}")
                    moved = True
                if FEED_LBS_RE.search(det):
                    notes["sanitizer_notes"].append(f"Feed rate noted: {det}")
                    moved = True
                if moved:
                    data["sanitizer_1_details"] = None

        # ---------------------------- MAIN DRAIN (MD) block ----------------------------
        md = section("MAIN DRAIN", equip_text) or section("MD", equip_text)
        if md:
            # model: includes 10AV/10AVR and Aquastar/AquaStar products
            mdl = re.search(r"\b(10AVR?|AquaStar\s*10AVR?)\b", md, re.I)
            if mdl:
                data["main_drain_model"] = norm_model(mdl.group(1).replace("Aquastar", "AquaStar"))
            data["main_drain_type"] = "Main Drain"  # minimal type label
            dt = DATE_RE.search(md)
            if dt:
                iso = normalize_date(dt.group(1))
                data["main_drain_install_date"] = iso
                # sanity check future-looking dates (> current year + 1)
                try:
                    yyyy = int(iso.split("-")[0])
                    if yyyy > date.today().year + 1:
                        notes["main_drain_notes"].append(f"Install date looks future: {iso}")
                except Exception:
                    pass
            if SUPP_RE.search(md):
                notes["main_drain_notes"].append("SUPPLEMENTAL ONLY in main drain section")

        # ---------------------------- EQ (equalizer) block ----------------------------
        eq = section("EQ", equip_text) or section("EQUALIZER", equip_text)
        if eq:
            mdl = MODEL_RE.search(eq)
            if mdl:
                data["equalizer_model"] = norm_model(mdl.group(1))
            dt = DATE_RE.search(eq)
            if dt:
                iso = normalize_date(dt.group(1))
                data["equalizer_install_date"] = iso
            if SUPP_RE.search(eq):
                notes["equalizer_notes"].append("SUPPLEMENTAL ONLY in EQ section")
            # Guard: if EQ model looks like a pump/filter family, move to notes instead
            if data.get("equalizer_model") and PUMP_OR_FILTER_FAMS.search(data["equalizer_model"]):
                notes["equalizer_notes"].append(
                    f"Likely non-equalizer token in EQ model: {data['equalizer_model']}"
                )
                data["equalizer_model"] = None

        # ---------------------------- final cleanup ----------------------------
        # Drop dangling commas/semis and 1-char tokens
        for k, v in list(data.items()):
            if isinstance(v, str):
                vv = v.strip().strip(",;")
                if len(vv) == 1:
                    notes["equipment_notes"].append(f"Dropped 1-char token from {k}: '{vv}'")
                    data[k] = None
                else:
                    data[k] = vv or None

        # Drop numeric-only or too-short "models" (e.g., "123")
        for key in ("filter_pump_1_model","filter_pump_2_model","filter_pump_3_model",
                    "jet_pump_1_model","jet_pump_2_model",
                    "filter_1_model","filter_2_model"):
            val = data.get(key)
            if isinstance(val, str):
                v = val.strip().strip(",;")
                if v.isdigit() or len(v) < 3:
                    notes["equipment_notes"].append(f"Dropped weak model token from {key}: '{v}'")
                    data[key] = None

        # Join notes into strings (DB columns are TEXT)
        for nk in list(notes.keys()):
            s = "; ".join(x for x in notes[nk] if x)
            data[nk] = s if s else None

        return data


    def _extract_water_chemistry(self, text):
        """
        Lightweight, defensive parser for water chemistry lines.
        Returns only fields it can confidently extract; never raises.
        """
        import re

        def find(pattern, flags=re.I):
            m = re.search(pattern, text, flags)
            return m.group(1) if m else None

        def to_float(val):
            try:
                return float(val)
            except Exception:
                return None

        data = {}
        try:
            # Free/Total/Combined Chlorine
            fc = find(r"\b(?:free\s*chlorine|fc)\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:ppm|mg/?L)?")
            tc = find(r"\b(?:total\s*chlorine|tc)\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:ppm|mg/?L)?")
            cc = find(r"\b(?:combined\s*chlorine|cc)\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:ppm|mg/?L)?")

            # pH
            ph = find(r"\bph\b\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?)", flags=re.I)

            # Alkalinity (TA), Cyanuric Acid (CYA), Calcium Hardness (CH)
            ta  = find(r"\b(?:total\s*alkalinity|alkalinity|ta)\s*[:=]?\s*([0-9]+)\s*(?:ppm|mg/?L)?")
            cya = find(r"\b(?:cyanuric\s*acid|stabilizer|cya)\s*[:=]?\s*([0-9]+)\s*(?:ppm|mg/?L)?")
            ch  = find(r"\b(?:calcium\s*hardness|hardness|ch)\s*[:=]?\s*([0-9]+)\s*(?:ppm|mg/?L)?")

            # Temperature (Â°F/Â°C)
            temp = find(r"\b(?:temp|temperature)\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:Â°?\s*[FC]|F|C)?")

            if fc is not None:  data["free_chlorine"]     = to_float(fc)
            if tc is not None:  data["total_chlorine"]    = to_float(tc)
            if cc is not None:  data["combined_chlorine"] = to_float(cc)
            if ph is not None:  data["ph"]                = to_float(ph)
            if ta is not None:  data["alkalinity_ppm"]    = int(ta)
            if cya is not None: data["cyanuric_acid_ppm"] = int(cya)
            if ch is not None:  data["calcium_hardness"]  = int(ch)
            if temp is not None:data["water_temp"]        = to_float(temp)

        except Exception as e:
            self.error_handler.log_warning("Water chemistry extract", f"Unexpected error: {e}")

        return data

    def _extract_report_notes(self, text):
        """Extract report notes from the Notes section."""
        lines = text.split("\n")
        notes_lines = []
        capturing = False

        for line in lines:
            if line.strip() == "Notes":
                capturing = True
                continue
            elif capturing:
                # Stop at major sections
                if line.strip() in ["Accepted By", "Reviewed", "Beginning in"] or line.startswith("County of"):
                    break
                elif line.strip():  # Non-empty line
                    notes_lines.append(line.strip())

        return "\n".join(notes_lines) if notes_lines else None
