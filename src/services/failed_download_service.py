#!/usr/bin/env python3
"""
Failed Download Service
Manages failed PDF download records for automatic retry functionality

Key responsibilities:
- Store failed download records in database
- Retrieve records ready for retry
- Update retry attempts and status
- Clean up completed/failed records

External dependencies:
- core.database.database
- core.error_handler.ErrorHandler
- sqlite3, datetime
"""

import sqlite3
from datetime import datetime, timedelta
import sys
import os

# Add path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.database import database
from core.error_handler import ErrorHandler

class FailedDownloadService:
   """Service for managing failed download records and retry logic"""
   
   def __init__(self):
       self.db = database
       self.error_handler = ErrorHandler(__name__)
   
   def store_failed_download(self, facility_name, pdf_url, inspection_id=None, 
                           inspection_date=None, failure_reason=None, 
                           failure_details=None, batch_id=None, max_retries=2):
       """Store a failed download record for retry"""
       try:
           # Calculate next retry time (5 minutes from now)
           next_retry_at = datetime.now() + timedelta(minutes=5)
           
           with self.db.get_connection() as conn:
               cursor = conn.cursor()
               cursor.execute("""
                   INSERT INTO failed_downloads (
                       facility_name, inspection_id, pdf_url, inspection_date,
                       failure_reason, failure_details, retry_count, max_retries,
                       next_retry_at, original_batch_id, status
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               """, (
                   facility_name,
                   inspection_id,
                   pdf_url,
                   inspection_date,
                   failure_reason or 'unknown',
                   failure_details,
                   0,  # Initial retry count
                   max_retries,
                   next_retry_at.isoformat(),
                   batch_id,
                   'pending'
               ))
               record_id = cursor.lastrowid
               
           self.error_handler.log_warning(
               "Failed download stored",
               f"Stored failed download for {facility_name}",
               {
                   'record_id': record_id,
                   'facility': facility_name,
                   'reason': failure_reason,
                   'batch_id': batch_id
               }
           )
           return record_id
           
       except Exception as e:
           self.error_handler.log_error(
               "Store failed download", e, 
               {'facility': facility_name, 'url': pdf_url}
           )
           return None
   
   def get_records_ready_for_retry(self, limit=10):
       """Get failed download records ready for retry"""
       try:
           current_time = datetime.now().isoformat()
           
           with self.db.get_connection() as conn:
               cursor = conn.cursor()
               cursor.execute("""
                   SELECT id, facility_name, inspection_id, pdf_url, inspection_date,
                          failure_reason, failure_details, retry_count, max_retries,
                          next_retry_at, original_batch_id, created_at, last_retry_at
                   FROM failed_downloads 
                   WHERE status = 'pending' 
                     AND retry_count < max_retries
                     AND (next_retry_at IS NULL OR next_retry_at <= ?)
                   ORDER BY created_at ASC
                   LIMIT ?
               """, (current_time, limit))
               
               rows = cursor.fetchall()
               
               # Convert to list of dicts
               records = []
               for row in rows:
                   records.append({
                       'id': row[0],
                       'facility_name': row[1],
                       'inspection_id': row[2],
                       'pdf_url': row[3],
                       'inspection_date': row[4],
                       'failure_reason': row[5],
                       'failure_details': row[6],
                       'retry_count': row[7],
                       'max_retries': row[8],
                       'next_retry_at': row[9],
                       'original_batch_id': row[10],
                       'created_at': row[11],
                       'last_retry_at': row[12]
                   })
               
               if records:
                   print(f"📋 Found {len(records)} records ready for retry")
               
               return records
               
       except Exception as e:
           self.error_handler.log_error("Get retry records", e)
           return []
   
   def update_retry_attempt(self, record_id, success=False, failure_reason=None, failure_details=None):
       """Update retry attempt for a failed download record"""
       try:
           current_time = datetime.now().isoformat()
           
           with self.db.get_connection() as conn:
               cursor = conn.cursor()
               
               if success:
                   # Mark as succeeded and remove from retry queue
                   cursor.execute("""
                       UPDATE failed_downloads 
                       SET status = 'succeeded', last_retry_at = ?
                       WHERE id = ?
                   """, (current_time, record_id))
                   
                   self.error_handler.log_warning(
                       "Retry succeeded",
                       f"Successfully retried record {record_id}",
                       {'record_id': record_id}
                   )
               else:
                   # Increment retry count and update failure info
                   cursor.execute("""
                       SELECT retry_count, max_retries FROM failed_downloads WHERE id = ?
                   """, (record_id,))
                   row = cursor.fetchone()
                   
                   if row:
                       retry_count, max_retries = row
                       new_retry_count = retry_count + 1
                       
                       if new_retry_count >= max_retries:
                           # Max retries reached, mark as failed
                           cursor.execute("""
                               UPDATE failed_downloads 
                               SET retry_count = ?, status = 'failed', last_retry_at = ?,
                                   failure_reason = ?, failure_details = ?
                               WHERE id = ?
                           """, (new_retry_count, current_time, failure_reason, failure_details, record_id))
                           
                           self.error_handler.log_warning(
                               "Max retries reached",
                               f"Record {record_id} failed after {new_retry_count} attempts",
                               {'record_id': record_id, 'reason': failure_reason}
                           )
                       else:
                           # Schedule next retry (exponential backoff: 5min, 15min, 45min)
                           delay_minutes = 5 * (3 ** new_retry_count)
                           next_retry_at = datetime.now() + timedelta(minutes=delay_minutes)
                           
                           cursor.execute("""
                               UPDATE failed_downloads 
                               SET retry_count = ?, last_retry_at = ?, next_retry_at = ?,
                                   failure_reason = ?, failure_details = ?
                               WHERE id = ?
                           """, (new_retry_count, current_time, next_retry_at.isoformat(), 
                                 failure_reason, failure_details, record_id))
                           
                           print(f"⏰ Scheduled retry #{new_retry_count} for record {record_id} in {delay_minutes} minutes")
               
               return True
               
       except Exception as e:
           self.error_handler.log_error(
               "Update retry attempt", e, 
               {'record_id': record_id, 'success': success}
           )
           return False
   
   def get_failed_download_stats(self):
       """Get statistics about failed downloads"""
       try:
           with self.db.get_connection() as conn:
               cursor = conn.cursor()
               
               # Get counts by status
               cursor.execute("""
                   SELECT status, COUNT(*) as count 
                   FROM failed_downloads 
                   GROUP BY status
               """)
               status_counts = dict(cursor.fetchall())
               
               # Get records pending retry
               cursor.execute("""
                   SELECT COUNT(*) FROM failed_downloads 
                   WHERE status = 'pending' AND retry_count < max_retries
               """)
               pending_retries = cursor.fetchone()[0]
               
               # Get records ready for retry now
               current_time = datetime.now().isoformat()
               cursor.execute("""
                   SELECT COUNT(*) FROM failed_downloads 
                   WHERE status = 'pending' 
                     AND retry_count < max_retries
                     AND (next_retry_at IS NULL OR next_retry_at <= ?)
               """, (current_time,))
               ready_for_retry = cursor.fetchone()[0]
               
               return {
                   'status_counts': status_counts,
                   'pending_retries': pending_retries,
                   'ready_for_retry': ready_for_retry,
                   'total_failed_records': sum(status_counts.values())
               }
               
       except Exception as e:
           self.error_handler.log_error("Get failed download stats", e)
           return {
               'status_counts': {},
               'pending_retries': 0,
               'ready_for_retry': 0,
               'total_failed_records': 0
           }
   
   def cleanup_old_records(self, days_old=7):
       """Clean up old succeeded/failed records older than specified days"""
       try:
           cutoff_date = datetime.now() - timedelta(days=days_old)
           cutoff_iso = cutoff_date.isoformat()
           
           with self.db.get_connection() as conn:
               cursor = conn.cursor()
               
               # Delete old succeeded and permanently failed records
               cursor.execute("""
                   DELETE FROM failed_downloads 
                   WHERE (status = 'succeeded' OR status = 'failed')
                     AND created_at < ?
               """, (cutoff_iso,))
               
               deleted_count = cursor.rowcount
               
               if deleted_count > 0:
                   print(f"🧹 Cleaned up {deleted_count} old failed download records")
               
               return deleted_count
               
       except Exception as e:
           self.error_handler.log_error("Cleanup old records", e)
           return 0
   
   def retry_specific_record(self, record_id):
       """Mark a specific record as ready for immediate retry"""
       try:
           current_time = datetime.now().isoformat()
           
           with self.db.get_connection() as conn:
               cursor = conn.cursor()
               cursor.execute("""
                   UPDATE failed_downloads 
                   SET next_retry_at = ?, status = 'pending'
                   WHERE id = ? AND retry_count < max_retries
               """, (current_time, record_id))
               
               if cursor.rowcount > 0:
                   print(f"⚡ Record {record_id} marked for immediate retry")
                   return True
               else:
                   print(f"❌ Record {record_id} not found or max retries exceeded")
                   return False
                   
       except Exception as e:
           self.error_handler.log_error("Retry specific record", e, {'record_id': record_id})
           return False
   
   def convert_facility_to_failed_record(self, facility_data, failure_reason, batch_id=None):
       """Convert facility data to failed download record format"""
       return {
           'facility_name': facility_data.get('name', 'Unknown'),
           'pdf_url': facility_data.get('pdf_url') or facility_data.get('url'),
           'inspection_id': facility_data.get('inspection_id'),
           'inspection_date': facility_data.get('inspection_date'),
           'failure_reason': failure_reason,
           'batch_id': batch_id
       }
