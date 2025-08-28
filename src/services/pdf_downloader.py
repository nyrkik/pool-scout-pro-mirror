#!/usr/bin/env python3
import time
import os
import requests
from pathlib import Path
from selenium.webdriver.common.by import By
from core.browser import BrowserManager
from core.error_handler import ErrorHandler, with_error_handling, CommonCleanup
from core.utilities import NameUtilities, ValidationUtilities, FileUtilities
from .pdf_extractor import PDFExtractor
from core.settings import settings
from .download_lock_service import DownloadLockService

class PDFDownloader:
    def __init__(self, shared_driver=None):
        self.browser_manager = BrowserManager()
        self.extractor = PDFExtractor()
        self.shared_driver = shared_driver
        self.error_handler = ErrorHandler(__name__)
        self.lock_service = DownloadLockService()
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
        from datetime import datetime
        current_year = str(datetime.now().year)
        base_path = Path(settings.pdf_download_path)
        self.download_path = base_path / current_year
        self.download_path.mkdir(parents=True, exist_ok=True)
        print(f"📁 Download path: {self.download_path}")

    @with_error_handling("PDF downloads", default_return={'success': False, 'code': 'ERROR', 'successful': 0, 'failed': 0, 'results': []})
    def download_pdfs_from_facilities(self, facilities_data):
        print(f"🔧 DEBUG: facilities_data type: {type(facilities_data)}")
        print(f"🔧 DEBUG: facilities_data length: {len(facilities_data) if facilities_data else 'None'}")
        if facilities_data:
            print(f"🔧 DEBUG: First facility: {facilities_data[0]}")

        if not facilities_data:

            return {'success': False, 'code': 'NO_INPUT', 'message': 'No facilities to process.', 'successful': 0, 'failed': 0, 'results': []}

        job_id = self._make_job_id()
        acquired, info = self.lock_service.acquire(job_id=job_id)
        if not acquired:
            msg = info.get("message", "Download already in progress")
            return {'success': False, 'code': 'ALREADY_RUNNING', 'message': msg, 'successful': 0, 'failed': 0, 'results': []}

        print(f"🔄 Starting PDF downloads for {len(facilities_data)} facilities (job {job_id})")
        successful_downloads, failed_downloads, results = 0, 0, []
        driver = self.shared_driver or self.browser_manager.create_driver()
        print(f"🔧 DEBUG: Driver created successfully: {driver}")
        print(f"🔧 DEBUG: Starting facility loop with {len(facilities_data)} facilities")

        try:
            for i, facility in enumerate(facilities_data, 1):
                facility_name = facility.get('name', 'Unknown')
                pdf_url = facility.get('pdf_url') or facility.get('url')
                print(f"\n🔄 [{i}/{len(facilities_data)}] Processing: {facility_name}")
                print(f"🔍 DEBUG: facility_name='{facility_name}'")
                print(f"🔍 DEBUG: pdf_url='{pdf_url}'")
                print(f"🔍 DEBUG: facility keys={list(facility.keys())}")

                from core.utilities import TextUtilities
                inspection_id = TextUtilities.extract_inspection_id_from_url(pdf_url)
                inspection_date = facility.get('inspection_date')
                filename = FileUtilities.generate_inspection_filename(facility_name, inspection_id, inspection_date)
                filepath = self.download_path / filename

                if self._download_pdf_file(pdf_url, filepath, driver):
                    try:
                        extraction_result = self.extractor.extract_and_save(
                            pdf_path=str(filepath), facility_name=facility_name, inspection_id=inspection_id)
                        if extraction_result:
                            successful_downloads += 1
                            results.append({'facility': facility_name, 'success': True, 'filename': filename})
                        else:
                            failed_downloads += 1
                            results.append({'facility': facility_name, 'success': False, 'error': 'Extraction failed'})
                    except Exception as e:
                        self.error_handler.log_error("PDF extraction", e, {'facility': facility_name, 'filename': filename})
                        failed_downloads += 1
                        results.append({'facility': facility_name, 'success': False, 'error': f'Extraction error: {str(e)}'})
                else:
                    failed_downloads += 1
                    results.append({'facility': facility_name, 'success': False, 'error': 'Download failed'})

                if i < len(facilities_data):
                    time.sleep(2)

        finally:
            # CORRECTED: More robust cleanup block
            print("--- Starting final cleanup ---")
            try:
                if not self.shared_driver and 'driver' in locals() and driver:
                    print("Attempting to close browser session...")
                    CommonCleanup.close_browser_driver(driver)
                    print("Browser session closed.")
            except Exception as e:
                self.error_handler.log_warning("Browser cleanup failed", f"Could not close browser session cleanly: {e}")

            try:
                print("Attempting to release download lock...")
                self.lock_service.release()
                print("Download lock released.")
            except Exception as e:
                self.error_handler.log_warning("Lock release failed", f"Could not release lock cleanly: {e}")

            print("--- Final cleanup finished ---")

        print(f"\n🎯 Download Summary (job {job_id}):\n   ✅ Successful: {successful_downloads}\n   ❌ Failed: {failed_downloads}")
        return {'success': True, 'code': 'OK', 'successful': successful_downloads, 'failed': failed_downloads, 'results': results, 'job_id': job_id}

    def _download_pdf_file(self, pdf_url, filepath, driver):
        try:
            print(f"⬇️ Downloading: {pdf_url}")
            if not driver: return False

            driver.get(pdf_url)
            time.sleep(2)

            pdf_link_element = driver.find_element(By.PARTIAL_LINK_TEXT, "View Original Inspection PDF")
            pdf_href = pdf_link_element.get_attribute("href")
            if not pdf_href: return False

            actual_pdf_url = ("https://inspections.myhealthdepartment.com" + pdf_href) if pdf_href.startswith("/") else pdf_href
            print(f"📎 Found PDF link: {actual_pdf_url}")

            cookies = {c["name"]: c["value"] for c in driver.get_cookies()}
            self.session.cookies.update(cookies)
            response = self.session.get(actual_pdf_url, timeout=30)
            response.raise_for_status()

            with open(filepath, 'wb') as f:
                f.write(response.content)

            if filepath.exists() and filepath.stat().st_size > 1000:
                print(f"✅ Downloaded: {filepath.name}")
                return True
            return False
        except Exception as e:
            self.error_handler.log_error("PDF download", e, {'pdf_url': pdf_url, 'filepath': str(filepath)})
            return False

    def _make_job_id(self):
        import datetime, os
        return f"{datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}-{os.getpid()}"
