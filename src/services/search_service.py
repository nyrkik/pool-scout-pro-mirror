#!/usr/bin/env python3
"""
EMD Website Search Service - Pool Scout Pro
CLEAN VERSION: No webpage date extraction - dates verified during PDF processing
ENHANCED: Proper duplicate detection using inspection ID extraction + EMD duplicate detection + Database filtering
ENHANCED: Dual logging (console + file) while preserving immediate feedback
ENHANCED: Timeout monitoring to diagnose delays
ENHANCED: Date change logging and saved reports counting
ENHANCED: Inspection ID extraction during search phase
ENHANCED: Mark saved facilities instead of filtering them out
"""

import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException, StaleElementReferenceException

from core.browser import BrowserManager
from core.error_handler import ErrorHandler, with_error_handling, CommonCleanup
from core.utilities import DateUtilities, NameUtilities, ValidationUtilities, TextUtilities
from services.database_service import DatabaseService
from core.database_config import db_config

try:
 from services.search_progress_service import SearchProgressService
except ImportError:
 SearchProgressService = None

class SearchService:
 def __init__(self, progress_service=None):
     self.browser_manager = BrowserManager()
     self.db_service = DatabaseService()
     self.progress_service = progress_service or (SearchProgressService() if SearchProgressService else None)
     self.error_handler = ErrorHandler(__name__)

     self.current_driver = None
     self.session_start_time = None
     self.session_timeout = 300

     # Track last search date for change detection
     self.last_search_date = None

 def log_date_change(self, new_date):
     """Log when user changes the search date"""
     if self.last_search_date != new_date:
         if self.last_search_date:
             self.error_handler.log_info("Date Change", f"User changed search date from {self.last_search_date} to {new_date}", {
                 'previous_date': self.last_search_date,
                 'new_date': new_date
             })
             print(f"📅 Date changed: {self.last_search_date} → {new_date}")
         else:
             self.error_handler.log_info("Initial Date", f"User set initial search date to {new_date}", {
                 'initial_date': new_date
             })
             print(f"📅 Initial date set: {new_date}")

         self.last_search_date = new_date

 def get_saved_reports_count(self, date):
     """Get count of already saved reports for the given date"""
     try:
         import sqlite3
         conn = sqlite3.connect(db_config.inspection_db_path, timeout=10)
         cursor = conn.cursor()

         # Count reports for the specific date
         cursor.execute("""
             SELECT COUNT(*)
             FROM inspection_reports
             WHERE inspection_date = ?
         """, (date,))
         count = cursor.fetchone()[0]

         # Also get facility names for reference
         cursor.execute("""
             SELECT f.name, ir.pdf_filename
             FROM inspection_reports ir
             JOIN facilities f ON ir.facility_id = f.id
             WHERE ir.inspection_date = ?
             ORDER BY f.name
             LIMIT 10
         """, (date,))
         saved_facilities = cursor.fetchall()

         conn.close()

         self.error_handler.log_info("Saved Reports Check", f"Found {count} already saved reports for {date}", {
             'date': date,
             'saved_count': count,
             'sample_facilities': [f[0] for f in saved_facilities[:5]]  # First 5 names
         })

         if count > 0:
             print(f"💾 Found {count} already saved reports for {date}")
             if saved_facilities:
                 print(f"   Sample: {', '.join([f[0] for f in saved_facilities[:3]])}{'...' if len(saved_facilities) > 3 else ''}")

         return count, saved_facilities

     except Exception as e:
         self.error_handler.log_error("Saved reports check", e, {'date': date})
         return 0, []

 @with_error_handling("EMD search", default_return={'facilities': [], 'emd_duplicate_count': 0, 'emd_duplicate_names': []})
 def search_emd_for_date(self, start_date, end_date=None, max_load_more=10):
     search_start_time = time.time()

     # Log date change
     self.log_date_change(start_date)

     # Check for already saved reports
     saved_count, saved_facilities = self.get_saved_reports_count(start_date)

     if end_date is None:
         end_date = start_date

     print(f"🚀 Starting EMD search for {start_date} to {end_date}")
     self.error_handler.log_info("EMD Search Start", f"Starting search for date range {start_date} to {end_date}", {
         'start_date': start_date,
         'end_date': end_date,
         'max_load_more': max_load_more,
         'existing_saved_count': saved_count
     })

     try:
         formatted_start = DateUtilities.convert_to_pacific_date(start_date)
         formatted_end = DateUtilities.convert_to_pacific_date(end_date)
         formatted_range = f"{formatted_start} to {formatted_end}"
     except ValueError as e:
         self.error_handler.log_error("Date conversion", e, {
             'start_date': start_date,
             'end_date': end_date
         })
         return {'facilities': [], 'emd_duplicate_count': 0, 'emd_duplicate_names': []}

     print(f"📅 Searching EMD for date range: {start_date} to {end_date} (formatted: {formatted_range})")

     driver = None
     try:
         # Monitor session creation time
         session_create_start = time.time()
         driver = self._get_or_create_session()
         session_create_time = time.time() - session_create_start

         self.error_handler.log_info("Session Creation Time", f"Browser session created in {session_create_time:.2f}s", {
             'creation_time_seconds': session_create_time
         })

         # Monitor navigation time
         nav_start = time.time()
         driver.get("https://inspections.myhealthdepartment.com/sacramento/program-rec-health")
         nav_time = time.time() - nav_start

         print("🔄 Navigated to EMD page")
         self.error_handler.log_info("EMD Navigation", f"Successfully navigated to EMD website in {nav_time:.2f}s", {
             'navigation_time_seconds': nav_time
         })

         # Monitor page load time
         page_load_start = time.time()
         WebDriverWait(driver, 15).until(
             EC.presence_of_element_located((By.CLASS_NAME, "alt-datePicker"))
         )
         page_load_time = time.time() - page_load_start

         self.error_handler.log_info("Page Load Time", f"Page loaded and ready in {page_load_time:.2f}s", {
             'page_load_time_seconds': page_load_time
         })

         # Set the date filter
         filter_start = time.time()
         self._set_date_filter(driver, formatted_start, formatted_end)
         filter_time = time.time() - filter_start

         self.error_handler.log_info("Date Filter Time", f"Date filter applied in {filter_time:.2f}s", {
             'filter_time_seconds': filter_time
         })

         time.sleep(5)

         result_elements = driver.find_elements(By.CSS_SELECTOR, ".flex-row")
         print(f"🔍 Found {len(result_elements)} facilities after filtering")
         self.error_handler.log_info("EMD Initial Results", f"Found {len(result_elements)} facilities after date filtering", {
             'result_count': len(result_elements),
             'date_range': formatted_range
         })

         if not result_elements:
             print("❌ No results found for this date")
             self.error_handler.log_info("EMD No Results", f"No facilities found for date range {formatted_range}")
             return {'facilities': [], 'emd_duplicate_count': 0, 'emd_duplicate_names': []}

         # Monitor load more time
         load_more_start = time.time()
         self._handle_load_more_with_progress(driver, max_load_more)
         load_more_time = time.time() - load_more_start

         self.error_handler.log_info("Load More Time", f"Load More process completed in {load_more_time:.2f}s", {
             'load_more_time_seconds': load_more_time
         })

         # Monitor extraction time
         extraction_start = time.time()
         all_facilities = self._extract_facilities_from_page(driver, start_date)
         extraction_time = time.time() - extraction_start

         self.error_handler.log_info("Extraction Time", f"Facility extraction completed in {extraction_time:.2f}s", {
             'extraction_time_seconds': extraction_time,
             'facilities_extracted': len(all_facilities)
         })

         # Process EMD duplicates
         emd_clean_data = self._detect_and_remove_emd_duplicates(all_facilities)

         # Mark saved facilities instead of filtering them out
         final_clean_data = self._mark_saved_facilities(emd_clean_data)

         total_search_time = time.time() - search_start_time

         print(f"✅ Found {len(all_facilities)} total facilities")
         print(f"🔄 Removed {emd_clean_data['emd_duplicate_count']} EMD duplicates")
         print(f"💾 Marked {len([f for f in final_clean_data['facilities'] if f.get('saved')])} already saved facilities")
         print(f"✨ Returning {len(final_clean_data['facilities'])} total facilities ({len([f for f in final_clean_data['facilities'] if not f.get('saved')])} unsaved)")

         # Enhanced completion logging with saved reports summary
         self.error_handler.log_info("EMD Search Complete", f"EMD search completed successfully in {total_search_time:.2f}s", {
             'total_found': len(all_facilities),
             'emd_duplicates_removed': emd_clean_data['emd_duplicate_count'],
             'already_saved_marked': len([f for f in final_clean_data['facilities'] if f.get('saved')]),
             'final_total_count': len(final_clean_data['facilities']),
             'final_unsaved_count': len([f for f in final_clean_data['facilities'] if not f.get('saved')]),
             'date_range': formatted_range,
             'total_search_time_seconds': total_search_time,
             'previously_saved_count': saved_count,
             'timing_breakdown': {
                 'session_creation': session_create_time,
                 'navigation': nav_time,
                 'page_load': page_load_time,
                 'date_filter': filter_time,
                 'load_more': load_more_time,
                 'extraction': extraction_time
             }
         })

         return final_clean_data

     except Exception as e:
         total_failure_time = time.time() - search_start_time
         self.error_handler.log_error("EMD search general error", e, {
             'time_before_failure_seconds': total_failure_time
         })
         self._cleanup_current_session()
         return {'facilities': [], 'emd_duplicate_count': 0, 'emd_duplicate_names': []}

 def _mark_saved_facilities(self, emd_data):
     """
     Mark facilities that already exist in database as saved=True based on inspection ID.
     """
     facilities = emd_data.get('facilities', [])
     if not facilities:
         return emd_data

     try:
         marked_facilities = []
         saved_count = 0
         saved_names = []

         for facility in facilities:
             inspection_id = facility.get('inspection_id')
             if not inspection_id:
                 facility['saved'] = False
                 marked_facilities.append(facility)
                 continue

             # Check if this inspection ID already exists in database
             if self._is_inspection_saved(inspection_id):
                 facility['saved'] = True
                 facility_name = facility.get('name', 'Unknown')
                 print(f"💾 Marked as saved: {facility_name} (ID: {inspection_id})")
                 saved_count += 1
                 saved_names.append(facility_name)
             else:
                 facility['saved'] = False
             
             marked_facilities.append(facility)

         if saved_count > 0:
             self.error_handler.log_info("Database Marking", f"Marked {saved_count} already saved facilities", {
                 'saved_count': saved_count,
                 'total_count': len(marked_facilities),
                 'saved_facility_names': saved_names
             })

         # Return updated data with all facilities marked properly
         return {
             'facilities': marked_facilities,
             'emd_duplicate_count': emd_data['emd_duplicate_count'],
             'emd_duplicate_names': emd_data['emd_duplicate_names']
         }

     except Exception as e:
         self.error_handler.log_error("Mark saved facilities", e)
         return emd_data

 def _is_inspection_saved(self, inspection_id):
     """
     Check if inspection ID already exists in database.
     """
     try:
         import sqlite3
         conn = sqlite3.connect(db_config.inspection_db_path, timeout=10)
         cursor = conn.cursor()
         cursor.execute("SELECT COUNT(*) FROM inspection_reports WHERE inspection_id = ?", (inspection_id,))
         count = cursor.fetchone()[0]
         conn.close()
         return count > 0
     except Exception as e:
         self.error_handler.log_error("Database inspection check", e)
         return False

 def _detect_and_remove_emd_duplicates(self, facilities):
     """
     Detect and remove EMD duplicates based on inspection ID extraction.
     Returns clean facilities list + duplicate count + duplicate names.
     """
     if not facilities:
         return {'facilities': [], 'emd_duplicate_count': 0, 'emd_duplicate_names': []}

     try:
         inspection_id_map = {}
         duplicate_names = []
         clean_facilities = []

         for facility in facilities:
             # Use inspection_id that was already extracted during search
             inspection_id = facility.get('inspection_id')

             if not inspection_id:
                 # No inspection ID found, keep facility
                 clean_facilities.append(facility)
                 continue

             if inspection_id in inspection_id_map:
                 # This is a duplicate - store the name and skip
                 duplicate_names.append(facility.get('name', 'Unknown'))
                 print(f"🔄 EMD Duplicate detected: {facility.get('name')} (ID: {inspection_id})")
             else:
                 # First occurrence - keep it and track the ID
                 inspection_id_map[inspection_id] = True
                 clean_facilities.append(facility)

         if len(duplicate_names) > 0:
             self.error_handler.log_info("EMD Duplicate Detection", f"Detected {len(duplicate_names)} EMD duplicates", {
                 'duplicate_count': len(duplicate_names),
                 'duplicate_names': duplicate_names
             })

         return {
             'facilities': clean_facilities,
             'emd_duplicate_count': len(duplicate_names),
             'emd_duplicate_names': duplicate_names
         }

     except Exception as e:
         self.error_handler.log_error("EMD duplicate detection", e)
         # On error, return original list without duplicate detection
         return {'facilities': facilities, 'emd_duplicate_count': 0, 'emd_duplicate_names': []}

 def _get_or_create_session(self):
     self._cleanup_current_session()

     try:
         browser_start = time.time()
         self.current_driver = self.browser_manager.create_driver()
         browser_time = time.time() - browser_start

         self.session_start_time = time.time()
         print("🔄 Created new browser session")
         self.error_handler.log_info("Browser Session", f"Created new browser session in {browser_time:.2f}s", {
             'browser_startup_time_seconds': browser_time
         })
         return self.current_driver
     except Exception as e:
         self.error_handler.log_error("Browser session creation", e)
         raise

 def _set_date_filter(self, driver, start_date, end_date):
     try:
         date_range = f"{start_date} to {end_date}"

         filter_input = driver.find_element(By.CLASS_NAME, "alt-datePicker")

         current_value = filter_input.get_attribute("value")
         print(f"📅 Current date filter: '{current_value}'")

         driver.execute_script("arguments[0].value = '';", filter_input)
         driver.execute_script("arguments[0].focus();", filter_input)
         time.sleep(1)

         driver.execute_script(f"arguments[0].value = '{date_range}';", filter_input)

         driver.execute_script("arguments[0].dispatchEvent(new Event('input', {bubbles: true}));", filter_input)
         driver.execute_script("arguments[0].dispatchEvent(new Event('change', {bubbles: true}));", filter_input)
         driver.execute_script("arguments[0].blur();", filter_input)

         new_value = filter_input.get_attribute("value")
         print(f"📅 Set date filter to: '{date_range}' (verified: '{new_value}')")
         self.error_handler.log_info("Date Filter", f"Set date filter to: {date_range}", {
             'date_range': date_range,
             'verified_value': new_value
         })

         print("⏳ Waiting for date filter to process...")
         time.sleep(5)

     except Exception as e:
         self.error_handler.log_error("Date filter setting", e)
         raise

 def _handle_load_more_with_progress(self, driver, max_attempts):
     load_attempts = 0

     while load_attempts < max_attempts:
         try:
             load_more_buttons = driver.find_elements(By.CSS_SELECTOR, ".load-more-results-button")

             if not load_more_buttons:
                 print("📋 No Load More button found")
                 break

             load_more_button = load_more_buttons[0]
             if not load_more_button.is_enabled() or not load_more_button.is_displayed():
                 print("📋 Load More button disabled or hidden")
                 break

             current_facilities = driver.find_elements(By.CSS_SELECTOR, '.flex-row')
             current_count = len(current_facilities)

             click_start = time.time()
             driver.execute_script("arguments[0].click();", load_more_button)
             load_attempts += 1

             print(f"🔄 Load More clicked (attempt {load_attempts}/{max_attempts})")
             self.error_handler.log_info("Load More", f"Load More attempt {load_attempts}/{max_attempts}", {
                 'attempt': load_attempts,
                 'max_attempts': max_attempts,
                 'current_count': current_count
             })

             time.sleep(5)
             click_time = time.time() - click_start

             new_facilities = driver.find_elements(By.CSS_SELECTOR, '.flex-row')
             new_count = len(new_facilities)

             print(f"📋 Results: {current_count} -> {new_count} ({new_count - current_count} new)")
             self.error_handler.log_info("Load More Result", f"Load More completed in {click_time:.2f}s", {
                 'load_more_time_seconds': click_time,
                 'before_count': current_count,
                 'after_count': new_count,
                 'new_items': new_count - current_count
             })

             if new_count <= current_count:
                 print("📋 No new results loaded, stopping")
                 self.error_handler.log_info("Load More Complete", "No new results loaded, stopping load more attempts")
                 break

         except Exception as e:
             self.error_handler.log_error("Load More", e)
             break

 def _extract_facilities_from_page(self, driver, search_date):
     facilities = []

     try:
         facility_elements = driver.find_elements(By.CSS_SELECTOR, '.flex-row')
         print(f"📋 Processing {len(facility_elements)} facility elements")
         self.error_handler.log_info("Facility Extraction", f"Processing {len(facility_elements)} facility elements", {
             'element_count': len(facility_elements),
             'search_date': search_date
         })

         for i, element in enumerate(facility_elements):
             try:
                 facility_data = self._extract_single_facility(driver, element, i, search_date)
                 if facility_data:
                     facilities.append(facility_data)

             except Exception as e:
                 self.error_handler.log_error("Facility extraction", e)
                 continue

         self.error_handler.log_info("Facility Extraction Complete", f"Successfully extracted {len(facilities)} facilities", {
             'extracted_count': len(facilities),
             'total_elements': len(facility_elements)
         })

     except Exception as e:
         self.error_handler.log_error("Facilities page extraction", e)

     return facilities

 def _extract_single_facility(self, driver, element, index, search_date):
     try:
         name_links = element.find_elements(By.CSS_SELECTOR, 'h4.establishment-list-name a')
         if not name_links:
             return None

         facility_name = name_links[0].text.strip()
         facility_url = name_links[0].get_attribute('href')

         address_elements = element.find_elements(By.CSS_SELECTOR, '.establishment-list-address')
         address = address_elements[0].text.strip() if address_elements else "Unknown"
         cleaned_address = NameUtilities.clean_address_string(address) if address else "Unknown"

         if index < 5:
             print(f"🏢 Facility {index + 1}: '{facility_name}'")
             print(f"   Address: {cleaned_address}")
             print(f"   Search date: {search_date}")

         pdf_url = self._find_pdf_url_for_facility_element(element)
         
         # Extract inspection ID during search phase
         inspection_id = None
         if pdf_url:
             inspection_id = TextUtilities.extract_inspection_id_from_url(pdf_url)
             if index < 5 and inspection_id:
                 print(f"   Inspection ID: {inspection_id}")

         return {
             'name': facility_name,
             'url': facility_url,
             'pdf_url': pdf_url,
             'inspection_id': inspection_id,
             'display_address': cleaned_address,
             'inspection_date': search_date,
             'saved': False  # Default to False, will be marked True by _mark_saved_facilities
         }

     except Exception as e:
         self.error_handler.log_error("Single facility extraction", e)
         return None

 def _find_pdf_url_for_facility_element(self, element):
     try:
         inspection_buttons = element.find_elements(By.CSS_SELECTOR, '.view-inspections-button')
         if inspection_buttons:
             inspection_url = inspection_buttons[0].get_attribute('href')
             return inspection_url

     except Exception as e:
         self.error_handler.log_warning("PDF URL extraction", f"Could not find PDF for facility element", {'error': str(e)})
     return None

 def _cleanup_current_session(self):
     if self.current_driver:
         try:
             self.current_driver.quit()
         except:
             pass
         self.current_driver = None
         self.session_start_time = None

 def manual_cleanup_session(self):
     try:
         self._cleanup_current_session()
         print("✅ Manual cleanup completed")
         self.error_handler.log_info("Session Cleanup", "Manual cleanup completed")
     except Exception as e:
         self.error_handler.log_error("Manual cleanup", e)

 def cleanup_session(self):
     self.manual_cleanup_session()

 def get_shared_driver(self):
     return self.current_driver
