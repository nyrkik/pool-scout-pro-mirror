"""
Shared Services Initialization for Pool Scout Pro
ENHANCED VERSION: Includes download progress service
"""

import logging
from services.database_service import DatabaseService
from services.search_service import SearchService
from services.duplicate_prevention_service import DuplicatePreventionService
from services.violation_severity_service import ViolationSeverityService
from services.saved_status_service import SavedStatusService
from services.pdf_downloader import PDFDownloader
from services.download_progress_service import get_download_progress_service

try:
    from services.search_progress_service import SearchProgressService
except ImportError:
    SearchProgressService = None

# Global services registry
services = {}
logger = logging.getLogger('pool_scout_pro.services')

def get_database_service():
    """Get or create database service instance"""
    if 'database_service' not in services:
        services['database_service'] = DatabaseService()
    return services['database_service']

# Alias for backward compatibility
def get_db_service():
    """Alias for get_database_service"""
    return get_database_service()

def get_duplicate_service():
    """Get or create duplicate prevention service instance"""
    if 'duplicate_service' not in services:
        services['duplicate_service'] = DuplicatePreventionService()
    return services['duplicate_service']

# Alias for API routes
def get_duplicate_prevention_service():
    """Alias for get_duplicate_service"""
    return get_duplicate_service()

def get_progress_service():
    """Get or create progress service instance"""
    if 'progress_service' not in services:
        if SearchProgressService:
            services['progress_service'] = SearchProgressService()
        else:
            # Create a dummy progress service instead of None
            class DummyProgressService:
                def update_search_progress(self, status, count):
                    pass
                def start_search(self, date):
                    pass
                def complete_search(self, count):
                    pass
                def estimate_search_duration(self):
                    return 25
            services['progress_service'] = DummyProgressService()
    return services['progress_service']

def get_search_service():
    """Get or create search service instance"""
    if 'search_service' not in services:
        progress_service = get_progress_service()
        services['search_service'] = SearchService(progress_service=progress_service)
    return services['search_service']

def get_pdf_downloader(shared_driver=None):
    """Get or create PDF downloader service instance"""
    # Always create new instance if shared_driver is provided
    if shared_driver is not None:
        return PDFDownloader(shared_driver=shared_driver)
    
    # Use cached instance if no shared_driver specified
    if 'pdf_downloader' not in services:
        services['pdf_downloader'] = PDFDownloader()
    return services['pdf_downloader']

def get_saved_status_service():
    """Get or create saved status service instance"""
    if 'saved_status_service' not in services:
        services['saved_status_service'] = SavedStatusService()
    return services['saved_status_service']

def get_severity_service():
    """Get or create violation severity service instance"""
    if 'severity_service' not in services:
        try:
            services['severity_service'] = ViolationSeverityService()
        except Exception as e:
            print(f"⚠️ Failed to initialize ViolationSeverityService: {e}")
            services['severity_service'] = None
    return services['severity_service']

def get_download_progress_service_factory():
    """Get download progress service instance"""
    # This service is a singleton, so we use its own factory
    return get_download_progress_service()

# Initialize shared instances
db_service = get_database_service()
duplicate_service = get_duplicate_service()
progress_service = get_progress_service()
search_service = get_search_service()
pdf_downloader = get_pdf_downloader()
severity_service = get_severity_service()
saved_status_service = get_saved_status_service()
download_progress_service = get_download_progress_service_factory()

# Export for direct import
__all__ = [
    'db_service', 'search_service', 'progress_service', 
    'duplicate_service', 'severity_service', 'pdf_downloader', 'saved_status_service',
    'download_progress_service',
    'get_database_service', 'get_db_service', 'get_search_service', 'get_progress_service',
    'get_duplicate_service', 'get_duplicate_prevention_service', 'get_severity_service', 
    'get_pdf_downloader', 'get_saved_status_service', 'get_download_progress_service_factory'
]
