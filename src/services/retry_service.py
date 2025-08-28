#!/usr/bin/env python3
"""
Retry Service for Failed PDF Downloads
Automatically processes failed download records for retry

Key responsibilities:
- Check for failed downloads ready for retry
- Use PDFDownloader to retry failed records
- Update retry status in database
- Clean up old completed/failed records
- Run as background service via systemd timer

External dependencies:
- services.failed_download_service.FailedDownloadService
- services.pdf_downloader.PDFDownloader
- core.error_handler.ErrorHandler
- core.browser.BrowserManager
"""

import sys
import os
import time
from datetime import datetime

# Add path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.error_handler import ErrorHandler, CommonCleanup
from core.browser import BrowserManager
from services.failed_download_service import FailedDownloadService
from services.pdf_extractor import PDFExtractor
from core.utilities import ValidationUtilities, FileUtilities, TextUtilities
from core.settings import settings
import requests
from pathlib import Path

class RetryService:
   """Background service for retrying failed PDF downloads"""
   
   def __init__(self):
       self.error_handler = ErrorHandler(__name__)
       self.failed_download_service = FailedDownloadService()
       self.browser_manager = BrowserManager()
       self.extractor = PDFExtractor()
       
       # Initialize HTTP session for downloads
       self.session = requests.Session()
       self.session.headers.update({
           'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
           'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
           'Accept-Language': 'en-US,en;q=0.9',
           'Accept-Encoding': 'gzip, deflate, br',
           'Connection': 'keep-alive',
           'Upgrade-Insecure-Requests': '1'
       })
       
       # Set up download path
       current_year = str(datetime.now().year)
       base_path = Path(settings.pdf_download_path)
       self.download_path = base_path / current_year
       self.download_path.mkdir(parents=True, exist_ok=True)
       
       print(f"🔄 Retry Service initialized - Download path: {self.download_path}")
   
   def run_retry_cycle(self):
       """Run one cycle of retry processing"""
       try:
           print(f"\n🔄 Starting retry cycle at {datetime.now().isoformat()}")
           
           # Get statistics first
           stats = self.failed_download_service.get_failed_download_stats()
           ready_count = stats.get('ready_for_retry', 0)
           
           if ready_count == 0:
               print("✅ No records ready for retry")
               return {'processed': 0, 'successful': 0, 'failed': 0}
           
           print(f"📋 Found {ready_count} records ready for retry")
           
           # Get records ready for retry (limit to avoid overwhelming)
           retry_records = self.failed_download_service.get_records_ready_for_retry(limit=5)
           
           if not retry_records:
               print("ℹ️ No records returned for retry")
               return {'processed': 0, 'successful': 0, 'failed': 0}
           
           # Process retries
           results = self._process_retry_records(retry_records)
           
           # Clean up old records (daily cleanup)
           if datetime.now().hour == 2:  # Run cleanup at 2 AM
               print("🧹 Running daily cleanup of old records...")
               cleaned = self.failed_download_service.cleanup_old_records(days_old=7)
               print(f"🧹 Cleaned up {cleaned} old records")
           
           print(f"✅ Retry cycle complete: {results['successful']} successful, {results['failed']} failed")
           return results
           
       except Exception as e:
           self.error_handler.log_error("Retry cycle", e)
           return {'processed': 0, 'successful': 0, 'failed': 0, 'error': str(e)}
   
   def _process_retry_records(self, retry_records):
       """Process individual retry records"""
       successful = 0
       failed = 0
       driver = None
       
       try:
           # Create browser driver for retries
           driver = self.browser_manager.create_driver()
           print(f"🌐 Created browser session for {len(retry_records)} retries")
           
           for i, record in enumerate(retry_records, 1):
               record_id = record['id']
               facility_name = record['facility_name']
               pdf_url = record['pdf_url']
               
               print(f"\n🔄 [{i}/{len(retry_records)}] Retrying: {facility_name}")
               print(f"   Record ID: {record_id}, Attempt: {record['retry_count'] + 1}")
               
               # Attempt retry
               success, error_info = self._retry_single_download(record, driver)
               
               if success:
                   # Mark as succeeded
                   self.failed_download_service.update_retry_attempt(record_id, success=True)
                   successful += 1
                   print(f"✅ Retry successful for {facility_name}")
               else:
                   # Mark as failed/update retry count
                   self.failed_download_service.update_retry_attempt(
                       record_id, 
                       success=False,
                       failure_reason=error_info.get('reason'),
                       failure_details=error_info.get('details')
                   )
                   failed += 1
                   print(f"❌ Retry failed for {facility_name}: {error_info.get('reason')}")
               
               # Short delay between retries to be gentle
               if i < len(retry_records):
                   time.sleep(3)
           
       finally:
           if driver:
               CommonCleanup.close_browser_driver(driver)
       
       return {
           'processed': len(retry_records),
           'successful': successful,
           'failed': failed
       }
   
   def _retry_single_download(self, record, driver):
       """Retry a single failed download record"""
       try:
           facility_name = record['facility_name']
           pdf_url = record['pdf_url']
           inspection_id = record['inspection_id']
           inspection_date = record['inspection_date']
           
           # Validate URL
           if not pdf_url or not ValidationUtilities.is_valid_url(pdf_url):
               return False, {
                   'reason': 'invalid_url',
                   'details': 'Invalid or missing PDF URL'
               }
           
           # Generate filename
           filename = FileUtilities.generate_inspection_filename(facility_name, inspection_id, inspection_date)
           filepath = self.download_path / filename
           
           # Attempt download
           success, error_info = self._download_pdf_with_timeout(pdf_url, filepath, driver)
           
           if success:
               # Attempt extraction
               try:
                   extraction_result = self.extractor.extract_and_save(
                       pdf_path=str(filepath),
                       facility_name=facility_name,
                       inspection_id=inspection_id
                   )
                   
                   if extraction_result:
                       file_size = FileUtilities.get_file_size_mb(str(filepath))
                       print(f"📄 Extracted data from {filename} ({file_size:.2f}MB)")
                       return True, {'reason': 'success'}
                   else:
                       return False, {
                           'reason': 'extraction_failed',
                           'details': 'PDF downloaded but extraction failed'
                       }
                       
               except Exception as e:
                   return False, {
                       'reason': 'extraction_error',
                       'details': f'Extraction error: {str(e)}'
                   }
           else:
               return False, error_info
               
       except Exception as e:
           self.error_handler.log_error("Single retry", e, {'record_id': record.get('id')})
           return False, {
               'reason': 'unexpected_error',
               'details': f'Unexpected retry error: {str(e)}'
           }
   
   def _download_pdf_with_timeout(self, pdf_url, filepath, driver):
       """Download PDF with timeout and error handling for retries"""
       from selenium.webdriver.common.by import By
       from selenium.webdriver.support.ui import WebDriverWait
       from selenium.webdriver.support import expected_conditions as EC
       from selenium.common.exceptions import TimeoutException
       
       try:
           print(f"⬇️ Downloading: {pdf_url}")
           
           # Set timeouts
           driver.set_page_load_timeout(30)
           
           # Navigate to page
           driver.get(pdf_url)
           
           # Wait for page load
           wait = WebDriverWait(driver, 10)
           wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
           time.sleep(2)  # Brief pause
           
           # Find PDF link
           pdf_link_element = wait.until(
               EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "View Original Inspection PDF"))
           )
           pdf_href = pdf_link_element.get_attribute("href")
           
           if not pdf_href:
               return False, {
                   'reason': 'no_pdf_link',
                   'details': 'Could not find PDF download link'
               }
           
           # Construct full URL
           actual_pdf_url = ("https://inspections.myhealthdepartment.com" + pdf_href) if pdf_href.startswith("/") else pdf_href
           
           # Update session cookies
           try:
               cookies = {c["name"]: c["value"] for c in driver.get_cookies()}
               if cookies:
                   self.session.cookies.update(cookies)
           except Exception:
               pass  # Continue without cookies if they fail
           
           # Download PDF
           response = self.session.get(actual_pdf_url, timeout=30)
           
           # Check for rate limiting
           if response.status_code == 403:
               return False, {
                   'reason': 'blocked_403',
                   'details': 'HTTP 403 Forbidden - rate limited'
               }
           
           response.raise_for_status()
           
           # Validate content
           content_type = (response.headers.get('content-type') or '').lower()
           content_length = len(response.content)
           
           if 'pdf' not in content_type and content_length < 5000:
               return False, {
                   'reason': 'invalid_content',
                   'details': f'Not a PDF: {content_type}, size: {content_length} bytes'
               }
           
           # Save file
           with open(filepath, 'wb') as f:
               f.write(response.content)
           
           # Verify file
           if FileUtilities.is_pdf_file(str(filepath)) and filepath.exists() and filepath.stat().st_size > 1000:
               file_size = FileUtilities.get_file_size_mb(str(filepath))
               print(f"✅ Downloaded: {filepath.name} ({file_size:.2f}MB)")
               return True, {'reason': 'success'}
           else:
               return False, {
                   'reason': 'file_verification_failed',
                   'details': 'Downloaded file is invalid'
               }
               
       except TimeoutException:
           return False, {
               'reason': 'timeout',
               'details': 'Page load or element find timeout'
           }
       except Exception as e:
           if hasattr(e, 'response') and hasattr(e.response, 'status_code'):
               return False, {
                   'reason': f'http_error_{e.response.status_code}',
                   'details': f'HTTP error {e.response.status_code}: {str(e)}'
               }
           else:
               return False, {
                   'reason': 'download_error',
                   'details': f'Download failed: {str(e)}'
               }
   
   def get_retry_status(self):
       """Get current retry service status"""
       try:
           stats = self.failed_download_service.get_failed_download_stats()
           return {
               'status': 'operational',
               'timestamp': datetime.now().isoformat(),
               'statistics': stats
           }
       except Exception as e:
           return {
               'status': 'error',
               'timestamp': datetime.now().isoformat(),
               'error': str(e)
           }

def main():
   """Main entry point for running retry service"""
   retry_service = RetryService()
   
   try:
       # Run single retry cycle
       results = retry_service.run_retry_cycle()
       
       print(f"\n📊 Retry Summary:")
       print(f"   Processed: {results.get('processed', 0)}")
       print(f"   Successful: {results.get('successful', 0)}")
       print(f"   Failed: {results.get('failed', 0)}")
       
       if results.get('error'):
           print(f"   Error: {results['error']}")
           sys.exit(1)
       
   except KeyboardInterrupt:
       print("\n⏹️ Retry service interrupted by user")
   except Exception as e:
       print(f"\n❌ Retry service failed: {e}")
       sys.exit(1)

if __name__ == "__main__":
   main()
