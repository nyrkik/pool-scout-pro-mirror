#!/usr/bin/env python3
"""
Download Progress Service - Pool Scout Pro

Tracks real-time progress during PDF downloads for frontend display.
Provides thread-safe progress updates and status reporting.

Key responsibilities:
- Track current download progress (facility, counts, status)
- Thread-safe updates during multi-threaded downloads
- Provide progress data for API endpoints
- Clean up progress data when downloads complete

External dependencies:
- threading.Lock for thread safety
- datetime for timestamps
- json for progress data serialization
"""

import threading
import time
from datetime import datetime
from typing import Dict, Any, Optional, List

class DownloadProgressService:
   """Thread-safe service for tracking download progress"""
   
   def __init__(self):
       self._lock = threading.Lock()
       self._progress_data = {
           'is_active': False,
           'job_id': None,
           'current_facility': '',
           'current_facility_inspection_id': '',
           'completed_count': 0,
           'failed_count': 0,
           'total_count': 0,
           'status': 'idle',
           'start_time': None,
           'last_update': None,
           'facilities_by_id': {},
           'message': ''
       }
   
   def start_download(self, job_id: str, facilities: List[Dict[str, Any]]) -> None:
       """Initialize progress tracking for new download batch"""
       with self._lock:
           facilities_by_id = {}
           
           for facility in facilities:
               inspection_id = facility.get('inspection_id')
               if inspection_id:
                   facilities_by_id[inspection_id] = {
                       'name': facility.get('name', 'Unknown'),
                       'status': 'pending',
                       'message': '',
                       'inspection_id': inspection_id
                   }
           
           self._progress_data = {
               'is_active': True,
               'job_id': job_id,
               'current_facility': '',
               'current_facility_inspection_id': '',
               'completed_count': 0,
               'failed_count': 0,
               'total_count': len(facilities),
               'status': 'starting',
               'start_time': datetime.now().isoformat(),
               'last_update': datetime.now().isoformat(),
               'facilities_by_id': facilities_by_id,
               'message': f'Starting download of {len(facilities)} facilities...'
           }
           print(f"📄 Progress tracking started for job {job_id}")
   
   def update_facility_progress(self, inspection_id: str, facility_name: str, status: str, message: str = '') -> None:
       """Update progress for specific facility using inspection ID"""
       with self._lock:
           if not self._progress_data['is_active']:
               return
           
           # Update current facility
           self._progress_data['current_facility'] = facility_name
           self._progress_data['current_facility_inspection_id'] = inspection_id
           self._progress_data['last_update'] = datetime.now().isoformat()
           
           # Update facility status in dictionary
           if inspection_id in self._progress_data['facilities_by_id']:
               self._progress_data['facilities_by_id'][inspection_id].update({
                   'status': status,
                   'message': message
               })
           
           # Update overall status
           if status == 'downloading':
               self._progress_data['status'] = 'downloading'
               self._progress_data['message'] = f'Downloading: {facility_name}'
           elif status == 'extracting':
               self._progress_data['status'] = 'processing'
               self._progress_data['message'] = f'Processing: {facility_name}'
           elif status == 'completed':
               self._progress_data['completed_count'] += 1
               self._progress_data['message'] = f'Completed: {facility_name}'
           elif status == 'failed':
               self._progress_data['failed_count'] += 1
               self._progress_data['message'] = f'Failed: {facility_name} - {message}'
           
           print(f"📊 Progress: {facility_name} -> {status}")
   
   def complete_download(self, job_id: str, successful: int, failed: int) -> None:
       """Mark download batch as complete"""
       with self._lock:
           if self._progress_data.get('job_id') != job_id:
               return
           
           self._progress_data.update({
               'status': 'completed',
               'current_facility': '',
               'current_facility_inspection_id': '',
               'completed_count': successful,
               'failed_count': failed,
               'last_update': datetime.now().isoformat(),
               'message': f'Download complete: {successful} successful, {failed} failed'
           })
           
           print(f"✅ Progress tracking completed for job {job_id}")
           
           # Auto-cleanup after 30 seconds
           threading.Timer(30.0, self._cleanup_progress).start()
   
   def get_progress(self) -> Dict[str, Any]:
       """Get current progress data"""
       with self._lock:
           # Convert facilities dictionary to array for API response
           facilities_array = list(self._progress_data['facilities_by_id'].values())
           
           progress_copy = dict(self._progress_data)
           progress_copy['facilities'] = facilities_array
           del progress_copy['facilities_by_id']  # Remove internal dictionary
           
           return progress_copy
   
   def is_download_active(self) -> bool:
       """Check if download is currently active"""
       with self._lock:
           return self._progress_data['is_active']
   
   def _cleanup_progress(self) -> None:
       """Clean up progress data after completion"""
       with self._lock:
           if self._progress_data['status'] == 'completed':
               self._progress_data['is_active'] = False
               self._progress_data['job_id'] = None
               print("🧹 Progress data cleaned up")
   
   def force_cleanup(self) -> None:
       """Force cleanup of progress data (for error recovery)"""
       with self._lock:
           self._progress_data.update({
               'is_active': False,
               'status': 'idle',
               'job_id': None,
               'current_facility': '',
               'current_facility_inspection_id': '',
               'message': 'Ready for downloads'
           })
           print("🔄 Progress data force cleaned")

# Global progress service instance
_progress_service = None

def get_download_progress_service():
   """Get global download progress service instance"""
   global _progress_service
   if _progress_service is None:
       _progress_service = DownloadProgressService()
   return _progress_service
