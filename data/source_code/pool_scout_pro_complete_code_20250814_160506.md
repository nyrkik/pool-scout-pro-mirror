# Pool Scout Pro - Complete Source Code Documentation
Generated: $(date '+%Y-%m-%d %H:%M:%S')
Project: Sacramento County Pool Inspection Automation System

## Table of Contents
- Python Source Code (src/)
- Web Templates and Assets (templates/)

---

## Python Source Code (src/)

### src/core/browser.py
```python
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import logging

logger = logging.getLogger(__name__)

class BrowserManager:
    """Browser manager with stealth configuration to avoid bot detection"""

    def __init__(self):
        # Use Docker Selenium Grid on localhost:4444
        self.selenium_url = 'http://localhost:4444/wd/hub'
        logger.info("Browser manager initialized")

    def _check_selenium_health(self):
        """Check if Selenium Grid is responding on localhost:4444"""
        try:
            import requests
            response = requests.get('http://localhost:4444/status', timeout=5)
            return response.status_code == 200
        except:
            return False

    def _start_selenium_container(self):
        """Start the Selenium Docker container using docker-compose"""
        try:
            import subprocess
            result = subprocess.run(['docker-compose', 'up', '-d', 'selenium'],
                                    cwd='.', capture_output=True, text=True, timeout=30)
            return result.returncode == 0
        except:
            return False

    def _wait_for_selenium_health(self, timeout=30):
        """Wait for Selenium to become healthy, checking every 2 seconds"""
        import time
        start_time = time.time()

        while time.time() - start_time < timeout:
            if self._check_selenium_health():
                return True
            time.sleep(2)

        return False

    def ensure_selenium_running(self):
        """Ensure Selenium is running, start if needed with user feedback"""
        status = self.get_selenium_status()

        if status['status'] == 'healthy':
            logger.info("Selenium already healthy")
            return True

        # Inform user about the wait
        if status['status'] == 'down':
            print("🔄 Selenium container is down. Starting container...")
            print("⏳ This may take 15-20 seconds. Please wait...")
        elif status['status'] == 'unhealthy':
            print("🔄 Selenium container starting. Waiting for readiness...")
            print("⏳ This may take 10-15 seconds. Please wait...")

        logger.info(f"Selenium status: {status['status']}, attempting to start...")

        if self._start_selenium_container():
            print("📦 Container started successfully. Waiting for Selenium Grid to be ready...")

            # Show progress during health check wait
            import time
            start_time = time.time()
            for attempt in range(1, 16):  # 30 seconds max, check every 2 seconds
                if self._check_selenium_health():
                    elapsed = time.time() - start_time
                    print(f"✅ Selenium Grid is ready! ({elapsed:.1f}s)")
                    logger.info("✅ Selenium is now healthy")
                    return True

                print(f"⏳ Waiting for Selenium Grid... ({attempt * 2}s)")
                time.sleep(2)

            print("❌ Selenium started but failed health check after 30 seconds")
            logger.error("❌ Selenium started but failed health check")
            return False
        else:
            print("❌ Failed to start Selenium container")
            logger.error("❌ Failed to start Selenium container")
            return False

    def create_driver(self):
        """Create a Firefox WebDriver instance with automatic Selenium management"""
        try:
            # Automatically ensure Selenium is running before creating driver
            if not self.ensure_selenium_running():
                raise Exception("Unable to start Selenium Grid")

            options = Options()

            # Stealth settings to avoid bot detection
            options.set_preference("general.useragent.override",
                                   "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/140.0")

            # Disable automation indicators
            options.set_preference("dom.webdriver.enabled", False)
            options.set_preference("useAutomationExtension", False)
            options.set_preference("marionette.enabled", False)

            # Normal browser behavior
            options.set_preference("browser.startup.homepage", "about:blank")
            options.set_preference("browser.startup.page", 0)
            options.set_preference("browser.cache.disk.enable", False)
            options.set_preference("browser.cache.memory.enable", False)
            options.set_preference("browser.cache.offline.enable", False)
            options.set_preference("network.http.use-cache", False)

            # Create the driver
            driver = webdriver.Remote(
                command_executor=self.selenium_url,
                options=options
            )

            logger.info("Browser driver created successfully with stealth configuration")
            return driver

        except Exception as e:
            logger.error(f"Failed to create browser driver: {e}")
            raise

    def _check_docker_container_status(self):
        """Check Docker container status using docker command"""
        try:
            import subprocess
            result = subprocess.run(['docker', 'ps', '--filter', 'name=selenium', '--format', '{{.Status}}'],
                                    capture_output=True, text=True, timeout=10)
            return 'Up' in result.stdout if result.returncode == 0 else False
        except:
            return False

    def get_selenium_status(self):
        """Get comprehensive Selenium service status"""
        health_ok = self._check_selenium_health()
        container_up = self._check_docker_container_status()

        if health_ok:
            return {'status': 'healthy', 'container': True, 'responding': True}
        elif container_up:
            return {'status': 'unhealthy', 'container': True, 'responding': False}
        else:
            return {'status': 'down', 'container': False, 'responding': False}

    def cleanup(self):
        """Cleanup method for compatibility"""
        pass```

### src/core/database.py
```python
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
        """Create the normalized database schema from milestone"""
        with self.get_connection() as conn:
            # Facilities table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS facilities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    address TEXT,
                    establishment_id TEXT,
                    permit_holder TEXT,
                    phone TEXT,
                    city TEXT,
                    zip_code TEXT,
                    program_identifier TEXT,
                    policy_announcements TEXT,
                    equipment_approvals TEXT,
                    facility_comments TEXT,
                    management_company_id INTEGER,
                    current_operational_status TEXT DEFAULT 'open',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (management_company_id) REFERENCES management_companies(id)
                )
            """)
            
            # Inspection reports table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS inspection_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    facility_id INTEGER NOT NULL,
                    permit_id TEXT,
                    inspection_date TEXT,
                    inspector_name TEXT,
                    inspector_phone TEXT,
                    accepted_by TEXT,
                    total_violations INTEGER DEFAULT 0,
                    major_violations INTEGER DEFAULT 0,
                    severity_score REAL DEFAULT 0.0,
                    closure_status TEXT DEFAULT 'operational',
                    closure_reason TEXT,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
                    violation_category TEXT,
                    severity_level TEXT,
                    observations TEXT,
                    full_observations TEXT,
                    code_description TEXT,
                    full_code_description TEXT,
                    correction_timeframe TEXT,
                    repeat_violation BOOLEAN DEFAULT FALSE,
                    repeat_count INTEGER DEFAULT 0,
                    severity_score REAL DEFAULT 0.0,
                    FOREIGN KEY (report_id) REFERENCES inspection_reports(id),
                    FOREIGN KEY (facility_id) REFERENCES facilities(id)
                )
            """)
            
            # Management companies table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS management_companies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_name TEXT NOT NULL,
                    contact_info TEXT,
                    service_areas TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()

database = Database()
```

### src/core/error_handler.py
```python
#!/usr/bin/env python3
"""
Standardized Error Handling for Pool Scout Pro
Provides consistent logging, error responses, and resource cleanup
"""

import logging
import traceback
from functools import wraps
from typing import Dict, Any, Optional, Callable

class ErrorHandler:
    """Centralized error handling with consistent patterns"""
    
    def __init__(self, logger_name: str = __name__):
        self.logger = logging.getLogger(logger_name)
    
    def log_error(self, operation: str, error: Exception, context: Dict[str, Any] = None):
        """Standardized error logging with context"""
        context_str = f" | Context: {context}" if context else ""
        error_msg = f"❌ {operation} failed: {str(error)}{context_str}"
        
        self.logger.error(error_msg)
        print(error_msg)  # Also print for immediate feedback
        
        # Log full traceback for debugging
        if self.logger.isEnabledFor(logging.DEBUG):
            self.logger.debug(f"Full traceback for {operation}:", exc_info=True)
    
    def log_warning(self, operation: str, message: str, context: Dict[str, Any] = None):
        """Standardized warning logging"""
        context_str = f" | Context: {context}" if context else ""
        warning_msg = f"⚠️ {operation}: {message}{context_str}"
        
        self.logger.warning(warning_msg)
        print(warning_msg)
    
    def create_error_response(self, operation: str, error: Exception, 
                            status_code: int = 500) -> Dict[str, Any]:
        """Create standardized error response for APIs"""
        return {
            'success': False,
            'error': str(error),
            'operation': operation,
            'status_code': status_code
        }
    
    def safe_execute(self, operation: str, func: Callable, 
                    default_return: Any = None, context: Dict[str, Any] = None,
                    cleanup_func: Optional[Callable] = None) -> Any:
        """Execute function with standardized error handling"""
        try:
            return func()
        except Exception as e:
            self.log_error(operation, e, context)
            if cleanup_func:
                try:
                    cleanup_func()
                except Exception as cleanup_error:
                    self.log_error(f"{operation} cleanup", cleanup_error)
            return default_return

def with_error_handling(operation: str, default_return: Any = None, 
                       cleanup_func: Optional[Callable] = None):
    """Decorator for standardized error handling"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            error_handler = ErrorHandler(func.__module__)
            
            def execute():
                return func(*args, **kwargs)
            
            context = {
                'function': func.__name__,
                'args_count': len(args),
                'kwargs_keys': list(kwargs.keys())
            }
            
            return error_handler.safe_execute(
                operation, execute, default_return, context, cleanup_func
            )
        return wrapper
    return decorator

def with_api_error_handling(operation: str):
    """Decorator for API endpoints with JSON error responses"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            error_handler = ErrorHandler(func.__module__)
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_handler.log_error(operation, e, {
                    'endpoint': func.__name__,
                    'args_count': len(args),
                    'kwargs_keys': list(kwargs.keys())
                })
                
                from flask import jsonify
                return jsonify(error_handler.create_error_response(operation, e)), 500
        return wrapper
    return decorator

# Common cleanup functions
class CommonCleanup:
    """Common cleanup operations"""
    
    @staticmethod
    def close_database_connection(conn):
        """Safely close database connection"""
        try:
            if conn:
                conn.close()
        except Exception as e:
            print(f"⚠️ Failed to close database connection: {e}")
    
    @staticmethod
    def close_browser_driver(driver):
        """Safely close browser driver"""
        try:
            if driver:
                driver.quit()
        except Exception as e:
            print(f"⚠️ Failed to close browser driver: {e}")
    
    @staticmethod
    def close_http_session(session):
        """Safely close HTTP session"""
        try:
            if session:
                session.close()
        except Exception as e:
            print(f"⚠️ Failed to close HTTP session: {e}")
```

### src/core/settings.py
```python
import yaml
from pathlib import Path
import os

class Settings:
    def __init__(self):
        # Find project root by looking for config directory
        current_dir = Path(__file__).parent
        project_root = current_dir.parent.parent  # Go up from src/core to project root
        
        # Try different possible locations for config
        config_paths = [
            project_root / "config" / "settings.yaml",
            Path("config/settings.yaml"),  # Relative from current working directory
            Path(__file__).parent.parent.parent / "config" / "settings.yaml"
        ]
        
        config_path = None
        for path in config_paths:
            if path.exists():
                config_path = path
                break
        
        if not config_path:
            raise FileNotFoundError(f"Could not find config/settings.yaml in any of: {config_paths}")
            
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

    @property
    def database_path(self):
        return self.config['database']['path']
    
    @property
    def selenium_host(self):
        return self.config['browser']['selenium_host']
    
    @property
    def flask_port(self):
        return self.config['flask']['port']
    
    @property
    def pdf_download_path(self):
        return self.config['downloads']['directory']

settings = Settings()
```

### src/core/utilities.py
```python
#!/usr/bin/env python3
"""
Common Utilities for Pool Scout Pro
Shared functions for date conversion, name normalization, and other common operations
"""

import re
from datetime import datetime
from typing import Optional, Dict, Any

class DateUtilities:
    """Date conversion and validation utilities"""

    @staticmethod
    def convert_frontend_to_emd_date(frontend_date: str) -> str:
        """Convert YYYY-MM-DD to MM/DD/YYYY for EMD website"""
        try:
            date_parts = frontend_date.split('-')
            if len(date_parts) == 3:
                return f"{date_parts[1]}/{date_parts[2]}/{date_parts[0]}"
            else:
                raise ValueError(f"Invalid date format: {frontend_date}")
        except Exception:
            raise ValueError(f"Cannot convert date: {frontend_date}")

    @staticmethod
    def convert_emd_to_frontend_date(emd_date: str) -> str:
        """Convert MM/DD/YYYY to YYYY-MM-DD for frontend"""
        try:
            date_parts = emd_date.split('/')
            if len(date_parts) == 3:
                month, day, year = date_parts
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            else:
                raise ValueError(f"Invalid EMD date format: {emd_date}")
        except Exception:
            raise ValueError(f"Cannot convert EMD date: {emd_date}")

    @staticmethod
    def validate_date_format(date_string: str, format_type: str = 'frontend') -> bool:
        """Validate date format (frontend: YYYY-MM-DD, emd: MM/DD/YYYY)"""
        try:
            if format_type == 'frontend':
                datetime.strptime(date_string, '%Y-%m-%d')
            elif format_type == 'emd':
                datetime.strptime(date_string, '%m/%d/%Y')
            else:
                return False
            return True
        except ValueError:
            return False

    @staticmethod
    def get_current_date_frontend() -> str:
        """Get current date in frontend format (YYYY-MM-DD)"""
        return datetime.now().strftime('%Y-%m-%d')

    @staticmethod
    def get_current_timestamp() -> str:
        """Get current timestamp in ISO format"""
        return datetime.now().isoformat()

    @staticmethod
    def convert_to_pacific_date(frontend_date: str) -> str:
        """Convert frontend date to Pacific timezone for EMD API"""
        try:
            import pytz
            
            # Parse frontend date (user's intended date)
            dt = datetime.strptime(frontend_date, '%Y-%m-%d')
            
            # EMD operates in Pacific timezone
            pacific_tz = pytz.timezone('America/Los_Angeles')
            
            # Set as Pacific timezone date (what user means)
            pacific_dt = pacific_tz.localize(dt)
            
            # Return in MM/DD/YYYY format for EMD
            return pacific_dt.strftime('%m/%d/%Y')
            
        except Exception as e:
            # Fallback to original conversion if timezone fails
            return DateUtilities.convert_frontend_to_emd_date(frontend_date)

class NameUtilities:
    """Name normalization and cleaning utilities"""
    
    @staticmethod
    def normalize_facility_name(name: str) -> str:
        """Normalize facility name for consistent comparison"""
        if not name:
            return ""
        
        # Convert to lowercase for comparison
        normalized = name.lower().strip()
        
        # Remove common variations
        normalized = re.sub(r'\s+', ' ', normalized)  # Normalize whitespace
        normalized = re.sub(r'[^\w\s]', '', normalized)  # Remove special chars
        normalized = re.sub(r'\b(the|inc|llc|corp|ltd)\b', '', normalized)  # Remove common business terms
        
        return normalized.strip()
    
    @staticmethod
    def sanitize_filename(filename: str, max_length: int = 50) -> str:
        """Create safe filename from any string"""
        if not filename:
            return "unknown"
        
        # Remove problematic characters
        safe_chars = []
        for char in filename:
            if char.isalnum() or char in '-_. ':
                safe_chars.append(char)
            else:
                safe_chars.append('_')
        
        # Join and clean up
        safe_name = ''.join(safe_chars)
        safe_name = safe_name.strip()
        safe_name = ' '.join(safe_name.split())  # Normalize whitespace
        safe_name = safe_name.replace(' ', '_')
        
        # Limit length
        if len(safe_name) > max_length:
            safe_name = safe_name[:max_length]
        
        return safe_name or "unknown"
    
    @staticmethod
    def clean_address_string(address: str) -> str:
        """Clean address by removing CA and zip codes"""
        if not address:
            return address
        
        # Remove ", CA" and everything after
        cleaned = re.sub(r',?\s*CA\s*.*$', '', address, flags=re.IGNORECASE)
        cleaned = re.sub(r'\s*\d{5}(?:-\d{4})?\s*$', '', cleaned)  # Remove trailing zip
        return cleaned.strip()
    
    @staticmethod
    def extract_zip_code(address: str) -> Optional[str]:
        """Extract zip code from address string"""
        if not address:
            return None
        
        zip_match = re.search(r'\b(\d{5}(?:-\d{4})?)\b', address)
        return zip_match.group(1) if zip_match else None
    
    @staticmethod
    def are_names_similar(name1: str, name2: str, threshold: float = 0.8) -> bool:
        """Check if two facility names are similar (basic implementation)"""
        if not name1 or not name2:
            return False
        
        norm1 = NameUtilities.normalize_facility_name(name1)
        norm2 = NameUtilities.normalize_facility_name(name2)
        
        if norm1 == norm2:
            return True
        
        # Simple similarity check - could be enhanced with more sophisticated algorithms
        if len(norm1) > 0 and len(norm2) > 0:
            shorter = min(len(norm1), len(norm2))
            longer = max(len(norm1), len(norm2))
            
            # Check if one name contains the other (accounting for abbreviations)
            if norm1 in norm2 or norm2 in norm1:
                return shorter / longer >= threshold
        
        return False

class ValidationUtilities:
    """Common validation utilities"""
    
    @staticmethod
    def validate_permit_id(permit_id: str) -> bool:
        """Validate permit ID format"""
        if not permit_id:
            return False
        
        # Sacramento County permit IDs are typically alphanumeric with dashes
        pattern = r'^[A-Z0-9\-]{4,}$'
        return bool(re.match(pattern, permit_id.upper()))
    
    @staticmethod
    def validate_phone_number(phone: str) -> bool:
        """Validate phone number format"""
        if not phone:
            return False
        
        # Remove all non-digits
        digits = re.sub(r'\D', '', phone)
        
        # Should be 10 digits for US numbers
        return len(digits) == 10
    
    @staticmethod
    def validate_zip_code(zip_code: str) -> bool:
        """Validate zip code format"""
        if not zip_code:
            return False
        
        # 5 digits or 5+4 format
        pattern = r'^\d{5}(-\d{4})?$'
        return bool(re.match(pattern, zip_code))
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Basic URL validation"""
        if not url:
            return False
        
        # Simple URL pattern
        pattern = r'^https?://[^\s]+$'
        return bool(re.match(pattern, url))

class TextUtilities:
    """Text processing utilities"""
    
    @staticmethod
    def extract_numbers_from_text(text: str) -> list:
        """Extract all numbers from text"""
        if not text:
            return []
        
        return re.findall(r'\d+(?:\.\d+)?', text)
    
    @staticmethod
    def clean_whitespace(text: str) -> str:
        """Clean and normalize whitespace in text"""
        if not text:
            return text
        
        # Replace multiple whitespace with single space
        cleaned = re.sub(r'\s+', ' ', text)
        return cleaned.strip()
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
        """Truncate text to specified length"""
        if not text:
            return text
        
        if len(text) <= max_length:
            return text
        
        return text[:max_length - len(suffix)] + suffix
    
    @staticmethod
    def extract_inspection_id_from_url(url: str) -> Optional[str]:
        """Extract inspection ID from Sacramento County PDF URL"""
        if not url:
            return None

        # Pattern: inspectionID=CA62BD11-D673-4F93-A47D-0FA5E842C4DF
        pattern = r"inspectionID=([A-F0-9\-]{36})"
        match = re.search(pattern, url, re.IGNORECASE)
        if match:
            full_id = match.group(1)
            return full_id.split("-")[-1]
        return None

    @staticmethod
    def extract_code_and_description(violation_text: str) -> Dict[str, str]:
        """Extract violation code and description from formatted text"""
        if not violation_text:
            return {'code': '', 'description': ''}

        # Pattern for code (number.number) followed by description
        pattern = r'^(\d+\.\d+)\s*-?\s*(.*)$'
        match = re.match(pattern, violation_text.strip())

        if match:
            return {
                'code': match.group(1),
                'description': match.group(2).strip()
            }

        return {'code': '', 'description': violation_text.strip()}

class FileUtilities:
    """File handling utilities"""
    
    @staticmethod
    def generate_timestamped_filename(base_name: str, extension: str = 'pdf') -> str:
        """Generate filename with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_base = NameUtilities.sanitize_filename(base_name)
        return f"{timestamp}_{safe_base}.{extension}"
    
    @staticmethod
    def get_file_size_mb(file_path: str) -> float:
        """Get file size in megabytes"""
        try:
            import os
            size_bytes = os.path.getsize(file_path)
            return size_bytes / (1024 * 1024)
        except:
            return 0.0
    
    @staticmethod
    def is_pdf_file(file_path: str) -> bool:
        """Check if file is a PDF based on extension"""
        return file_path.lower().endswith('.pdf')

    @staticmethod
    def extract_inspection_id_from_url(url: str) -> Optional[str]:
        """Extract inspection ID from Sacramento County PDF URL"""
        if not url:
            return None
        
        # Pattern: inspectionID=CA62BD11-D673-4F93-A47D-0FA5E842C4DF
        pattern = r'inspectionID=([A-F0-9\-]{36})'
        match = re.search(pattern, url, re.IGNORECASE)
        if match:
            full_id = match.group(1)
            return full_id.split("-")[-1]
        return None

    @staticmethod
    def generate_inspection_filename(facility_name: str, inspection_id: str, inspection_date: str = None) -> str:
        """Generate filename in format: YYYYMMDD_FACILITY_NAME_SHORTID.pdf"""
        
        # Use inspection date if available, otherwise current date
        if inspection_date:
            try:
                # Handle various date formats that might come from PDF
                if '/' in inspection_date:
                    # Format: MM/DD/YYYY
                    date_obj = datetime.strptime(inspection_date, '%m/%d/%Y')
                else:
                    # Format: YYYY-MM-DD or other formats
                    date_obj = datetime.strptime(inspection_date, '%Y-%m-%d')
                date_prefix = date_obj.strftime('%Y%m%d')
            except:
                # Fallback to current date if date parsing fails
                date_prefix = datetime.now().strftime('%Y%m%d')
        else:
            # Use current date as fallback
            date_prefix = datetime.now().strftime('%Y%m%d')
        
        # Clean facility name: remove spaces, special chars, limit length
        safe_name = NameUtilities.sanitize_filename(facility_name)
        safe_name = safe_name.replace('_', '').upper()[:20]  # Remove underscores, uppercase, limit length
        
        # Extract short ID (last part after final dash)
        if inspection_id and '-' in inspection_id:
            short_id = inspection_id.split('-')[-1]  # Get last part after final dash
        else:
            short_id = inspection_id[:12] if inspection_id else 'UNKNOWN'
        
        return f"{date_prefix}_{safe_name}_{short_id}.pdf"
```

### src/services/database_service.py
```python
import sqlite3
from datetime import datetime
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core.database import database

class DatabaseService:
    def __init__(self):
        self.db = database
    
    def create_facility(self, facility_data):
        """Create a new facility record"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO facilities (
                INSERT INTO facilities (
                    name, street_address, establishment_id, permit_holder, phone, 
                    city, state, zip_code, program_identifier
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                facility_data.get('name'),
                facility_data.get('street_address'),
                facility_data.get('establishment_id'),
                facility_data.get('permit_holder'),
                facility_data.get('phone'),
                facility_data.get('city'),
                facility_data.get('state', 'CA'),
                facility_data.get('zip_code'),
                facility_data.get('program_identifier')
            ))
            return cursor.lastrowid
    
    def get_facility_by_establishment_id(self, establishment_id):
        """Find facility by establishment ID"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM facilities WHERE establishment_id = ?",
                (establishment_id,)
            )
            return cursor.fetchone()
    
    def create_inspection_report(self, report_data):
        """Create a new inspection report"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO inspection_reports (
                    facility_id, permit_id, inspection_date, inspector_name,
                    inspector_phone, total_violations, severity_score, closure_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                report_data.get('facility_id'),
                report_data.get('permit_id'),
                report_data.get('inspection_date'),
                report_data.get('inspector_name'),
                report_data.get('inspector_phone'),
                report_data.get('total_violations', 0),
                report_data.get('severity_score', 0.0),
                report_data.get('closure_status', 'operational')
            ))
            return cursor.lastrowid

    def get_or_create_facility(self, name, street_address):
        """Look up or create a facility record by name + street_address"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM facilities WHERE name = ? AND street_address = ?",
                (name, street_address)
            )
            result = cursor.fetchone()
            if result:
                return result[0]

            # If not found, insert minimal placeholder
            cursor.execute("""
                INSERT INTO facilities (name, street_address, state)
                VALUES (?, ?, ?)
            """, (name, street_address, 'CA'))
            return cursor.lastrowid

    def get_facility_by_permit_id(self, permit_id):
        """Return facility row dict by permit ID, or None if not found"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM facilities WHERE permit_id = ?", (permit_id,))
            row = cursor.fetchone()
            if not row:
                return None
            # Map row to dict
            col_names = [desc[0] for desc in cursor.description]
            return dict(zip(col_names, row))
```

### src/services/download_lock_service.py
```python
#!/usr/bin/env python3
"""
DownloadLockService - Pool Scout Pro
Single-flight guard with BOTH:
- process-local mutex (blocks re-entrancy inside same Gunicorn worker)
- cross-process file lock via flock (blocks other workers/processes)

Never throws; returns structured {acquired: bool, info}.
"""

import fcntl
import json
import os
import time
import threading
from typing import Tuple, Dict, Optional

# Process-local guard (per interpreter / worker)
_PROCESS_LOCK = threading.Lock()
_PROCESS_HELD = False
_PROCESS_HOLDER = {"job_id": None, "pid": None, "ts": None}

class DownloadLockService:
    def __init__(self, lock_file: str = "/tmp/pool_scout_pro.download.lock", ttl_seconds: int = 1800):
        self.lock_file = lock_file
        self.ttl_seconds = ttl_seconds
        self._fd: Optional[int] = None
        self._owns_file_lock = False

    def acquire(self, job_id: str) -> Tuple[bool, Dict]:
        """
        Acquire both the process-local and file lock. If either is held, deny.
        """
        global _PROCESS_HELD, _PROCESS_HOLDER

        # 1) Process-local guard
        if _PROCESS_HELD:
            age = int(time.time() - (_PROCESS_HOLDER.get("ts") or time.time()))
            msg = f"Local download already in progress (job {_PROCESS_HOLDER.get('job_id','?')}, pid {_PROCESS_HOLDER.get('pid','?')}, age {age}s)."
            return False, {"message": msg, "holder": dict(_PROCESS_HOLDER)}

        with _PROCESS_LOCK:
            if _PROCESS_HELD:
                age = int(time.time() - (_PROCESS_HOLDER.get("ts") or time.time()))
                msg = f"Local download already in progress (job {_PROCESS_HOLDER.get('job_id','?')}, pid {_PROCESS_HOLDER.get('pid','?')}, age {age}s)."
                return False, {"message": msg, "holder": dict(_PROCESS_HOLDER)}

            # set local ownership BEFORE file lock to block re-entrancy
            _PROCESS_HELD = True
            _PROCESS_HOLDER = {"job_id": job_id, "pid": os.getpid(), "ts": int(time.time())}

        # 2) Cross-process file lock
        try:
            os.makedirs(os.path.dirname(self.lock_file), exist_ok=True)
        except Exception:
            pass

        try:
            fd = os.open(self.lock_file, os.O_CREAT | os.O_RDWR, 0o644)
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                holder = self._read_holder(fd)
                msg = "Download already in progress by another worker."
                if holder:
                    age = int(time.time() - holder.get("ts", 0))
                    msg = f"Download already in progress (job {holder.get('job_id','unknown')}, pid {holder.get('pid','?')}, age {age}s)."
                # release process-local ownership since we didn't get file lock
                self._release_process_local()
                os.close(fd)
                return False, {"message": msg, "holder": holder or {}}

            # we hold the file lock
            self._fd = fd
            self._owns_file_lock = True
            holder_data = {"job_id": job_id, "pid": os.getpid(), "ts": int(time.time())}
            os.ftruncate(self._fd, 0)
            os.lseek(self._fd, 0, os.SEEK_SET)
            os.write(self._fd, json.dumps(holder_data).encode("utf-8"))
            os.fsync(self._fd)
            return True, {"message": "Lock acquired", "holder": holder_data}

        except Exception as e:
            # release process-local guard on error
            self._release_process_local()
            return False, {"message": f"Failed to acquire lock: {e}"}

    def release(self) -> None:
        try:
            # release file lock first
            if self._fd is not None and self._owns_file_lock:
                try:
                    fcntl.flock(self._fd, fcntl.LOCK_UN)
                finally:
                    os.close(self._fd)
                self._fd = None
                self._owns_file_lock = False
                try:
                    os.remove(self.lock_file)
                except Exception:
                    pass
        finally:
            # always release local guard
            self._release_process_local()

    def _release_process_local(self):
        global _PROCESS_HELD, _PROCESS_HOLDER
        with _PROCESS_LOCK:
            _PROCESS_HELD = False
            _PROCESS_HOLDER = {"job_id": None, "pid": None, "ts": None}

    def _read_holder(self, fd: int):
        try:
            os.lseek(fd, 0, os.SEEK_SET)
            raw = os.read(fd, 4096)
            if not raw:
                return None
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.release()
```

### src/services/duplicate_prevention_service.py
```python
"""
Duplicate Prevention Service - Pool Scout Pro
Pure business logic service for duplicate detection.
No UI concerns, no state management.
"""

import sqlite3

class DuplicatePreventionService:
    def __init__(self):
        self.db_path = "data/reports.db"
    
    def is_duplicate_by_inspection_id(self, inspection_id, search_date):
        """
        Check if PDF already exists for this inspection ID and date.
        
        Args:
            inspection_id: The inspection ID to check
            search_date: Date in YYYY-MM-DD format
            
        Returns:
            bool: True if duplicate exists, False otherwise
        """
        if not inspection_id or not search_date:
            return False

        try:
            # Convert search date to filename format
            search_date_formatted = search_date.replace('-', '') if search_date else None
            if not search_date_formatted:
                return False

            conn = sqlite3.connect(self.db_path, timeout=10)
            cursor = conn.cursor()
            
            # Check for existing PDF filename pattern
            pattern = f'{search_date_formatted}_%_{inspection_id}.pdf'
            
            cursor.execute("""
                SELECT COUNT(*) FROM inspection_reports
                WHERE pdf_filename LIKE ? AND pdf_filename IS NOT NULL
            """, (pattern,))
            
            count = cursor.fetchone()[0]
            conn.close()
            
            return count > 0

        except Exception:
            # Silent failure - return False to allow retry
            return False

    def is_duplicate_by_name(self, facility_name):
        """
        Check if facility exists by name.
        
        Args:
            facility_name: Name of facility to check
            
        Returns:
            bool: True if facility exists, False otherwise
            
        Note: This method is deprecated - prefer inspection_id based checking
        """
        return False
```

### src/services/failed_download_service.py
```python
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
```

### src/services/pdf_downloader.py
```python
#!/usr/bin/env python3
"""
PDF Downloader with Transactional Database Updates
Enhanced with proper transaction flow: Download → Extract → Database

Key responsibilities:
- Download PDF files successfully FIRST
- Extract and validate data SECOND  
- Insert database records ONLY after successful download + extraction
- Store failed downloads for automatic retry via FailedDownloadService
- Trigger enterprise retry service when failures occur
- Use human-like timing patterns to avoid detection

External dependencies:
- core.browser.BrowserManager
- core.error_handler.ErrorHandler, with_error_handling, CommonCleanup
- core.utilities.NameUtilities, ValidationUtilities, FileUtilities, TextUtilities
- core.settings.settings
- services.download_lock_service.DownloadLockService
- services.failed_download_service.FailedDownloadService
- services.pdf_extractor.PDFExtractor
- requests, selenium, pathlib, pytz (indirect), random, etc.
"""

import time
import os
import requests
import random
from pathlib import Path
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from core.browser import BrowserManager
from core.error_handler import ErrorHandler, with_error_handling, CommonCleanup
from core.utilities import NameUtilities, ValidationUtilities, FileUtilities
from services.pdf_extractor import PDFExtractor
from core.settings import settings
from services.download_lock_service import DownloadLockService
from services.failed_download_service import FailedDownloadService

class PDFDownloader:
    """PDF Downloader with transactional database updates"""

    def __init__(self, shared_driver=None):
        self.browser_manager = BrowserManager()
        self.extractor = PDFExtractor()
        self.shared_driver = shared_driver
        self.error_handler = ErrorHandler(__name__)
        self.lock_service = DownloadLockService()
        self.failed_download_service = FailedDownloadService()

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

        # Set up download path correctly with current year
        from datetime import datetime
        current_year = str(datetime.now().year)
        base_path = Path(settings.pdf_download_path)
        self.download_path = base_path / current_year
        self.download_path.mkdir(parents=True, exist_ok=True)
        print(f"📁 Download path: {self.download_path}")

        # Human-like timing state
        self.download_count = 0
        self.next_long_pause = random.randint(8, 10)  # Random pause every 8-10 downloads
        self.next_browser_refresh = 14  # Refresh browser every 14 downloads
        
        # Enterprise integration state
        self.batch_has_failures = False

    @with_error_handling("PDF downloads", default_return={'success': False, 'code': 'ERROR', 'successful': 0, 'failed': 0, 'results': []})
    def download_pdfs_from_facilities(self, facilities_data):
        """
        Download PDFs for multiple facilities with transactional database updates.
        NEW FLOW: Download → Extract → Database (only on success)
        """
        if not facilities_data:
            print("❌ No facilities data provided")
            return {'success': False, 'code': 'NO_INPUT', 'successful': 0, 'failed': 0, 'results': [], 'message': 'No facilities to process.'}

        # --- Acquire single-flight lock ---
        job_id = self._make_job_id()
        acquired, info = self.lock_service.acquire(job_id=job_id)
        # Initialize progress tracking
        self.progress_tracker = {'current_facility': '', 'completed': 0, 'total': len(facilities_data), 'status': 'downloading'}
        if not acquired:
            msg = info.get("message", "Download already in progress")
            print(f"🔒 {msg}")
            return {
                'success': False,
                'code': 'ALREADY_RUNNING',
                'message': msg,
                'successful': 0,
                'failed': 0,
                'results': []
            }

        print(f"🔄 Starting PDF downloads for {len(facilities_data)} facilities (job {job_id})")
        print(f"📋 NEW TRANSACTIONAL FLOW: Download → Extract → Database")

        successful_downloads = 0
        failed_downloads = 0
        results = []
        self.batch_has_failures = False

        # Use shared driver if available, otherwise create new one
        driver = self.shared_driver if self.shared_driver else self.browser_manager.create_driver()
        print("🔄 Using shared browser session" if self.shared_driver else "🔄 Created new browser session")

        try:
            for i, facility in enumerate(facilities_data, 1):
                facility_name = facility.get('name', 'Unknown')
                pdf_url = facility.get('pdf_url') or facility.get('url')  # tolerate 'url' key from upstream

                # Validate PDF URL using utilities
                if not pdf_url or not ValidationUtilities.is_valid_url(pdf_url):
                    self.error_handler.log_warning(
                        "PDF URL validation",
                        f"Invalid or missing PDF URL for {facility_name}",
                        {'facility': facility_name, 'url': pdf_url, 'job_id': job_id}
                    )
                    # Store as failed download for retry
                    self._store_failed_download_with_trigger(
                        facility, 
                        {'reason': 'invalid_url', 'details': 'Invalid or missing PDF URL'}, 
                        job_id
                    )
                    failed_downloads += 1
                    results.append({'facility': facility_name, 'success': False, 'error': 'Invalid or missing PDF URL'})
                    continue

                print(f"\n🔄 [{i}/{len(facilities_data)}] Processing: {facility_name}")
                # Update progress tracking
                getattr(self, 'progress_tracker', {}).update({'current_facility': facility_name, 'completed': i-1, 'total': len(facilities_data)})

                # Extract inspection ID + build filename
                from core.utilities import TextUtilities
                inspection_id = TextUtilities.extract_inspection_id_from_url(pdf_url)
                print(f"📋 Inspection ID: {inspection_id}")

                inspection_date = facility.get('inspection_date')
                filename = FileUtilities.generate_inspection_filename(facility_name, inspection_id, inspection_date)
                filepath = self.download_path / filename

                # TRANSACTIONAL FLOW: Download → Extract → Database
                success = self._process_facility_transactionally(
                    facility, pdf_url, filepath, driver, job_id, inspection_id
                )

                if success:
                    successful_downloads += 1
                    file_size = FileUtilities.get_file_size_mb(str(filepath))
                    results.append({
                        'facility': facility_name,
                        'success': True,
                        'filename': filename,
                        'file_size_mb': file_size
                    })
                    print(f"✅ COMPLETE: {facility_name} → {filename}")
                else:
                    failed_downloads += 1
                    results.append({'facility': facility_name, 'success': False, 'error': 'Download or extraction failed'})

                # Human-like timing patterns
                self._apply_human_timing(i, len(facilities_data), driver)

        finally:
            # Trigger enterprise retry service if there were failures
            if self.batch_has_failures:
                self._trigger_enterprise_retry_service(job_id, failed_downloads)
            
            # Release resources
            if not self.shared_driver and 'driver' in locals():
                CommonCleanup.close_browser_driver(driver)
            # Release the single-flight lock
            self.lock_service.release()

        print(f"\n🎯 Download Summary (job {job_id}):")
        print(f"   ✅ Successful: {successful_downloads}")
        print(f"   ❌ Failed: {failed_downloads}")
        
        if self.batch_has_failures:
            print(f"   🎯 Enterprise retry service triggered for {failed_downloads} failures")

        return {
            'success': True,
            'code': 'OK',
            'successful': successful_downloads,
            'failed': failed_downloads,
            'results': results,
            'job_id': job_id,
            'retry_triggered': self.batch_has_failures
        }

    def _process_facility_transactionally(self, facility, pdf_url, filepath, driver, job_id, inspection_id):
        """
        TRANSACTIONAL PROCESSING: Download → Extract → Database
        Only insert database records if ALL steps succeed
        """
        facility_name = facility.get('name', 'Unknown')
        
        try:
            # STEP 1: Download PDF file
            print(f"📥 STEP 1: Downloading PDF...")
            download_success, download_error = self._download_pdf_file_only(pdf_url, filepath, driver)
            
            if not download_success:
                print(f"❌ Download failed: {download_error.get('reason')}")
                self._store_failed_download_with_trigger(facility, download_error, job_id)
                return False

            print(f"✅ Download successful: {filepath.name}")

            # STEP 2: Extract data from PDF and save to database
            print(f"📄 STEP 2: Extracting and saving...")
            extraction_result = self.extractor.extract_and_save(
                pdf_path=str(filepath),
                facility_name=facility_name,
                inspection_id=inspection_id
            )
            
            if not extraction_result:
                print(f"❌ Extraction and save failed")
                # Remove downloaded file since extraction/save failed
                try:
                    filepath.unlink()
                    print(f"🗑️ Removed failed PDF: {filepath.name}")
                except:
                    pass
                
                self._store_failed_download_with_trigger(
                    facility,
                    {'reason': 'extraction_failed', 'details': 'PDF downloaded but extraction/save failed'},
                    job_id
                )
                return False

            print(f"✅ Extraction and database save successful")
            return True

        except Exception as e:
            print(f"❌ Unexpected error in transactional processing: {str(e)}")
            
            # Clean up PDF file on any unexpected error
            try:
                if filepath.exists():
                    filepath.unlink()
                    print(f"🗑️ Cleaned up PDF after unexpected error: {filepath.name}")
            except:
                pass
            
            self.error_handler.log_error("Transactional processing", e, {
                'facility': facility_name,
                'job_id': job_id
            })
            self._store_failed_download_with_trigger(
                facility,
                {'reason': 'unexpected_error', 'details': f'Unexpected processing error: {str(e)}'},
                job_id
            )
            return False
    def _download_pdf_file_only(self, pdf_url, filepath, driver):
        """Download PDF file only - no database operations"""
        try:
            print(f"⬇️ Downloading: {pdf_url}")

            if not driver:
                return False, {
                    'reason': 'no_driver',
                    'details': 'No browser driver available'
                }

            try:
                # Set timeouts for page operations
                driver.set_page_load_timeout(30)
                
                # Navigate to inspection page
                driver.get(pdf_url)
                
                # Wait for page to load with explicit wait
                wait = WebDriverWait(driver, 10)
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                
                # Random wait to simulate human reading time
                time.sleep(random.uniform(2, 5))

                # Find PDF link with timeout
                pdf_link_element = wait.until(
                    EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "View Original Inspection PDF"))
                )
                pdf_href = pdf_link_element.get_attribute("href")
                
                if not pdf_href:
                    return False, {
                        'reason': 'no_pdf_link',
                        'details': 'Could not find PDF download link on page'
                    }

                # Construct full URL if needed
                actual_pdf_url = ("https://inspections.myhealthdepartment.com" + pdf_href) if pdf_href.startswith("/") else pdf_href
                print(f"📎 Found PDF link: {actual_pdf_url}")

                # Browser cookies → session
                try:
                    cookies = {c["name"]: c["value"] for c in driver.get_cookies()}
                    if cookies:
                        self.session.cookies.update(cookies)
                        print(f"🍪 Updated session with {len(cookies)} cookies")
                except Exception as e:
                    print(f"⚠️ Cookie extraction failed: {e}")

                # Download PDF with robust error handling
                print(f"🌐 Attempting HTTP download...")
                try:
                    response = self.session.get(actual_pdf_url, timeout=60, stream=True)
                    print(f"📡 HTTP Response: {response.status_code} {response.reason}")
                    
                    # Check for 403 specifically before other processing
                    if response.status_code == 403:
                        return False, {
                            'reason': 'blocked_403',
                            'details': f'HTTP 403 Forbidden - EMD server blocked PDF download request'
                        }
                    
                    # Check for other HTTP errors
                    if response.status_code >= 400:
                        return False, {
                            'reason': f'http_error_{response.status_code}',
                            'details': f'HTTP {response.status_code} {response.reason} - Server error downloading PDF'
                        }
                    
                    # Success response - check content
                    content_type = (response.headers.get('content-type') or '').lower()
                    content_length = response.headers.get('content-length')
                    print(f"📄 Content-Type: {content_type}, Length: {content_length}")
                    
                    # Read content with timeout protection
                    content = b''
                    start_time = time.time()
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            content += chunk
                            # Timeout protection for large files
                            if time.time() - start_time > 120:  # 2 minute max for download
                                return False, {
                                    'reason': 'download_timeout',
                                    'details': 'PDF download took longer than 2 minutes'
                                }
                    
                    print(f"📦 Downloaded {len(content)} bytes")
                    
                except requests.exceptions.Timeout as e:
                    return False, {
                        'reason': 'request_timeout',
                        'details': f'HTTP request timeout after 60 seconds: {str(e)}'
                    }
                    
                except requests.exceptions.ConnectionError as e:
                    return False, {
                        'reason': 'connection_error',
                        'details': f'Connection error downloading PDF: {str(e)}'
                    }
                    
                except requests.exceptions.RequestException as e:
                    return False, {
                        'reason': 'request_error',
                        'details': f'Request error downloading PDF: {str(e)}'
                    }
                
            except TimeoutException as e:
                return False, {
                    'reason': 'selenium_timeout',
                    'details': f'Selenium timeout finding PDF link: {str(e)}'
                }
                
            except Exception as e:
                return False, {
                    'reason': 'navigation_error',
                    'details': f'Failed to navigate to PDF page: {str(e)}'
                }

            # Validate content
            if len(content) < 5000:
                return False, {
                    'reason': 'invalid_content_size',
                    'details': f'Downloaded content too small: {len(content)} bytes (likely error page)'
                }

            if 'pdf' not in content_type and not content.startswith(b'%PDF'):
                return False, {
                    'reason': 'invalid_content_type',
                    'details': f'Not a PDF: Content-Type={content_type}, starts with: {content[:20]}'
                }

            # Save file
            print(f"💾 Saving to: {filepath}")
            with open(filepath, 'wb') as f:
                f.write(content)

            # Verify file
            if FileUtilities.is_pdf_file(str(filepath)) and filepath.exists() and filepath.stat().st_size > 1000:
                file_size = FileUtilities.get_file_size_mb(str(filepath))
                print(f"✅ Downloaded: {filepath.name} ({file_size:.2f}MB)")
                return True, {'reason': 'success'}
            else:
                return False, {
                    'reason': 'file_verification_failed',
                    'details': f'Saved file failed verification - exists: {filepath.exists()}, size: {filepath.stat().st_size if filepath.exists() else 0}'
                }

        except Exception as e:
            self.error_handler.log_error("PDF download only", e, {'pdf_url': pdf_url, 'filepath': str(filepath)})
            return False, {
                'reason': 'unexpected_error',
                'details': f'Unexpected download error: {str(e)}'
            }

    def _extract_pdf_data_only(self, filepath, facility_name, inspection_id):
        """Extract data from PDF only - no database operations"""
        try:
            print(f"🔍 Processing: {filepath.name}")
            
            # Use the existing PDF extractor but don't save to database yet
            extraction_result = self.extractor.extract_pdf_data_only(
                pdf_path=str(filepath),
                facility_name=facility_name,
                inspection_id=inspection_id
            )
            
            if extraction_result and extraction_result.get('success'):
                print(f"📊 Extracted: {len(extraction_result.get('violations', []))} violations, {len(extraction_result.get('equipment', []))} equipment records")
                return True, extraction_result
            else:
                return False, None

        except Exception as e:
            self.error_handler.log_error("PDF extraction only", e, {
                'filepath': str(filepath),
                'facility': facility_name
            })
            return False, None

    def _save_to_database_only(self, filepath, facility_name, inspection_id, extracted_data):
        """Save extracted data to database only"""
        try:
            # Use the existing PDF extractor's save method with the extracted data
            save_result = self.extractor.save_extracted_data_to_database(
                extracted_data=extracted_data,
                pdf_filename=filepath.name,
                facility_name=facility_name,
                inspection_id=inspection_id
            )
            
            if save_result and save_result.get('success'):
                print(f"💾 Saved to database: facility_id={save_result.get('facility_id')}, report_id={save_result.get('report_id')}")
                return True
            else:
                return False

        except Exception as e:
            self.error_handler.log_error("Database save only", e, {
                'filepath': str(filepath),
                'facility': facility_name
            })
            return False

    def _store_failed_download_with_trigger(self, facility, error_info, batch_id):
        """Store failed download for retry and mark batch as having failures"""
        try:
            facility_name = facility.get('name', 'Unknown')
            pdf_url = facility.get('pdf_url') or facility.get('url')
            inspection_id = facility.get('inspection_id')
            inspection_date = facility.get('inspection_date')
            
            # Store in failed downloads table
            record_id = self.failed_download_service.store_failed_download(
                facility_name=facility_name,
                pdf_url=pdf_url,
                inspection_id=inspection_id,
                inspection_date=inspection_date,
                failure_reason=error_info.get('reason'),
                failure_details=error_info.get('details'),
                batch_id=batch_id
            )
            
            if record_id:
                self.batch_has_failures = True
                print(f"💾 Stored failed download (ID: {record_id}) for retry")
            
        except Exception as e:
            self.error_handler.log_error("Store failed download with trigger", e, {'facility': facility.get('name', 'Unknown')})

    def _trigger_enterprise_retry_service(self, batch_id, failure_count):
        """Trigger enterprise retry service for failed downloads"""
        try:
            # Create trigger file for enterprise service
            trigger_file = '/tmp/pool_scout_retry_needed'
            Path(trigger_file).touch()
            
            self.error_handler.log_warning(
                "Enterprise retry triggered",
                f"Triggered retry service for batch {batch_id}",
                {
                    'batch_id': batch_id,
                    'failure_count': failure_count,
                    'trigger_file': trigger_file
                }
            )
            
            print(f"🎯 Triggered enterprise retry service (trigger file: {trigger_file})")
            return True
            
        except Exception as e:
            self.error_handler.log_error("Trigger enterprise retry", e, {
                'batch_id': batch_id,
                'failure_count': failure_count
            })
            print(f"⚠️ Failed to trigger enterprise retry service: {e}")
            return False

    def _apply_human_timing(self, current_index, total_count, driver):
        """Apply human-like timing patterns between downloads"""
        self.download_count += 1
        
        # Check if we need a browser refresh
        if self.download_count % self.next_browser_refresh == 0 and current_index < total_count:
            print("🔄 Refreshing browser session (human-like behavior)")
            try:
                driver.refresh()
                time.sleep(random.uniform(2, 4))
            except Exception as e:
                self.error_handler.log_warning("Browser refresh", f"Failed to refresh browser: {e}")
        
        # Check if we need a longer pause
        if self.download_count == self.next_long_pause and current_index < total_count:
            pause_duration = random.randint(10, 20)
            print(f"⏸️ Taking longer pause: {pause_duration}s (human-like behavior)")
            time.sleep(pause_duration)
            # Set next long pause randomly
            self.next_long_pause += random.randint(8, 10)
        
        # Regular random delay between downloads
        if current_index < total_count:
            delay = random.uniform(2, 6)
            print(f"⏱️ Waiting {delay:.1f}s before next download...")
            time.sleep(delay)

    def download_single_pdf(self, facility_data):
        """Download a single PDF for testing purposes"""
        facilities_list = [facility_data] if isinstance(facility_data, dict) else facility_data
        return self.download_pdfs_from_facilities(facilities_list)

    def get_pdf_links_from_page(self, driver):
        """Extract PDF download links from current page with validation"""
        pdf_links = []
        try:
            pdf_elements = driver.find_elements(By.PARTIAL_LINK_TEXT, "View Original Inspection PDF")
            for element in pdf_elements:
                try:
                    pdf_url = element.get_attribute('href')
                    if pdf_url and ValidationUtilities.is_valid_url(pdf_url) and pdf_url not in pdf_links:
                        pdf_links.append(pdf_url)
                except Exception as e:
                    self.error_handler.log_warning("PDF link extraction", "Failed to get PDF link from element", {'error': str(e)})
                    continue
        except Exception as e:
            self.error_handler.log_error("PDF links extraction", e)
        return pdf_links

    def close(self):
        """Clean up resources"""
        CommonCleanup.close_http_session(self.session)
        if not self.shared_driver:
            try:
                self.browser_manager.close_driver()
            except Exception as e:
                self.error_handler.log_warning("Driver cleanup", "Failed to close browser driver", {"error": str(e)})

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _make_job_id(self):
        import datetime, os
        return f"{datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}-{os.getpid()}"
```

### src/services/pdf_extractor.py
```python
#!/usr/bin/env python3
"""
Sacramento County PDF Extractor - Pool Scout Pro

Extracts inspection data from Sacramento County PDFs and saves to normalized database.
Uses proper foreign key relationships and enterprise data structure.

Dependencies:
- pypdfium2 for PDF text extraction
- sqlite3 for database operations
- core.error_handler for standardized error handling
- Database: data/reports.db with facilities, inspection_reports, violations, pool_equipment, water_chemistry tables
"""

import warnings
warnings.filterwarnings("ignore", message="get_text_range.*will be implicitly redirected.*", category=UserWarning)
import pypdfium2 as pdfium
import re
import sqlite3
import os

from datetime import datetime
from core.error_handler import ErrorHandler, with_error_handling, CommonCleanup

class PDFExtractor:
    def __init__(self, db_path='data/reports.db'):
        self.db_path = db_path
        self.error_handler = ErrorHandler(__name__)
        
    @with_error_handling("PDF extraction and save", default_return=None)
    def extract_and_save(self, pdf_path, facility_name=None, inspection_id=None):
        """Extract complete data from Sacramento County PDFs with proper schema"""
        print(f"🔍 Processing: {os.path.basename(pdf_path)}")
        
        text = self.extract_text(pdf_path)
        if not text:
            return None
        
        print(f"📄 Extracted {len(text)} characters")
        
        data = {
            'inspection_id': inspection_id,
            'facility_name': facility_name,
            'permit_id': self._find_permit_id(text),
            'establishment_id': self._find_establishment_id(text),
            'inspection_date': self._find_date(text),
            'program_info': self._find_program_identifier(text),
            'raw_address': self._extract_address(text),
            'permit_holder': self._extract_permit_holder(text),
            'phone': self._extract_phone(text),
            'inspection_type': self._extract_inspection_type(text),
            'pdf_filename': os.path.basename(pdf_path),
            'inspector_info': self._extract_inspector_info(text),
            'violations': self._extract_violations(text),
            'equipment': self._extract_equipment(text),
            'water_chemistry': self._extract_water_chemistry(text),
            'report_notes': self._extract_report_notes(text)
        }
        
        return self._save_complete_data(data)

    def extract_text(self, pdf_path):
        """Extract text using pypdfium2 with basic error handling"""
        try:
            pdf = pdfium.PdfDocument(pdf_path)
            text_parts = []
            
            for page_num in range(min(10, len(pdf))):  # Limit to first 10 pages
                page = pdf[page_num]
                textpage = page.get_textpage()
                text = textpage.get_text_range()
                text_parts.append(text)
                textpage.close()
                page.close()
            
            pdf.close()
            return "\n".join(text_parts)
            
        except Exception as e:
            self.error_handler.log_error("PDF text extraction", e, {
                "pdf_path": pdf_path
            })
            return ""

    def _save_complete_data(self, data):
        """Save extracted data to database with proper enterprise schema"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            facility_id = self._get_or_create_facility(cursor, data)
            
            violations = data.get('violations', [])
            total_violations = len(violations) if violations else 0
            major_violations = sum(1 for v in violations if v.get('is_major_violation')) if violations else 0
            severity_score = sum(v.get('severity_score', 1.0) for v in violations) if violations else 0.0
            
            inspector_info = data.get('inspector_info', {})
            
            cursor.execute('''
                INSERT INTO inspection_reports 
                (facility_id, permit_id, establishment_id, inspection_date, inspection_id, 
                 inspector_name, inspector_phone, accepted_by,
                 total_violations, major_violations, severity_score,
                 pdf_filename, report_notes, processed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                facility_id, 
                data['permit_id'], 
                data['establishment_id'], 
                data['inspection_date'], 
                data.get('inspection_id'),
                inspector_info.get('name') if isinstance(inspector_info, dict) else inspector_info,
                inspector_info.get('phone') if isinstance(inspector_info, dict) else None,
                inspector_info.get('accepted_by') if isinstance(inspector_info, dict) else None,
                total_violations, 
                major_violations, 
                severity_score,
                data['pdf_filename'], 
                data['report_notes'], 
                datetime.now().isoformat()
            ))
            
            report_id = cursor.lastrowid
            print(f"✅ Saved inspection report: ID {report_id}")
            print(f"   📊 Violations: {total_violations} total, {major_violations} major")
            
            # Save violations with error handling for each violation
            if violations:
                self._save_violations(cursor, violations, report_id, facility_id)
            
            # Save equipment data with error handling
            if data.get('equipment'):
                self._save_equipment_data(cursor, data.get('equipment', {}), report_id, facility_id)
            
            # Save water chemistry with error handling
            if data.get('water_chemistry'):
                self._save_water_chemistry(cursor, data.get('water_chemistry', {}), report_id, facility_id)
            
            # Update download status to extracted
            cursor.execute("""
                UPDATE inspection_reports 
                SET download_status = 'extracted' 
                WHERE id = ?
            """, (report_id,))
            conn.commit()
            
            print(f"🎯 Complete data saved for: {data.get('facility_name', 'Unknown')}")
            return {
                'facility_id': facility_id,
                'report_id': report_id,
                'total_violations': total_violations,
                'major_violations': major_violations,
                'severity_score': severity_score
            }
            
        except sqlite3.IntegrityError as e:
            self.error_handler.log_error("Database integrity", e, {
                'facility_name': data.get('facility_name'),
                'permit_id': data.get('permit_id')
            })
            return None
        except Exception as e:
            self.error_handler.log_error("Database save", e, {
                'facility_name': data.get('facility_name'),
                'pdf_filename': data.get('pdf_filename')
            })
            return None
        finally:
            CommonCleanup.close_database_connection(conn)
    
    def _get_or_create_facility(self, cursor, data):
        """Create or retrieve facility with proper error handling"""
        facility_name = data.get('facility_name') or "Unknown Facility"
        program_info = data.get('program_info', {})
        raw_address = data.get('raw_address', {})

        try:
            # Check if facility exists
            cursor.execute('SELECT id FROM facilities WHERE name = ?', (facility_name,))
            result = cursor.fetchone()
            if result:
                facility_id = result[0]

                # Update facility with new info if available
                if isinstance(program_info, dict) and program_info.get('program_identifier'):
                    cursor.execute('''
                        UPDATE facilities
                        SET program_identifier = ?, facility_type = ?, 
                            street_address = ?, city = ?, state = ?, zip_code = ?, permit_holder = ?, phone = ?
                        WHERE id = ?
                    ''', (
                        program_info.get('program_identifier'),
                        program_info.get('facility_type', 'POOL'),
                        raw_address.get('street_address') if isinstance(raw_address, dict) else raw_address,
                        raw_address.get('city') if isinstance(raw_address, dict) else None,
                        'CA',
                        raw_address.get('zip_code') if isinstance(raw_address, dict) else None,
                        data.get('permit_holder'),
                        data.get('phone'),
                        facility_id
                    ))
                    print(f"🔄 Updated facility {facility_id} with program info and address")

                return facility_id

            # Create new facility with all available info
            cursor.execute('''
                INSERT INTO facilities (name, program_identifier, facility_type, street_address, city, state, zip_code, permit_holder, phone)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                facility_name,
                program_info.get('program_identifier') if isinstance(program_info, dict) else program_info,
                program_info.get('facility_type', 'POOL') if isinstance(program_info, dict) else 'POOL',
                raw_address.get('street_address') if isinstance(raw_address, dict) else raw_address,
                raw_address.get('city') if isinstance(raw_address, dict) else None,
                'CA',
                raw_address.get('zip_code') if isinstance(raw_address, dict) else None,
                data.get('permit_holder'),
                data.get('phone')
            ))

            facility_id = cursor.lastrowid
            print(f"✅ Created new facility {facility_id}: {facility_name}")
            if isinstance(raw_address, dict) and raw_address.get('street_address'):
                print(f"   🏠 Address: {raw_address['street_address']}, {raw_address.get('city', '')} {raw_address.get('zip_code', '')}")
            elif isinstance(raw_address, str):
                print(f"   🏠 Address: {raw_address}")
            if isinstance(program_info, dict) and program_info.get('program_identifier'):
                print(f"   🏊 Program: {program_info['program_identifier']}")

            return facility_id
            
        except Exception as e:
            self.error_handler.log_error("Facility creation/retrieval", e, {
                'facility_name': facility_name,
                'has_program_info': bool(program_info),
                'has_raw_address': bool(raw_address)
            })
            raise
            cursor.execute('''
                INSERT INTO facilities (name, program_identifier, facility_type, street_address, city, state, zip_code, permit_holder, phone)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                facility_name,
                program_info.get('program_identifier') if isinstance(program_info, dict) else program_info,
                program_info.get('facility_type', 'POOL') if isinstance(program_info, dict) else 'POOL',
                raw_address.get('street_address') if isinstance(raw_address, dict) else raw_address,
                raw_address.get('city') if isinstance(raw_address, dict) else None,
                'CA',
                raw_address.get('city') if isinstance(raw_address, dict) else None,
                'CA',
                raw_address.get('zip_code') if isinstance(raw_address, dict) else None,
                data.get('permit_holder'),
                data.get('phone')
            ))

            facility_id = cursor.lastrowid
            print(f"✅ Created new facility {facility_id}: {facility_name}")
            if isinstance(raw_address, dict) and raw_address.get('street_address'):
                print(f"   🏠 Address: {raw_address['street_address']} {raw_address.get('zip_code', '')}")
            elif isinstance(raw_address, str):
                print(f"   🏠 Address: {raw_address}")
            if isinstance(program_info, dict) and program_info.get('program_identifier'):
                print(f"   🏊 Program: {program_info['program_identifier']}")

            return facility_id
            
        except Exception as e:
            self.error_handler.log_error("Facility creation/retrieval", e, {
                'facility_name': facility_name,
                'has_program_info': bool(program_info),
                'has_raw_address': bool(raw_address)
            })
            raise

    def _save_violations(self, cursor, violations, report_id, facility_id):
        """Save violations with individual error handling"""
        if not violations:
            return
            
        saved_violations = 0
        for i, violation in enumerate(violations):
            try:
                cursor.execute('''
                    INSERT INTO violations 
                    (report_id, facility_id, violation_code, violation_title,
                     observations, code_description, is_major_violation, 
                     corrective_actions, severity_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    report_id, facility_id,
                    violation.get('violation_code'),
                    violation.get('violation_title'),
                    violation.get('observations'),
                    violation.get('code_description'),
                    violation.get('is_major_violation', False),
                    violation.get('corrective_actions'),
                    violation.get('severity_score', 1.0)
                ))
                saved_violations += 1
            except Exception as e:
                self.error_handler.log_warning("Violation save", 
                    f"Failed to save violation {i+1}", {
                        'violation_code': violation.get('violation_code'),
                        'error': str(e)
                    })
        
        if saved_violations > 0:
            print(f"   ✅ Saved {saved_violations}/{len(violations)} violations")

    def _save_equipment_data(self, cursor, equipment, report_id, facility_id):
        """Save equipment data with error handling"""
        if not equipment:
            return
            
        try:
            cursor.execute('''
                INSERT INTO pool_equipment 
                (report_id, facility_id, capacity_gallons, pump_gpm, 
                 equipment_description, specialized_equipment)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                report_id, facility_id,
                equipment.get('capacity_gallons'),
                equipment.get('pump_gpm'),
                equipment.get('equipment_description') if isinstance(equipment, dict) else str(equipment),
                equipment.get('specialized_equipment')
            ))
            print(f"   ✅ Saved equipment data")
        except Exception as e:
            self.error_handler.log_warning("Equipment save", 
                "Failed to save equipment data", {'error': str(e)})

    def _save_water_chemistry(self, cursor, chemistry, report_id, facility_id):
        """Save water chemistry with error handling"""
        if not chemistry:
            return
            
        try:
            cursor.execute('''
                INSERT INTO water_chemistry 
                (report_id, facility_id, free_chlorine_ppm, combined_chlorine_ppm,
                 ph_level, cya_ppm, pool_spa_temp_f, flow_rate_gpm)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                report_id, facility_id,
                chemistry.get('free_chlorine_ppm'),
                chemistry.get('combined_chlorine_ppm'),
                chemistry.get('ph_level'),
                chemistry.get('cya_ppm'),
                chemistry.get('pool_spa_temp_f'),
                chemistry.get('flow_rate_gpm')
            ))
            print(f"   ✅ Saved water chemistry data")
        except Exception as e:
            self.error_handler.log_warning("Water chemistry save", 
                "Failed to save water chemistry data", {'error': str(e)})

    # Extraction methods - fixed patterns for Sacramento County PDFs
    def _find_permit_id(self, text):
        """Extract permit ID from text"""
        patterns = [
            r'Permit\s*(?:ID|#)?[:\s]*([A-Z0-9\-]+)',
            r'(?:Permit|ID)\s*[#:]?\s*([A-Z0-9\-]{6,})',
            r'([A-Z]{2,3}\d{4,})',
            r'ID[:\s]*([A-Z0-9\-]+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0].strip()
        return None

    def _find_establishment_id(self, text):
        """Extract establishment ID"""
        patterns = [
            r'Establishment\s*(?:ID)?[:\s]*([A-Z0-9\-]+)',
            r'Est\.?\s*ID[:\s]*([A-Z0-9\-]+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0].strip()
        return None

    def _find_date(self, text):
        """Extract inspection date"""
        patterns = [
            r'(?:Inspection|Date)[:\s]*(\d{1,2}/\d{1,2}/\d{4})',
            r'(\d{1,2}/\d{1,2}/\d{4})',
            r'(\d{4}-\d{2}-\d{2})'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0]
        return None

    def _find_program_identifier(self, text):
        """Extract complete program identifier information"""
        program_patterns = [
            r'Program\s*Identifier[:\s]*([^\n]+)',
            r'Program[:\s]*([^\n]+(?:POOL|SPA)[^\n]*)',
            r'Type[:\s]*([^\n]*(?:POOL|SPA)[^\n]*)'
        ]
        
        program_identifier = None
        for pattern in program_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                program_identifier = matches[0].strip()
                break
        
        # Determine facility type
        facility_type = "POOL"  # default
        if program_identifier:
            if "SPA" in program_identifier.upper():
                facility_type = "SPA"
            elif "POOL" in program_identifier.upper():
                facility_type = "POOL"
        
        return {
            'program_identifier': program_identifier,
            'facility_type': facility_type
        }

    def _extract_address(self, text):
        """Extract facility address information with proper multi-line parsing"""
        try:
            # Look for the structured address pattern in Sacramento County PDFs
            address_pattern = r'Facility Address\s*([^\n\r]+)(?:\s*\n\r?|\s+)Facility City\s*([^\n\r]+)(?:\s*\n\r?|\s+)Facility ZIP\s*(\d{5}(?:-\d{4})?)?'
            match = re.search(address_pattern, text, re.IGNORECASE | re.MULTILINE)
            
            if match:
                street_address = match.group(1).strip()
                city = match.group(2).strip()
                zip_code = match.group(3).strip() if match.group(3) else None
                
                # Build clean address string
                full_address = street_address
                if city:
                    full_address += f", {city}"
                if zip_code:
                    full_address += f" {zip_code}"
                
                return {
                    'street_address': street_address,
                    'city': city,
                    'zip_code': zip_code,
                    'full_address': full_address
                }
            
            # Fallback to original patterns if structured format not found
            fallback_patterns = [
                r'(?:Address|Location)[:\s]*([^\n]+)',
                r'(\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Boulevard|Blvd|Lane|Ln|Way|Circle|Cir|Court|Ct)[^\n]*)',
            ]
            
            for pattern in fallback_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    address = matches[0].strip()
                    
                    # Extract zip code from fallback address
                    zip_match = re.search(r'\b(\d{5}(?:-\d{4})?)\b', address)
                    zip_code = zip_match.group(1) if zip_match else None
                    
                    # Clean address (remove CA and zip for street portion)
                    street_address = address
                    if street_address:
                        street_address = re.sub(r',?\s*CA\s*\d{5}.*$', '', street_address)
                        street_address = re.sub(r'\s*\d{5}(?:-\d{4})?\s*$', '', street_address)
                        street_address = street_address.strip()
                    
                    return {
                        'street_address': street_address,
                        'city': None,
                        'zip_code': zip_code,
                        'full_address': address
                    }
            
            return {
                'street_address': None,
                'city': None,
                'zip_code': None,
                'full_address': None
            }
            
        except Exception as e:
            self.error_handler.log_error("Address extraction", e)
            return {
                'street_address': None,
                'city': None,
                'zip_code': None,
                'full_address': None
            }
    def _extract_permit_holder(self, text):
        """Extract permit holder information"""
        patterns = [
            r'(?:Permit\s*Holder|Owner)[:\s]*([^\n]+)',
            r'(?:Business|Company)\s*Name[:\s]*([^\n]+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0].strip()
        return None

    def _extract_phone(self, text):
        """Extract phone number"""
        patterns = [
            r'(?:Phone|Tel)[:\s]*(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})',
            r'(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0]
        return None

    def _extract_inspection_type(self, text):
        """Extract inspection type"""
        patterns = [
            r'(?:Inspection\s*Type|Type)[:\s]*([^\n]+)',
            r'(Routine|Follow-up|Complaint|Initial|Annual)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0].strip()
        return None

    def _extract_inspector_info(self, text):
        """Extract inspector information"""
        inspector_patterns = [
            r'Inspector[:\s]*([^\n]+)',
            r'Inspected\s*by[:\s]*([^\n]+)'
        ]
        
        phone_patterns = [
            r'Inspector.*?(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})',
            r'Phone[:\s]*(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})'
        ]
        
        accepted_patterns = [
            r'Accepted\s*by[:\s]*([^\n]+)',
            r'Report\s*accepted[:\s]*([^\n]+)'
        ]
        
        inspector_name = None
        for pattern in inspector_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                inspector_name = matches[0].strip()
                break
        
        inspector_phone = None
        for pattern in phone_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                inspector_phone = matches[0]
                break
        
        accepted_by = None
        for pattern in accepted_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                accepted_by = matches[0].strip()
                break
        
        return {
            'name': inspector_name,
            'phone': inspector_phone,
            'accepted_by': accepted_by
        }

    def _extract_violations(self, text):
        """Extract all violations with complete code descriptions"""
        violations = []
        
        # Pattern for violations with code descriptions
        violation_pattern = r'(\d+\.\d+)\s*-?\s*([^\n]+?)(?:\n|\r\n?)(.*?)(?=\d+\.\d+|$)'
        matches = re.findall(violation_pattern, text, re.DOTALL | re.MULTILINE)
        
        for match in matches:
            violation_code = match[0].strip()
            violation_title = match[1].strip()
            full_text = match[2].strip()
            
            # Extract observations and code description
            observations = ""
            code_description = ""
            
            # Look for "Code Description:" or similar markers
            if "Code Description:" in full_text:
                parts = full_text.split("Code Description:", 1)
                observations = parts[0].strip()
                code_description = parts[1].strip()
            else:
                # Try to separate observations from description
                lines = full_text.split('\n')
                if len(lines) > 1:
                    observations = lines[0].strip()
                    code_description = '\n'.join(lines[1:]).strip()
                else:
                    observations = full_text
            
            # Determine if it's a major violation
            is_major = self._is_major_violation(violation_code, violation_title, observations)
            
            # Get severity score
            severity_score = self._get_violation_severity(violation_code, violation_title)
            
            violations.append({
                'violation_code': violation_code,
                'violation_title': violation_title,
                'observations': observations,
                'code_description': code_description,
                'is_major_violation': is_major,
                'corrective_actions': self._extract_corrective_actions(full_text),
                'severity_score': severity_score
            })
        
        return violations

    def _is_major_violation(self, code, title, observations):
        """Determine if violation is major based on code and content"""
        major_keywords = [
            'safety', 'health', 'chlorine', 'chemical', 'equipment failure',
            'not operational', 'broken', 'missing', 'inadequate disinfection'
        ]
        
        text_to_check = f"{title} {observations}".lower()
        return any(keyword in text_to_check for keyword in major_keywords)

    def _get_violation_severity(self, code, title):
        """Get severity score for violation (1-5 scale)"""
        safety_keywords = ['safety', 'hazard', 'danger', 'emergency']
        health_keywords = ['health', 'contamination', 'chlorine', 'chemical']
        equipment_keywords = ['equipment', 'pump', 'filter', 'broken', 'not working']
        
        text_to_check = f"{title}".lower()
        
        if any(keyword in text_to_check for keyword in safety_keywords):
            return 5.0
        elif any(keyword in text_to_check for keyword in health_keywords):
            return 4.0
        elif any(keyword in text_to_check for keyword in equipment_keywords):
            return 3.0
        else:
            return 2.0

    def _extract_corrective_actions(self, text):
        """Extract corrective actions from violation text"""
        action_patterns = [
            r'(?:Corrective\s*Action|Action\s*Required)[:\s]*([^\n]+)',
            r'(?:Must|Shall|Required)[:\s]*([^\n]+)'
        ]
        
        for pattern in action_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0].strip()
        return None

    def _extract_equipment(self, text):
        """Extract equipment information"""
        equipment = {}
        
        # Capacity
        capacity_patterns = [
            r'(?:Capacity|Gallons)[:\s]*(\d+(?:,\d+)?)\s*(?:gallons?|gal)',
            r'(\d+(?:,\d+)?)\s*(?:gallons?|gal)'
        ]
        
        for pattern in capacity_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                capacity_str = matches[0].replace(',', '')
                equipment['capacity_gallons'] = int(capacity_str)
                break
        
        # Pump GPM
        gpm_patterns = [
            r'(?:Pump|GPM)[:\s]*(\d+(?:\.\d+)?)\s*(?:gpm|GPM)',
            r'(\d+(?:\.\d+)?)\s*(?:gpm|GPM)'
        ]
        
        for pattern in gpm_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                equipment['pump_gpm'] = float(matches[0])
                break
        
        # Equipment description
        equipment_patterns = [
            r'(?:Equipment|Description)[:\s]*([^\n]+)',
            r'(?:Pump|Filter|Heater)[:\s]*([^\n]+)'
        ]
        
        descriptions = []
        for pattern in equipment_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            descriptions.extend(matches)
        
        if descriptions:
            equipment['equipment_description'] = '; '.join(descriptions)
        
        return equipment

    def _extract_water_chemistry(self, text):
        """Extract water chemistry measurements"""
        chemistry = {}
        
        # Free Chlorine
        chlorine_patterns = [
            r'(?:Free\s*Chlorine)[:\s]*(\d+(?:\.\d+)?)',
            r'Chlorine[:\s]*(\d+(?:\.\d+)?)'
        ]
        
        for pattern in chlorine_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                chemistry['free_chlorine_ppm'] = float(matches[0])
                break
        
        # pH
        ph_patterns = [
            r'pH[:\s]*(\d+(?:\.\d+)?)',
            r'(?:pH\s*Level)[:\s]*(\d+(?:\.\d+)?)'
        ]
        
        for pattern in ph_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                chemistry['ph_level'] = float(matches[0])
                break
        
        # Temperature
        temp_patterns = [
            r'(?:Temperature|Temp)[:\s]*(\d+(?:\.\d+)?)\s*(?:°F|F|degrees)',
            r'(\d+(?:\.\d+)?)\s*(?:°F|F|degrees)'
        ]
        
        for pattern in temp_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                chemistry['pool_spa_temp_f'] = float(matches[0])
                break
        
        # CYA
        cya_patterns = [
            r'(?:CYA|Cyanuric\s*Acid)[:\s]*(\d+(?:\.\d+)?)',
            r'Stabilizer[:\s]*(\d+(?:\.\d+)?)'
        ]
        
        for pattern in cya_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                chemistry['cya_ppm'] = float(matches[0])
                break
        
        # Flow Rate
        flow_patterns = [
            r'(?:Flow\s*Rate)[:\s]*(\d+(?:\.\d+)?)\s*(?:gpm|GPM)',
            r'Flow[:\s]*(\d+(?:\.\d+)?)\s*(?:gpm|GPM)'
        ]
        
        for pattern in flow_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                chemistry['flow_rate_gpm'] = float(matches[0])
                break
        
        return chemistry

    def _extract_report_notes(self, text):
        """Extract general report notes"""
        notes_patterns = [
            r'(?:Notes|Comments|Remarks)[:\s]*([^\n]+(?:\n[^\n]+)*)',
            r'(?:Additional\s*Information)[:\s]*([^\n]+(?:\n[^\n]+)*)'
        ]
        
        for pattern in notes_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0].strip()
        return None
```

### src/services/retry_service.py
```python
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
```

### src/services/search_progress_service.py
```python
import os
import time
import sqlite3
import logging
from cProfile import label
from datetime import datetime

logger = logging.getLogger(__name__)

class SearchProgressService:
    DEFAULT_ESTIMATED_DURATION = 25  # seconds
    TIMING_TABLE = "search_timings"

    def __init__(self, database_service=None):
        # ✅ Use configured DB path if available
        self.db_path = getattr(database_service, 'db_path', 'data/reports.db')
        logger.info(f"📊 Progress DB path initialized: {self.db_path}")
        self._ensure_table_exists()

    def start_search(self, search_date):
        self.search_start_time = time.time()
        self.search_date = search_date
        logger.info(f"🚀 Search started at {self.search_start_time:.2f} for {search_date}")

    def complete_search(self, result_count):
        if not hasattr(self, 'search_start_time'):
            logger.warning("⚠️ No start time recorded — cannot complete search timing.")
            return

        duration = time.time() - self.search_start_time
        logger.info(f"✅ Search complete — duration: {duration:.2f}s, results: {result_count}")
        self._save_timing_to_database(self.search_date, duration)

    def get_estimated_duration(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(f"""
                SELECT duration FROM {self.TIMING_TABLE}
                ORDER BY timestamp DESC LIMIT 10
            """)
            rows = cursor.fetchall()
            conn.close()

            durations = [r[0] for r in rows if r[0] > 0]
            if durations:
                avg = sum(durations) / len(durations)
                logger.info(f"📈 Avg estimated duration from history: {avg:.2f}s")
                return avg
            else:
                logger.info("📉 No historical data found — using default estimate.")
        except Exception as e:
            logger.warning(f"⚠️ Failed to read average duration: {e}")

        return self.DEFAULT_ESTIMATED_DURATION

    def update_search_progress(self, status, facility_count=None, percent=None):
        """Optional mid-search progress tracking (logs only — extend if needed)"""
        try:
            elapsed = time.time() - self.search_start_time if self.search_start_time else 0
            logger.info(f"📶 Progress update — {percent}%: {label} ({self.search_date})")
        except Exception as e:
            logger.warning(f"⚠️ Failed to update progress: {e}")

    def _save_timing_to_database(self, search_date, duration):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(f"""
                INSERT INTO {self.TIMING_TABLE} (search_date, duration, timestamp)
                VALUES (?, ?, ?)
            """, (search_date, duration, datetime.now()))
            conn.commit()
            conn.close()
            logger.info(f"💾 Search duration ({duration:.2f}s) saved to DB.")
        except Exception as e:
            logger.warning(f"⚠️ Failed to save duration to database: {e}")

    def _ensure_table_exists(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.TIMING_TABLE} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    search_date TEXT NOT NULL,
                    duration REAL NOT NULL,
                    timestamp TIMESTAMP NOT NULL
                )
            """)
            conn.commit()
            conn.close()
            logger.info(f"📁 Ensured table '{self.TIMING_TABLE}' exists in DB.")
        except Exception as e:
            logger.warning(f"⚠️ Failed to ensure timing table exists: {e}")

    def estimate_search_duration(self):
        """API-compatible alias for get_estimated_duration"""
        return self.get_estimated_duration()
```

### src/services/search_service.py
```python
#!/usr/bin/env python3
"""
EMD Website Search Service - Pool Scout Pro
ENHANCED DEBUG VERSION - Step-by-step result tracking
"""

import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException, StaleElementReferenceException

from core.browser import BrowserManager
from core.error_handler import ErrorHandler, with_error_handling, CommonCleanup
from core.utilities import DateUtilities, NameUtilities, ValidationUtilities
from services.database_service import DatabaseService
from services.duplicate_prevention_service import DuplicatePreventionService

try:
   from services.search_progress_service import SearchProgressService
except ImportError:
   SearchProgressService = None

class SearchService:
   def __init__(self, progress_service=None):
       self.browser_manager = BrowserManager()
       self.db_service = DatabaseService()
       self.duplicate_service = DuplicatePreventionService()
       self.progress_service = progress_service or (SearchProgressService() if SearchProgressService else None)
       self.error_handler = ErrorHandler(__name__)
       
       self.current_driver = None
       self.session_start_time = None
       self.session_timeout = 300

   def _debug_current_results(self, driver, stage_name):
       """Debug helper to show current results at each stage"""
       try:
           facility_elements = driver.find_elements(By.CSS_SELECTOR, '.flex-row')
           print(f"\n🔍 DEBUG - {stage_name}:")
           print(f"   Total results: {len(facility_elements)}")
           
           for i, element in enumerate(facility_elements[:3]):
               try:
                   name_links = element.find_elements(By.CSS_SELECTOR, 'h4.establishment-list-name a')
                   facility_name = name_links[0].text.strip() if name_links else "Unknown"
                   
                   date_text = "No date found"
                   all_text = element.text
                   date_match = re.search(r'\d{1,2}/\d{1,2}/\d{4}', all_text)
                   if date_match:
                       date_text = date_match.group()
                   
                   print(f"   [{i+1}] {facility_name} | Date: {date_text}")
                   
               except Exception as e:
                   print(f"   [{i+1}] Error reading facility: {e}")
           
           if len(facility_elements) > 3:
               print(f"   ... and {len(facility_elements) - 3} more results")
               
       except Exception as e:
           print(f"🔍 DEBUG - {stage_name}: Error reading results - {e}")

   @with_error_handling("EMD search", default_return=[])
   def search_emd_for_date(self, start_date, end_date=None, max_load_more=10):
       if end_date is None:
           end_date = start_date
       
       print(f"🚀 Starting actual EMD search for {start_date} to {end_date}")
       
       try:
           formatted_start = DateUtilities.convert_to_pacific_date(start_date)
           formatted_end = DateUtilities.convert_to_pacific_date(end_date)
           formatted_range = f"{formatted_start} to {formatted_end}"
       except ValueError as e:
           self.error_handler.log_error("Date conversion", e, {
               'start_date': start_date, 
               'end_date': end_date
           })
           return []

       print(f"🔍 Searching EMD for date range: {start_date} to {end_date} (formatted: {formatted_range})")

       driver = None
       try:
           driver = self._get_or_create_session()
           
           driver.get("https://inspections.myhealthdepartment.com/sacramento/program-rec-health")
           print("📄 Navigated to EMD page")
           
           WebDriverWait(driver, 15).until(
               EC.presence_of_element_located((By.CLASS_NAME, "alt-datePicker"))
           )
           
           # DEBUG: Show initial page load results
           self._debug_current_results(driver, "INITIAL PAGE LOAD")
           
           # Set the date filter
           self._set_date_filter(driver, formatted_start, formatted_end)
           
           time.sleep(5)
           
           # DEBUG: Show results after date filter
           self._debug_current_results(driver, "AFTER DATE FILTER")
           
           result_elements = driver.find_elements(By.CSS_SELECTOR, ".flex-row")
           print(f"🔍 Found {len(result_elements)} .flex-row elements after filtering")
           
           if not result_elements:
               print("❌ No results found for this date")
               return []
           
           self._handle_load_more_with_progress(driver, max_load_more)
           
           # DEBUG: Show final results after Load More
           self._debug_current_results(driver, "AFTER LOAD MORE")
           
           facilities = self._extract_facilities_from_page(driver, start_date)
           
           print(f"✅ Found {len(facilities)} facilities")
           
           return facilities
           
       except Exception as e:
           self.error_handler.log_error("EMD search general error", e)
           self._cleanup_current_session()
           return []

   def _get_or_create_session(self):
       self._cleanup_current_session()
       
       try:
           self.current_driver = self.browser_manager.create_driver()
           self.session_start_time = time.time()
           print("🔄 Created new browser session")
           return self.current_driver
       except Exception as e:
           self.error_handler.log_error("Browser session creation", e)
           raise

   def _set_date_filter(self, driver, start_date, end_date):
       try:
           date_range = f"{start_date} to {end_date}"

           filter_input = driver.find_element(By.CLASS_NAME, "alt-datePicker")
           
           field_type = filter_input.get_attribute("type")
           current_value = filter_input.get_attribute("value")
           print(f"🔍 DEBUG: Date field - type: '{field_type}', current: '{current_value}'")

           driver.execute_script("arguments[0].value = '';", filter_input)
           driver.execute_script("arguments[0].focus();", filter_input)
           time.sleep(1)

           driver.execute_script(f"arguments[0].value = '{date_range}';", filter_input)
           
           driver.execute_script("arguments[0].dispatchEvent(new Event('input', {bubbles: true}));", filter_input)
           driver.execute_script("arguments[0].dispatchEvent(new Event('change', {bubbles: true}));", filter_input)
           driver.execute_script("arguments[0].blur();", filter_input)

           new_value = filter_input.get_attribute("value")
           print(f"📅 Set date filter to: '{date_range}' (verified: '{new_value}')")
           
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
               
               print(f"\n🔄 Before Load More click #{load_attempts + 1}:")
               self._debug_current_results(driver, f"BEFORE LOAD MORE #{load_attempts + 1}")
               
               driver.execute_script("arguments[0].click();", load_more_button)
               load_attempts += 1
               
               print(f"🔄 Load More clicked (attempt {load_attempts}/{max_attempts})")
               
               time.sleep(5)
               
               new_facilities = driver.find_elements(By.CSS_SELECTOR, '.flex-row')
               new_count = len(new_facilities)
               
               print(f"\n📋 After Load More click #{load_attempts}:")
               print(f"   Results changed: {current_count} -> {new_count} ({new_count - current_count} new)")
               self._debug_current_results(driver, f"AFTER LOAD MORE #{load_attempts}")
               
               if new_count <= current_count:
                   print("📋 No new results loaded, stopping")
                   break
                   
           except Exception as e:
               self.error_handler.log_error("Load More", e)
               break

   def _extract_facilities_from_page(self, driver, search_date):
       facilities = []
       
       try:
           facility_elements = driver.find_elements(By.CSS_SELECTOR, '.flex-row')
           print(f"📋 Processing {len(facility_elements)} facility elements")
           
           for i, element in enumerate(facility_elements):
               try:
                   facility_data = self._extract_single_facility(driver, element, i, search_date)
                   if facility_data:
                       facilities.append(facility_data)
                       
               except Exception as e:
                   self.error_handler.log_error("Facility extraction", e)
                   continue
           
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
           
           element_text = element.text
           date_match = re.search(r'\d{1,2}/\d{1,2}/\d{4}', element_text)
           actual_date = date_match.group() if date_match else "Not found"
           
           if index < 5:
               print(f"🏢 Facility {index + 1}: '{facility_name}'")
               print(f"   Address: {cleaned_address}")
               print(f"   Actual date found: {actual_date}")
               print(f"   Search date: {search_date}")
           
           pdf_url = self._find_pdf_url_for_facility_element(element)
           
           return {
               'name': facility_name,
               'url': facility_url,
               'pdf_url': pdf_url,
               'display_address': cleaned_address,
               'inspection_date': search_date,
               'actual_date_found': actual_date,
               'index': index
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
       except Exception as e:
           self.error_handler.log_error("Manual cleanup", e)

   def cleanup_session(self):
       self.manual_cleanup_session()

   def get_shared_driver(self):
       return self.current_driver
```

### src/services/violation_severity_service.py
```python
#!/usr/bin/env python3
"""
Violation Severity Assessment Service
Assigns severity levels 1-5 based on reference table and internet research
"""

import sqlite3
import re
import logging
import requests
import time
from datetime import datetime
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class ViolationSeverityService:
    def __init__(self, db_path='data/reports.db'):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
    def assess_violation_severity(self, violation_text, violation_code=None):
        """
        Assess violation severity using reference table and internet research
        Returns: (severity_level, reasoning, matched_pattern)
        """
        # First, try to match against reference table
        severity_info = self._match_reference_table(violation_text)
        
        if severity_info:
            return severity_info
        
        # If no match, research online and assign severity
        return self._research_and_assign_severity(violation_text, violation_code)
    
    def _match_reference_table(self, violation_text):
        """Match violation against reference table patterns"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT category_number, short_phrase, severity_reasoning, finding_pattern
                FROM violation_severity_reference
                ORDER BY category_number
            """)
            
            patterns = cursor.fetchall()
            conn.close()
            
            violation_lower = violation_text.lower()
            
            for category, phrase, reasoning, pattern in patterns:
                if re.search(pattern, violation_lower, re.IGNORECASE):
                    self.logger.info(f"Matched pattern '{pattern}' -> Severity {category}")
                    return {
                        'severity_level': category,
                        'short_phrase': phrase,
                        'reasoning': reasoning,
                        'matched_pattern': pattern,
                        'source': 'reference_table'
                    }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error matching reference table: {e}")
            return None
    
    def _research_and_assign_severity(self, violation_text, violation_code=None):
        """Research violation online and assign severity using logic"""
        try:
            # Simulate web search logic (replace with actual search if needed)
            severity = self._apply_severity_logic(violation_text)
            
            # Log for future reference table updates
            self._log_unknown_violation(violation_text, violation_code, severity)
            
            return {
                'severity_level': severity,
                'short_phrase': self._generate_short_phrase(violation_text, severity),
                'reasoning': 'Assigned via automated logic - review needed',
                'matched_pattern': None,
                'source': 'automated_logic'
            }
            
        except Exception as e:
            self.logger.error(f"Error researching violation: {e}")
            return {
                'severity_level': 3,  # Default to moderate
                'short_phrase': 'Compliance Issue',
                'reasoning': 'Default assignment - manual review required',
                'matched_pattern': None,
                'source': 'default'
            }
    
    def _apply_severity_logic(self, violation_text):
        """Apply logical rules to assign severity"""
        text_lower = violation_text.lower()
        
        # Level 1: Immediate safety hazards
        safety_keywords = ['drain', 'entrapment', 'electrical', 'shock', 'emergency', 'closure']
        if any(keyword in text_lower for keyword in safety_keywords):
            return 1
            
        # Level 2: Health risks
        health_keywords = ['bacteria', 'contamination', 'fecal', 'chemical', 'illness']
        if any(keyword in text_lower for keyword in health_keywords):
            return 2
            
        # Level 3: Equipment/chemical issues (most common)
        maintenance_keywords = ['chlorine', 'ph', 'filter', 'pump', 'chemical', 'equipment']
        if any(keyword in text_lower for keyword in maintenance_keywords):
            return 3
            
        # Level 4: Documentation/administrative
        admin_keywords = ['record', 'log', 'sign', 'certificate', 'permit', 'training']
        if any(keyword in text_lower for keyword in admin_keywords):
            return 4
            
        # Level 5: Default for minor issues
        return 5
    
    def _generate_short_phrase(self, violation_text, severity):
        """Generate standardized short phrase based on severity"""
        severity_phrases = {
            1: 'Safety Hazard',
            2: 'Health Risk', 
            3: 'Equipment Issue',
            4: 'Documentation',
            5: 'Minor Issue'
        }
        return severity_phrases.get(severity, 'Compliance Issue')
    
    def _log_unknown_violation(self, violation_text, violation_code, assigned_severity):
        """Log unknown violations for future reference table updates"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create unknown violations log table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS unknown_violations_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    violation_text TEXT,
                    violation_code TEXT,
                    assigned_severity INTEGER,
                    log_date DATE DEFAULT CURRENT_DATE,
                    review_needed BOOLEAN DEFAULT TRUE
                )
            """)
            
            cursor.execute("""
                INSERT INTO unknown_violations_log 
                (violation_text, violation_code, assigned_severity)
                VALUES (?, ?, ?)
            """, (violation_text, violation_code, assigned_severity))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error logging unknown violation: {e}")
    
    def update_reference_table(self, pattern, category, phrase, description, reasoning):
        """Add new pattern to reference table"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO violation_severity_reference 
                (finding_pattern, category_number, short_phrase, description, severity_reasoning)
                VALUES (?, ?, ?, ?, ?)
            """, (pattern, category, phrase, description, reasoning))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Added new severity pattern: {pattern} -> {category}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating reference table: {e}")
            return False
    
    def get_severity_summary(self, violations_list):
        """Get severity summary for a list of violations"""
        severity_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        
        for violation in violations_list:
            severity_info = self.assess_violation_severity(
                violation.get('observations', ''),
                violation.get('violation_code')
            )
            severity_counts[severity_info['severity_level']] += 1
        
        return severity_counts

# Test function
def test_severity_service():
    service = ViolationSeverityService()
    
    test_violations = [
        "Pool operator shall maintain pH between 7.2 and 7.8",
        "Drain cover is missing from main drain",
        "Chemical storage area has safety concerns",
        "Daily log records are missing for June",
        "Minor crack in deck surface"
    ]
    
    print("\n🧪 Testing violation severity assessment:")
    for violation in test_violations:
        result = service.assess_violation_severity(violation)
        print(f"Violation: {violation[:50]}...")
        print(f"  -> Severity {result['severity_level']}: {result['short_phrase']}")
        print(f"  -> Source: {result['source']}")
        print()

if __name__ == "__main__":
    test_severity_service()
```

### src/web/app.py
```python
#!/usr/bin/env python3
"""
Flask Application with Enterprise Logging and Search Reports
"""

import os
import sys
import logging
import logging.config
import yaml
import time
import socket
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, jsonify, request, g, redirect
from werkzeug.middleware.proxy_fix import ProxyFix

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class PerformanceMiddleware:
    """Middleware to log request performance metrics"""
    def __init__(self, app):
        self.app = app
        self.logger = logging.getLogger('performance')

    def __call__(self, environ, start_response):
        start_time = time.time()

        def new_start_response(status, response_headers, exc_info=None):
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # ms
            self.logger.info({
                'timestamp': datetime.utcnow().isoformat(),
                'method': environ.get('REQUEST_METHOD'),
                'path': environ.get('PATH_INFO'),
                'status_code': status.split()[0],
                'response_time_ms': round(response_time, 2),
                'remote_addr': environ.get('REMOTE_ADDR'),
                'user_agent': environ.get('HTTP_USER_AGENT', ''),
                'content_length': environ.get('CONTENT_LENGTH', 0)
            })
            return start_response(status, response_headers, exc_info)

        return self.app(environ, new_start_response)

def setup_logging():
    """Setup enterprise logging configuration"""
    log_dir = Path('data/logs')
    log_dir.mkdir(parents=True, exist_ok=True)

    config_path = Path('config/logging_config.yaml')
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            logging.config.dictConfig(config)
    else:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
            handlers=[logging.StreamHandler(), logging.FileHandler('data/logs/pool_scout_pro.log')]
        )

    logger = logging.getLogger('pool_scout_pro')
    logger.info("🚀 Enterprise logging system initialized")
    return logger

def create_app():
    """Create and configure Flask app with enterprise features"""
    logger = logging.getLogger('pool_scout_pro')

    app = Flask(
        __name__,
        template_folder='../../templates',
        static_folder='../../templates/static'
    )
    app.config['SECRET_KEY'] = 'your-secret-key-here'

    # Reverse proxy fix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    # Performance middleware
    app.wsgi_app = PerformanceMiddleware(app.wsgi_app)

    # Request timing
    @app.before_request
    def before_request():
        g.start_time = time.time()
        logger.debug(f"🔥 REQUEST START: {request.method} {request.path}")

    @app.after_request
    def after_request(response):
        if hasattr(g, 'start_time'):
            duration = (time.time() - g.start_time) * 1000
            logger.debug(f"✅ REQUEST END: {request.method} {request.path} - {response.status_code} ({duration:.2f}ms)")
        return response

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        logging.getLogger('errors').error(f"404 Not Found: {request.path} from {request.remote_addr}")
        return jsonify({'error': 'Not found'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        logging.getLogger('errors').error(f"500 Internal Error: {request.path} - {str(error)}")
        return jsonify({'error': 'Internal server error'}), 500

    # Blueprints
    try:
        from web.routes.api_routes import api_routes
        from web.routes.downloads import bp as downloads_api

        app.register_blueprint(api_routes)
        app.register_blueprint(downloads_api)

        logger.info("✅ API routes registered successfully")
        logger.info("✅ Downloads API registered successfully")
    except Exception as e:
        logger.error(f"❌ Failed to register routes: {e}")
        raise

    # Main routes
    @app.route('/')
    def index():
        logger.info(f"📱 Index page accessed from {request.remote_addr}")
        return redirect('/search-reports')

    @app.route('/search-reports')
    def search_reports():
        logger.info(f"📋 Search reports page accessed from {request.remote_addr}")
        return render_template('search_reports.html')

    @app.route('/health')
    def health():
        health_info = {
            'status': 'healthy',
            'service': 'pool_scout_pro',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0',
            'hostname': socket.gethostname(),
            'uptime_seconds': time.time() - app.start_time if hasattr(app, 'start_time') else 0
        }
        logger.debug(f"🏥 Health check from {request.remote_addr}")
        return jsonify(health_info)

    app.start_time = time.time()
    return app
```

### src/web/routes/api_routes.py
```python
#!/usr/bin/env python3
"""
API Routes with Standardized Error Handling and Date Format Conversion
Fixed database binding issue - query parameters now match placeholders
"""

import json
import sqlite3
import sys
import os
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify

# Add the src directory to the path so we can import properly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core.error_handler import ErrorHandler, with_api_error_handling, CommonCleanup
from core.utilities import DateUtilities
from web.shared.services import (
    get_db_service, get_search_service, get_progress_service,
    get_pdf_downloader, get_duplicate_prevention_service, get_saved_status_service)

try:
    from services.violation_severity_service import ViolationSeverityService
except ImportError as e:
    print(f"⚠ ViolationSeverityService not available: {e}")
    ViolationSeverityService = None

api_routes = Blueprint('api_routes', __name__)
error_handler = ErrorHandler(__name__)


def parse_violation_data(violation_text):
    """Parse violation data with standardized error handling"""
    try:
        if not violation_text:
            return {'violations': [], 'total_violations': 0, 'major_violations': 0}

        violation_lines = [line.strip() for line in violation_text.split('\n') if line.strip()]
        violations = []
        major_count = 0

        for line in violation_lines:
            if line and not line.startswith('Total'):
                is_major = 'MAJOR' in line.upper() or 'CRITICAL' in line.upper()
                violations.append({
                    'description': line,
                    'is_major': is_major
                })
                if is_major:
                    major_count += 1

        return {
            'violations': violations,
            'total_violations': len(violations),
            'major_violations': major_count
        }
    except Exception as e:
        error_handler.log_warning("Violation parsing", f"Failed to parse violations: {e}")
        return {'violations': [], 'total_violations': 0, 'major_violations': 0}


def get_existing_reports_from_db(search_date):
    """Get existing reports with corrected date format conversion and fixed binding"""
    conn = None
    try:
        db_service = get_db_service()
        conn = sqlite3.connect(db_service.db.db_path)
        cursor = conn.cursor()

        # Fixed: Use single parameter that matches the query placeholder
        query = '''
            SELECT
                f.name as facility_name,
                f.current_operational_status,
                f.street_address,
                f.city,
                ir.permit_id,
                ir.inspection_date,
                ir.total_violations,
                ir.major_violations,
                ir.severity_score,
                ir.closure_status,
                GROUP_CONCAT(v.violation_title, '; ') as violation_details
            FROM facilities f
            LEFT JOIN inspection_reports ir ON f.id = ir.facility_id
            LEFT JOIN violations v ON ir.id = v.report_id
            WHERE ir.inspection_date = ? OR ir.inspection_date = ?
            GROUP BY f.id, ir.id
            ORDER BY f.name
        '''

        # Fixed: Pass only one parameter to match the single placeholder
        # Convert date format for database lookup
        db_date = search_date.replace("-", "/").split("/"); db_date = f"{db_date[1]}/{db_date[2]}/{db_date[0]}"
        cursor.execute(query, (search_date, db_date))
        rows = cursor.fetchall()

        facilities = []
        for row in rows:
            violation_data = parse_violation_data(row[10] or "")
            # Build display_address from components
            street = row[2] or ""
            city = row[3] or ""
            display_address = street
            if street and city:
                display_address = f"{street}, {city}"
            elif city:
                display_address = city
            
            facilities.append({
                "name": row[0],
                "operational_status": row[1] or "unknown",
                "display_address": display_address,
                "permit_id": row[4],
                "inspection_date": row[5],
                "total_violations": row[6] or 0,
                "major_violations": row[7] or 0,
                "severity_score": row[8] or 0.0,
                "closure_status": row[9] or "operational",
                "violations": violation_data["violations"],
                "saved": True,
                "pool_status": "closed" if row[9] == "closed" else "operational"
            })

        print(f"🔍 Found {len(facilities)} existing reports for date: {search_date}")
        return facilities

    except Exception as e:
        error_handler.log_error("Database query for existing reports", e, {
            'search_date': search_date,
            'query_type': 'single_date_lookup'
        })
        raise
    finally:
        CommonCleanup.close_database_connection(conn)


@api_routes.route('/api/v1/reports/search-with-duplicates', methods=['POST'])
@with_api_error_handling("EMD search with duplicates")
def search_with_duplicates():
    data = request.get_json()
    start_date = data.get('start_date') or data.get('date')
    end_date = data.get('end_date') or start_date

    if not start_date:
        return jsonify({'success': False, 'error': 'Date is required'}), 400

    try:
        # Validate date format
        datetime.strptime(start_date, '%Y-%m-%d')
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

    # Perform EMD search
    search_service = get_search_service()
    progress_service = get_progress_service()

    if progress_service:
        progress_service.start_search(start_date)

    facilities = search_service.search_emd_for_date(start_date, end_date)

    if progress_service:
        progress_service.complete_search(len(facilities))

    # Add basic saved status (simplified for now)
    for facility in facilities:
        try:
            # Determine pool status
            closure_keywords = ['closed', 'shutdown', 'suspended']
            name_lower = facility.get('name', '').lower()
            facility['pool_status'] = 'closed' if any(keyword in name_lower for keyword in closure_keywords) else 'operational'
            facility['saved'] = False  # Will be enhanced later
        except Exception as e:
            facility['pool_status'] = 'operational'
            facility['saved'] = False

    return jsonify({
        'success': True,
        'facilities': facilities,
        'total_reports': len(facilities),
        'search_date': start_date,
        'cached': False,
        'search_timestamp': datetime.now().isoformat()
    })


@api_routes.route('/api/v1/reports/download/start', methods=['POST'])
@with_api_error_handling("PDF download start")
def start_downloads():
    data = request.get_json()
    facilities = data.get('facilities', [])

    if not facilities:
        return jsonify({'success': False, 'error': 'No facilities provided'}), 400

    print(f"🔄 Starting downloads for {len(facilities)} facilities")

    # Get shared driver from search service for session continuity
    search_service = get_search_service()
    shared_driver = search_service.get_shared_driver()

    # Initialize PDF downloader with shared session
    pdf_downloader = get_pdf_downloader(shared_driver=shared_driver)

    # Download PDFs
    results = pdf_downloader.download_pdfs_from_facilities(facilities)

    return jsonify({
        'success': True,
        'started_downloads': len(facilities),
        'successful_downloads': results['successful'],
        'failed_downloads': results['failed'],
        'message': f"Download completed: {results['successful']} successful, {results['failed']} failed"
    })


@api_routes.route('/api/v1/reports/existing-for-date', methods=['POST'])
@with_api_error_handling("Get existing reports for date")
def get_existing_reports_for_date():
    data = request.get_json()
    search_date = data.get('search_date') or data.get('date')

    if not search_date:
        return jsonify({'success': False, 'error': 'Date is required'}), 400

    try:
        # Validate date format
        datetime.strptime(search_date, '%Y-%m-%d')
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

        # Use centralized SavedStatusService instead
    saved_status_service = get_saved_status_service()
    facilities = saved_status_service.get_facilities_for_date(search_date)
        return jsonify({
            'success': True,
            'facilities': facilities,
            'total_reports': len(facilities),
            'search_date': search_date
        })


@api_routes.route('/api/v1/reports/existing', methods=['POST'])
@with_api_error_handling("Check existing facilities")
def check_existing_facilities():
    data = request.get_json()
    facility_names = data.get('facility_names', [])

    if not facility_names:
        return jsonify({'success': False, 'error': 'No facility names provided'}), 400

    duplicate_service = get_duplicate_prevention_service()
    existing_status = {}

    for name in facility_names:
        try:
            existing_status[name] = duplicate_service.is_duplicate_by_name(name)  # Keep this for legacy name-based checks
        except Exception as e:
            error_handler.log_warning(
                "Facility existence check",
                f"Failed for facility {name}",
                {'error': str(e)}
            )
            existing_status[name] = False

    return jsonify({
        'success': True,
        'existing_facilities': existing_status
    })


@api_routes.route('/api/status', methods=['GET'])
@with_api_error_handling("System status check")
def get_system_status():
    try:
        db_service = get_db_service()

        # Test database connection
        conn = sqlite3.connect(db_service.db.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM facilities')
        facility_count = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM inspection_reports')
        report_count = cursor.fetchone()[0]

        conn.close()

        return jsonify({
            'success': True,
            'status': 'operational',
            'database': {
                'connected': True,
                'facilities': facility_count,
                'reports': report_count
            },
            'services': {
                'search_service': 'available',
                'pdf_downloader': 'available',
                'database_service': 'available'
            },
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        error_handler.log_error("System status check", e)
        return jsonify({
            'success': False,
            'status': 'degraded',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@api_routes.route('/api/v1/estimate', methods=['POST'])
@with_api_error_handling("Search duration estimate")
def estimate_search_duration():
    progress_service = get_progress_service()

    if not progress_service:
        return jsonify({
            'success': True,
            'estimated_duration': 25,
            'message': 'Estimate service not available, using default'
        })

    estimate = progress_service.estimate_search_duration()

    return jsonify({
        'success': True,
        'estimated_duration': estimate,
        'message': f'Estimated {estimate} seconds based on recent searches'
    })
```

### src/web/routes/downloads.py
```python
"""
Downloads API Routes - non-blocking starter
Accepts both /api/v1/downloads/start and /api/downloads/start
"""

from flask import Blueprint, request, jsonify
import threading
import logging

from services.pdf_downloader import PDFDownloader

# Note: blueprint is rooted at /api so we can define both /v1/downloads/start and /downloads/start
bp = Blueprint('downloads', __name__, url_prefix='/api')
logger = logging.getLogger('pool_scout_pro')

def _run_downloads(facilities):
    try:
        downloader = PDFDownloader()
        result = downloader.download_pdfs_from_facilities(facilities or [])
        logger.info("Download job finished: %s", {
            'successful': result.get('successful'),
            'failed': result.get('failed')
        })
    except Exception as e:
        logger.exception("Background download job crashed: %s", e)

def _start_download_impl():
    payload = request.get_json(silent=True) or {}
    facilities = payload.get('facilities') or []
    logger.info("▶️ /downloads/start called — starting background job for %d facilities", len(facilities))

    t = threading.Thread(target=_run_downloads, args=(facilities,), daemon=True)
    t.start()

    return jsonify({
        'success': True,
        'message': 'Download started',
        'started_count': len(facilities)
    }), 200

@bp.route('/v1/downloads/start', methods=['POST'])
def start_download_v1():
    return _start_download_impl()

@bp.route('/downloads/start', methods=['POST'])
def start_download_legacy():
    return _start_download_impl()
```

### src/web/shared/services.py
```python
"""
Shared Services Initialization for Pool Scout Pro
Provides centralized service instances for the web application
"""

from services.database_service import DatabaseService
from services.search_service import SearchService
from services.duplicate_prevention_service import DuplicatePreventionService
from services.violation_severity_service import ViolationSeverityService
from services.saved_status_service import SavedStatusService
from services.pdf_downloader import PDFDownloader

try:
    from services.search_progress_service import SearchProgressService
except ImportError:
    SearchProgressService = None

# Global services registry
services = {}

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

# Initialize shared instances
db_service = get_database_service()
duplicate_service = get_duplicate_service()
progress_service = get_progress_service()
search_service = get_search_service()
pdf_downloader = get_pdf_downloader()
severity_service = get_severity_service()

# Export for direct import
__all__ = [
    'db_service', 'search_service', 'progress_service', 
    'duplicate_service', 'severity_service', 'pdf_downloader',
    'get_database_service', 'get_db_service', 'get_search_service', 'get_progress_service',
    'get_duplicate_service', 'get_duplicate_prevention_service', 'get_severity_service', 'get_pdf_downloader', 'get_saved_status_service'
]
```

## Web Templates and Assets (templates/)

### templates/search_reports.html
```html
<!DOCTYPE html>
<html lang="en">
<head>
   <meta charset="UTF-8">
   <meta name="viewport" content="width=device-width, initial-scale=1.0">
   <title>Pool Scout Pro - Sacramento County Pool Inspection Reports</title>
   <meta name="description" content="Sacramento County pool inspection reports search and management system">
   <link rel="stylesheet" href="/static/css/search_reports.css">
   <script src="https://unpkg.com/lucide@latest/dist/umd/lucide.js"></script>
</head>
<body>
   <nav class="navbar-modern" role="navigation" aria-label="Main navigation">
       <div class="nav-container-modern">
           <div class="nav-brand-modern">
               <div class="brand-icon">
                   <i data-lucide="waves" class="brand-icon-svg" aria-hidden="true"></i>
               </div>
               <div class="brand-text">
                   <h1>Pool Scout Pro</h1>
                   <span class="brand-subtitle">Sacramento County</span>
               </div>
           </div>

           <ul class="nav-menu-modern" role="menubar">
               <li class="nav-item-modern" role="none">
                   <a href="/reports" class="nav-link-modern active" role="menuitem" aria-current="page">
                       <div class="nav-icon">
                           <i data-lucide="file-text" class="nav-icon-svg" aria-hidden="true"></i>
                       </div>
                       <span class="nav-text">Reports</span>
                       <div class="nav-indicator" aria-hidden="true"></div>
                   </a>
               </li>
               <li class="nav-item-modern" role="none">
                   <a href="/dashboard" class="nav-link-modern" role="menuitem">
                       <div class="nav-icon">
                           <i data-lucide="bar-chart-3" class="nav-icon-svg" aria-hidden="true"></i>
                       </div>
                       <span class="nav-text">Analytics</span>
                       <div class="nav-indicator" aria-hidden="true"></div>
                   </a>
               </li>
               <li class="nav-item-modern" role="none">
                   <a href="/business" class="nav-link-modern" role="menuitem">
                       <div class="nav-icon">
                           <i data-lucide="building-2" class="nav-icon-svg" aria-hidden="true"></i>
                       </div>
                       <span class="nav-text">Business</span>
                       <div class="nav-indicator" aria-hidden="true"></div>
                   </a>
               </li>
           </ul>

           <button class="nav-toggle-modern" aria-label="Toggle navigation menu" aria-expanded="false">
               <div class="hamburger-modern">
                   <span class="hamburger-line" aria-hidden="true"></span>
                   <span class="hamburger-line" aria-hidden="true"></span>
                   <span class="hamburger-line" aria-hidden="true"></span>
               </div>
           </button>
       </div>
   </nav>

   <main class="container" role="main">
       <!-- Sticky Search and Header Container -->
       <section class="search-and-header-container" aria-label="Search controls and results summary">
           <div class="search-controls">
               <div class="search-controls-header">
                   <div class="header-left">
                       <h2 id="search-title">Report Search</h2>
                       <div class="search-form" role="search">
                           <label for="searchDate" class="sr-only">Search date</label>
                           <input type="date" 
                                  id="searchDate" 
                                  class="form-control-refined"
                                  aria-describedby="date-help"
                                  required>
                           <span id="date-help" class="sr-only">Select inspection date to search for reports</span>
                           
                           <button id="searchButton" 
                                   class="btn btn-primary search-btn-refined"
                                   type="button"
                                   aria-describedby="search-status">
                               <i data-lucide="search" aria-hidden="true"></i>
                               <span>Search</span>
                           </button>
                           
                           <input type="hidden" id="purposeSelect" value="inspection">
                       </div>
                   </div>
               </div>

               <div class="results-summary" role="status" aria-live="polite">
                   <div class="results-left">
                       <div class="results-count" aria-label="Search results summary">
                           <span>Found:</span>
                           <span id="results-count" class="badge badge-large" aria-label="Number of facilities found">0</span>
                       </div>
                       <div class="results-count">
                           <span>On File:</span>
                           <span id="on-file-count" class="badge badge-large badge-success" aria-label="Number of reports already saved">0</span>
                       </div>
                       <div class="search-date">
                           <span>Date:</span>
                           <span id="current-search-date" aria-label="Current search date">-</span>
                       </div>
                   </div>
                   
                   <!-- Search Progress (moved inline) -->
                   <div id="progress-container" 
                        class="progress-container-inline" 
                        style="display: none;"
                        role="progressbar"
                        aria-label="Search progress"
                        aria-valuemin="0"
                        aria-valuemax="100">
                       <div class="progress-info">
                           <span id="progress-text">Searching EMD database...</span>
                       </div>
                       <div class="progress-bar-container">
                           <div id="progress-bar" class="progress-bar" style="width: 0%"></div>
                       </div>
                   </div>
               </div>

               <!-- Status Messages -->
               <div id="status-message" 
                    class="alert alert-info" 
                    style="display: none;" 
                    role="alert" 
                    aria-live="assertive"
                    aria-atomic="true">
               </div>

               <!-- Download Progress Section -->
               <div id="download-progress-container" 
                    class="download-progress-container" 
                    style="display: none;"
                    role="region"
                    aria-label="Download progress">
                   <div class="download-progress-header">
                       <h3>Download Progress</h3>
                       <div class="download-summary">
                           <span id="download-completed">0</span> of <span id="download-total">0</span> completed
                       </div>
                   </div>
                   <div id="download-progress-list" class="download-progress-list"></div>
               </div>
           </div>

           <!-- Table Header (part of sticky container) -->
           <div class="table-header-container">
               <table class="table table-header-only" role="table" aria-label="Inspection reports">
                   <thead>
                       <tr role="row">
                           <th scope="col" style="width: 60px;" id="col-number">#</th>
                           <th scope="col" id="col-facility">Facility</th>
                           <th scope="col" id="col-findings">Findings</th>
                           <th scope="col" style="width: 60px;" id="col-saved">
                               <span class="sr-only">Saved Status</span>
                               <i data-lucide="save" aria-hidden="true" title="Saved Status"></i>
                           </th>
                           <th scope="col" style="width: 60px;" id="col-pool-status">
                               <span class="sr-only">Pool Status</span>
                               <i data-lucide="droplets" aria-hidden="true" title="Pool Status"></i>
                           </th>
                       </tr>
                   </thead>
               </table>
           </div>
       </section>

       <!-- Scrolling Results Container -->
       <section class="results-container" aria-label="Search results" aria-describedby="search-title">
           <div class="table-responsive">
               <table class="table table-striped table-body-only" 
                      role="table" 
                      aria-label="Inspection reports data">
                   <tbody id="reports-table-body" role="rowgroup">
                       <tr class="no-results" role="row">
                           <td colspan="5" 
                               class="text-center text-muted"
                               headers="col-number col-facility col-findings col-saved col-pool-status">
                               <div class="no-results-content">
                                   <p>🔍 No search performed yet</p>
                                   <p class="help-text">Select a date and click Search to find inspection reports</p>
                               </div>
                           </td>
                       </tr>
                   </tbody>
               </table>
           </div>
       </section>

       <!-- Loading State -->
       <div id="loading-overlay" class="loading-overlay" style="display: none;" aria-hidden="true">
           <div class="loading-spinner">
               <div class="spinner"></div>
               <p>Loading...</p>
           </div>
       </div>
   </main>

   <footer class="page-footer" role="contentinfo">
       <div class="footer-content">
           <p>&copy; 2025 Pool Scout Pro | Sacramento County Pool Inspection Tool</p>
           <p class="footer-links">
               <a href="#" onclick="showAbout()" aria-label="About Pool Scout Pro">About</a> |
               <a href="#" onclick="showHelp()" aria-label="Help and documentation">Help</a> |
               <a href="#" onclick="showSettings()" aria-label="Application settings">Settings</a>
           </p>
       </div>
   </footer>

   <!-- Screen Reader Only Styles -->
   <style>
       .sr-only {
           position: absolute;
           width: 1px;
           height: 1px;
           padding: 0;
           margin: -1px;
           overflow: hidden;
           clip: rect(0, 0, 0, 0);
           white-space: nowrap;
           border: 0;
       }
       
       .help-text {
           font-size: 14px;
           margin-top: 8px;
           opacity: 0.7;
       }
   </style>

   <!-- Core JavaScript - Optimized Loading Order -->
   <script>
       // Initialize global namespace
       window.poolScoutPro = {
           modules: {},
           config: {
               apiBase: '/api/v1',
               pollInterval: 2000,
               maxRetries: 3
           }
       };
   </script>

   <!-- Core utilities and dependencies first -->
   <script src="/static/js/core/utilities.js"></script>
   <script src="/static/js/core/api-client.js"></script>
   <script src="/static/js/core/ui-manager.js"></script>
   <script src="/static/js/core/violation-modal.js"></script>

   <!-- Download system -->
   <script src="/static/js/downloads/download-service.js"></script>
   <script src="/static/js/downloads/download-ui.js"></script>

   <!-- Search system -->
   <script src="/static/js/search/search-service.js"></script>
   <script src="/static/js/search/search-ui.js"></script>

   <!-- Main application initialization -->
   <script src="/static/js/main.js"></script>

   <!-- Initialize Lucide icons after DOM load -->
   <script>
       document.addEventListener('DOMContentLoaded', function() {
           if (typeof lucide !== 'undefined') {
               lucide.createIcons();
           }
           
           // Initialize mobile navigation
           const navToggle = document.querySelector('.nav-toggle-modern');
           const navMenu = document.querySelector('.nav-menu-modern');
           
           if (navToggle && navMenu) {
               navToggle.addEventListener('click', function() {
                   const isExpanded = navToggle.getAttribute('aria-expanded') === 'true';
                   navToggle.setAttribute('aria-expanded', !isExpanded);
                   navMenu.style.display = isExpanded ? 'none' : 'flex';
               });
           }
       });
   </script>
</body>
</html>
```

### templates/static/css/search_reports.css
```css
/* Global Reset and Base Styles */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #ffffff;
    min-height: 100vh;
    color: #1f2937;
    line-height: 1.6;
}

/* Container */
.container {
   width: 100%;
   max-width: none;
   margin: 0;
   padding: 20px 10px;
   background: #ffffff;
}
/* Modern Navbar System */
.navbar-modern {
    background: linear-gradient(135deg, #38bdf8 0%, #0ea5e9 100%);
    box-shadow: 0 4px 12px rgba(56, 189, 248, 0.25);
    padding: 0;
    position: sticky;
    top: 0;
    z-index: 1000;
    width: 100%;
}

.nav-container-modern {
    width: 100%;
    max-width: none;
    margin: 0;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 20px;
    flex-wrap: wrap;
}

.nav-brand-modern {
    display: flex;
    align-items: center;
    gap: 12px;
    color: white;
}

.brand-icon {
    width: 48px;
    height: 48px;
    background: rgba(255, 255, 255, 0.2);
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.brand-icon-svg {
    width: 24px;
    height: 24px;
    color: white;
}

.brand-text h1 {
    font-size: 1.5rem;
    font-weight: 700;
    margin: 0;
    color: white;
}

.brand-subtitle {
    font-size: 0.875rem;
    opacity: 0.9;
    color: white;
}

.nav-menu-modern {
    display: flex;
    list-style: none;
    gap: 8px;
    margin: 0;
}

.nav-item-modern {
    position: relative;
}

.nav-link-modern {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 16px;
    border-radius: 8px;
    color: rgba(255, 255, 255, 0.8);
    text-decoration: none;
    transition: all 0.3s ease;
    font-weight: 500;
    font-size: 0.875rem;
}

.nav-link-modern:hover {
    background: rgba(255, 255, 255, 0.15);
    color: white;
    transform: translateY(-1px);
}

.nav-link-modern.active {
    background: rgba(255, 255, 255, 0.2);
    color: white;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.nav-icon {
    width: 20px;
    height: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.nav-icon-svg {
    width: 16px;
    height: 16px;
}

.nav-indicator {
    position: absolute;
    bottom: -16px;
    left: 50%;
    transform: translateX(-50%);
    width: 4px;
    height: 4px;
    background: white;
    border-radius: 50%;
    opacity: 0;
    transition: opacity 0.3s ease;
}

.nav-link-modern.active .nav-indicator {
    opacity: 1;
}

.nav-toggle-modern {
    display: none;
}

.hamburger-modern {
    display: flex;
    flex-direction: column;
    gap: 4px;
    cursor: pointer;
}

.hamburger-line {
    width: 24px;
    height: 2px;
    background: white;
    border-radius: 2px;
    transition: all 0.3s ease;
}

/* Card System */
.card {
   background: #ffffff;
   border: 1px solid rgba(56, 189, 248, 0.1);
   border-radius: 16px;
   box-shadow: 0 8px 25px rgba(56, 189, 248, 0.15);
   overflow: hidden;
   margin-bottom: 20px;
   width: 100%;
   max-width: none;
}

.card-header {
   background: #e0f2fe;
   border-bottom: 1px solid #e5e7eb;
   padding: 24px 20px;
   color: #1f2937;
   width: 100%;
   box-sizing: border-box;
   display: block;
}

.card-body {
   padding: 0;
   background: #ffffff;
   width: 100%;
   box-sizing: border-box;
}

/* Sticky Search and Header Container */
.search-and-header-container {
    position: sticky;
    top: 0;
    z-index: 100;
    background: #ffffff;
    border: 1px solid rgba(56, 189, 248, 0.1);
    border-radius: 16px 16px 0 0;
    box-shadow: 0 8px 25px rgba(56, 189, 248, 0.15);
    margin-bottom: 0;
}

.search-controls {
    background: #e0f2fe;
    border-bottom: 1px solid #e5e7eb;
    padding: 24px 20px;
    color: #1f2937;
    border-radius: 16px 16px 0 0;
}

.search-controls-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 16px;
    margin-bottom: 16px;
}

.search-controls-header h2 {
    font-size: 1.25rem;
    font-weight: 600;
    color: #1f2937;
    margin: 0;
    white-space: nowrap;
}

.search-form {
    display: flex;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
    flex: 1;
    min-width: 0;
}

.header-inline {
   display: flex;
   justify-content: space-between;
   align-items: center;
   flex-wrap: wrap;
   gap: 16px;
   width: 100%;
   box-sizing: border-box;
}

.header-left {
   display: flex;
   align-items: center;
   gap: 16px;
   flex-wrap: wrap;
   flex: 1;
   min-width: 0;
}

.header-left h3 {
   font-size: 1.25rem;
   font-weight: 600;
   color: #1f2937;
   margin: 0;
   white-space: nowrap;
}

.results-summary {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 16px;
    gap: 20px;
}

.results-left {
    display: flex;
    gap: 20px;
    flex-wrap: wrap;
}

.progress-container-inline {
    flex: 1;
    max-width: 400px;
    min-width: 200px;
    margin-left: 20px;
}

.progress-container-inline .progress-info {
    margin-bottom: 4px;
    font-size: 12px;
    color: #6b7280;
}

.progress-container-inline .progress-bar-container {
    background: #e5e7eb;
    border-radius: 4px;
    height: 6px;
    overflow: hidden;
}

.results-count {
   display: flex;
   align-items: center;
   gap: 8px;
   font-size: 14px;
   color: #6b7280;
}

.search-date {
   display: flex;
   align-items: center;
   gap: 8px;
   font-size: 14px;
   color: #6b7280;
}

/* Table Header Container (part of sticky area) */
.table-header-container {
    background: #ffffff;
    border-top: none;
    margin: 0;
    padding: 0;
}

.table-header-only {
    width: 100%;
    border-collapse: collapse;
    margin: 0;
    table-layout: fixed;
}

.table-header-only thead th {
    background: #bae6fd;
    border-top: 1px solid #7dd3fc;
    border-bottom: 2px solid #0284c7;
    padding: 16px 12px;
    text-align: left;
    font-weight: 600;
    color: #374151;
    font-size: 14px;
    white-space: nowrap;
}

/* Add to search_reports.css after the table styles */
.table-header-only,
.table-body-only {
    table-layout: fixed;
}

.table-header-only th:nth-child(1),
.table-body-only td:nth-child(1) {
    width: 60px;
}

.table-header-only th:nth-child(4),
.table-body-only td:nth-child(4) {
    width: 60px;
}

.table-header-only th:nth-child(5),
.table-body-only td:nth-child(5) {
    width: 60px;
}

/* Scrolling Results Container */
.results-container {
    background: #ffffff;
    border: 1px solid rgba(56, 189, 248, 0.1);
    border-top: none;
    border-radius: 0 0 16px 16px;
    box-shadow: 0 8px 25px rgba(56, 189, 248, 0.15);
    margin-top: 0;
    max-height: calc(100vh - 300px);
    overflow-y: auto;
}

.table-body-only {
    width: 100%;
    border-collapse: collapse;
    margin: 0;
    table-layout: fixed;
}

.table-body-only tbody td {
    padding: 16px 12px;
    border-bottom: 1px solid #e5e7eb;
    vertical-align: top;
    font-size: 14px;
}

.table-body-only tbody tr:hover {
    background: rgba(56, 189, 248, 0.05);
}

.table-body-only tbody tr:nth-child(even) {
    background: #f9fafb;
}

.table-body-only tbody tr:nth-child(even):hover {
    background: rgba(56, 189, 248, 0.08);
}

/* Form Controls */
.form-control-refined {
    display: inline-block;
    width: auto;
    padding: 8px 12px;
    font-size: 14px;
    line-height: 1.5;
    color: #495057;
    background-color: #fff;
    background-clip: padding-box;
    border: 1px solid #ced4da;
    border-radius: 6px;
    transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
}

.form-control-refined:focus {
    color: #495057;
    background-color: #fff;
    border-color: #80bdff;
    outline: 0;
    box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
}

/* Button System */
.btn {
   display: inline-flex;
   align-items: center;
   justify-content: center;
   gap: 8px;
   padding: 6px 6px;
   font-size: 12px;
   font-weight: 600;
   border-radius: 8px;
   border: none;
   cursor: pointer;
   user-select: none;
   transition: all 0.3s ease;
   white-space: nowrap;
   min-width: 120px;
   box-sizing: border-box;
   text-decoration: none;
}

.btn-primary {
   background-color: #0ea5e9;
   color: white;
   box-shadow: 0 4px 8px rgba(14, 165, 233, 0.4);
}

.btn-primary:hover:not(:disabled) {
   background-color: #0284c7;
   box-shadow: 0 6px 12px rgba(2, 132, 199, 0.5);
   transform: translateY(-1px);
}

.btn-primary:active {
   transform: scale(0.97);
}

.btn:disabled {
   opacity: 0.6;
   cursor: not-allowed;
   transform: none;
}

.search-btn-refined {
   background-color: #0ea5e9;
   color: white;
   box-shadow: 0 4px 8px rgba(14, 165, 233, 0.4);
}

.save-btn-refined {
   background-color: #10b981;
   color: white;
   box-shadow: 0 4px 8px rgba(16, 185, 129, 0.4);
}

.save-btn-refined:hover:not(:disabled) {
   background-color: #059669;
   box-shadow: 0 6px 12px rgba(5, 150, 105, 0.5);
   transform: translateY(-1px);
}

.btn i {
   width: 12px;
   height: 12px;
   flex-shrink: 0;
}
/* Badge System */
.badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 4px 8px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 600;
    line-height: 1;
}

.badge-large {
    padding: 6px 12px;
    font-size: 14px;
    border-radius: 8px;
    min-width: 32px;
}

.badge-success {
    background: #dcfce7;
    color: #166534;
    border: 1px solid #bbf7d0;
}

.badge:not(.badge-success) {
    background: #f3f4f6;
    color: #374151;
    border: 1px solid #d1d5db;
}

/* Alert System */
.alert {
    padding: 12px 16px;
    border-radius: 8px;
    margin: 12px 0;
    border: 1px solid;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.alert-info {
    background: #eff6ff;
    border-color: #3b82f6;
    color: #1e40af;
}

.alert-success {
    background: #f0fdf4;
    border-color: #06b6d4;
    color: #065f46;
}

.alert-danger {
    background: #fef2f2;
    border-color: #ef4444;
    color: #dc2626;
}

.alert-warning {
    background: #fffbeb;
    border-color: #f59e0b;
    color: #92400e;
}

/* Progress System */
.progress-container {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 16px;
    box-shadow: 0 2px 4px rgba(56, 189, 248, 0.1);
}

.progress-info {
    margin-bottom: 8px;
    font-size: 14px;
    color: #6b7280;
}

.progress-bar-container {
    background: #e5e7eb;
    border-radius: 4px;
    height: 8px;
    overflow: hidden;
}

.progress-bar {
    background: linear-gradient(90deg, #0ea5e9, #0284c7);
    height: 100%;
    border-radius: 4px;
    transition: width 0.3s ease;
    width: 0%;
}

/* Download Progress Styles */
.download-progress-container {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 16px;
    margin-top: 16px;
}

.download-progress-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
}

.download-progress-header h3 {
    font-size: 1rem;
    font-weight: 600;
    color: #1f2937;
    margin: 0;
}

.download-summary {
    font-size: 14px;
    color: #6b7280;
}

.download-progress-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
    max-height: 200px;
    overflow-y: auto;
}

.download-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 12px;
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    font-size: 13px;
}

.download-item-name {
    flex: 1;
    margin-right: 12px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.download-item-status {
    display: flex;
    align-items: center;
    gap: 8px;
}

.download-status-pending {
    color: #6b7280;
}

.download-status-downloading {
    color: #3b82f6;
}

.download-status-success {
    color: #10b981;
}

.download-status-failed {
    color: #ef4444;
}

/* Loading Overlay */
.loading-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(255, 255, 255, 0.8);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
}

.loading-spinner {
    text-align: center;
}

.spinner {
    width: 40px;
    height: 40px;
    border: 4px solid #e5e7eb;
    border-top: 4px solid #3b82f6;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 0 auto 12px;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* Table System */
.table-responsive {
    overflow-x: auto;
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(56, 189, 248, 0.15);
    background: #ffffff;
    width: 100%;
    max-width: none;
}

.table {
    width: 100%;
    border-collapse: collapse;
    background: white;
    margin: 0;
    table-layout: fixed;
}

.table-striped tbody tr:nth-child(even) {
    background: #f9fafb;
}

.table th {
    background: #e0f2fe;
    padding: 16px 12px;
    text-align: left;
    font-weight: 600;
    color: #374151;
    border-bottom: 1px solid #e5e7eb;
    font-size: 14px;
    white-space: nowrap;
}

.table td {
    padding: 16px 12px;
    border-bottom: 1px solid #e5e7eb;
    vertical-align: top;
    font-size: 14px;
}

.table tr:hover {
    background: rgba(56, 189, 248, 0.05);
}

.table tbody tr:last-child {
    border-bottom: none;
}

/* Utility Classes */
.text-center {
    text-align: center;
}

.text-muted {
    color: #6b7280;
}

.text-danger {
    color: #dc2626;
}

.mt-3 {
    margin-top: 1rem;
}

/* No Results */
.no-results td {
    padding: 40px 12px;
    text-align: center;
    color: #6b7280;
}

.no-results-content p {
    margin: 0;
    font-size: 16px;
}

/* Footer */
.page-footer {
    background: #e0f2fe;
    border-top: 1px solid #e5e7eb;
    color: #374151;
    text-align: center;
    padding: 20px;
    margin-top: 40px;
    box-shadow: 0 -2px 4px rgba(0, 0, 0, 0.05);
    width: 100%;
}

.footer-content p {
    margin: 8px 0;
    font-size: 14px;
}

.footer-links a {
    color: #0284c7;
    text-decoration: none;
    transition: color 0.3s ease;
    font-weight: 500;
}

.footer-links a:hover {
    color: #0369a1;
}

/* Animation for saved facilities */
.facility-newly-saved {
    background-color: rgba(16, 185, 129, 0.1) !important;
    transition: background-color 0.3s ease;
}

/* Responsive Design */
@media (max-width: 768px) {
    .nav-container-modern {
        flex-wrap: wrap;
    }
    
    .nav-menu-modern {
        display: none;
        width: 100%;
        flex-direction: column;
        gap: 8px;
        margin-top: 16px;
    }
    
    .nav-toggle-modern {
        display: block;
    }
    
    .search-controls {
        padding: 16px;
    }
    
    .search-controls-header {
        flex-direction: column;
        align-items: stretch;
    }
    
    .search-form {
        flex-direction: column;
        align-items: stretch;
        gap: 12px;
    }
    
    .results-summary {
        flex-direction: column;
        align-items: stretch;
        gap: 12px;
    }
    
    .results-left {
        justify-content: center;
        gap: 12px;
    }
    
    .progress-container-inline {
        margin-left: 0;
        max-width: none;
    }
    
    .results-container {
        max-height: calc(100vh - 400px);
    }
    
    .download-progress-header {
        flex-direction: column;
        align-items: stretch;
        gap: 8px;
    }
    
    .container {
        padding: 12px;
    }
}

@media (max-width: 480px) {
    .table-header-only thead th,
    .table-body-only tbody td {
        padding: 8px 6px;
        font-size: 12px;
    }
    
    .search-controls-header h2 {
        font-size: 1.1rem;
    }
    
    .btn {
        width: 100%;
        justify-content: center;
    }
    
    .results-left {
        gap: 8px;
    }
}

/* Badge color states - Pastel theme */
.badge-grey {
    background-color: #d1d5db !important; /* Light grey */
    color: #374151 !important; /* Darker text for contrast */
}

.badge-active {
    background-color: #2563eb !important;
    color: white !important;
}

.badge-empty {
    background-color: #ef4444 !important;
    color: white !important;
}

/* Mini progress bars for download progress */
.download-progress {
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.progress-bar-mini {
    width: 100%;
    height: 8px;
    background-color: #e5e7eb;
    border-radius: 4px;
    overflow: hidden;
}

.progress-fill {
    height: 100%;
    background-color: #3b82f6;
    transition: width 0.3s ease;
}

.progress-text {
    font-size: 11px;
    color: #6b7280;
    text-align: center;
}
```

### templates/static/js/core/api-client.js
```javascript
/**
 * API Client - Pool Scout Pro
 * 
 * Handles all communication with the Flask backend API.
 * Provides standardized methods for:
 * - Search requests to EMD database
 * - Download initiation and status
 * - Database queries for existing reports
 * - System status checks
 * 
 * All API calls return standardized Promise-based responses.
 */

class ApiClient {
    constructor() {
        this.baseUrl = '';
    }

    async searchWithDuplicates(startDate, endDate) {
        const response = await fetch('/api/v1/reports/search-with-duplicates', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                start_date: startDate,
                end_date: endDate
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();
    }

    async startDownload(facilities) {
        const response = await fetch('/api/v1/reports/download/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                facilities: facilities
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();
    }

    async checkExistingFacilities(facilityNames) {
        const response = await fetch('/api/v1/reports/existing', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                facilities: facilityNames
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();
    }

    async getExistingReportsForDate(date) {
        const response = await fetch('/api/v1/reports/existing-for-date', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                date: date
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();
    }

    async getSystemStatus() {
        const response = await fetch('/api/status');

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();
    }

    async getSearchEstimate() {
        const response = await fetch('/api/v1/estimate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();
    }
}

// Initialize global instance
window.apiClient = new ApiClient();
```

### templates/static/js/core/ui-manager.js
```javascript
/**
 * UI Manager - Pool Scout Pro
 * 
 * Centralized UI state management and DOM manipulation.
 * Single responsibility: Manage UI elements and their states.
 */

class UIManager {
    constructor() {
        this.elements = {
            searchButton: document.getElementById('searchButton'),
            dateInput: document.getElementById('searchDate'),
            resultsBody: document.getElementById('reports-table-body'),
            statusDiv: document.getElementById('status-message'),
            resultsCount: document.getElementById('results-count'),
            onFileCount: document.getElementById('on-file-count'),
            currentSearchDate: document.getElementById('current-search-date')
        };
    }

    showStatusMessage(message, type = 'info') {
        if (!this.elements.statusDiv) return;

        const iconMap = {
            success: 'check-circle',
            error: 'alert-circle',
            warning: 'alert-triangle',
            info: 'info'
        };

        const classMap = {
            success: 'alert alert-success',
            error: 'alert alert-danger',
            warning: 'alert alert-warning',
            info: 'alert alert-info'
        };

        const icon = iconMap[type] || 'info';
        const className = classMap[type] || 'alert alert-info';

        this.elements.statusDiv.innerHTML = `
            <div class="${className}" style="display: flex; align-items: center; gap: 8px;">
                <i data-lucide="${icon}"></i>
                <span>${this.escapeHtml(message)}</span>
            </div>
        `;
        this.elements.statusDiv.style.display = 'block';

        this.refreshIcons();
    }

    clearStatusMessage() {
        if (this.elements.statusDiv) {
            this.elements.statusDiv.innerHTML = '';
            this.elements.statusDiv.style.display = 'none';
        }
    }

    updateResultsCounts(total = 0, onFile = 0) {
        if (this.elements.resultsCount) {
            this.elements.resultsCount.textContent = total;
        }
        if (this.elements.onFileCount) {
            this.elements.onFileCount.textContent = onFile;
        }
    }

    setCurrentSearchDate(date) {
        if (this.elements.currentSearchDate) {
            this.elements.currentSearchDate.textContent = date || '-';
        }
    }

    clearResults() {
        if (this.elements.resultsBody) {
            this.elements.resultsBody.innerHTML = `
                <tr><td colspan="5" class="text-center text-muted">
                    <div class="no-results-content">
                        <p>🔍 No search performed yet</p>
                    </div>
                </td></tr>
            `;
        }
        this.updateResultsCounts(0, 0);
       this.setFoundBadgeState("pre-search"); // Grey badge on clear
        this.setCurrentSearchDate('-');
        this.clearStatusMessage();
    }

    renderSearchResults(facilities) {
        if (!this.elements.resultsBody) {
            console.error('Results table body not found');
            return;
        }

        if (!facilities || facilities.length === 0) {
            this.elements.resultsBody.innerHTML = `
                <tr><td colspan="5" class="text-center text-muted">
                    No inspection reports found for the selected date.
                </td></tr>
            `;
            // Only update Found count to 0, preserve On File count
            const currentOnFile = parseInt(this.elements.onFileCount?.textContent) || 0;
            // Count updates removed - managed by search UI
        // this.updateResultsCounts(0, currentOnFile);
            this.setFoundBadgeState("empty");
            return;
        }

        let html = '';
        facilities.forEach((facility, index) => {
            html += this.renderFacilityRow(facility, index);
        });

        this.elements.resultsBody.innerHTML = html;

        // DO NOT update counts here - this is handled by displaySearchResults
        // The counts should only be managed by the search UI, not the renderer

        const searchDate = this.elements.dateInput?.value;
        this.setCurrentSearchDate(searchDate);

        this.refreshIcons();
    }

    renderFacilityRow(facility, index) {
        const cleanAddress = this.getCleanAddress(facility.display_address);
        const escapedName = this.escapeHtml(facility.name || '');
        const escapedAddress = this.escapeHtml(cleanAddress);
        
        const topFindings = this.renderTopFindings(facility, index);
        const savedIcon = this.getSavedIcon(facility.saved);
        const statusIcon = this.getStatusIcon(facility.closure_status);
        const facilityTypeIcon = this.getFacilityTypeIcon(facility.program_identifier);

        return `
            <tr data-facility-index="${index}">
                <td style="text-align: center;">${index + 1}</td>
                <td>
                    <div style="display: flex; align-items: flex-start; gap: 8px;">
                        ${facilityTypeIcon}
                        <div style="flex: 1;">
                            <div style="font-weight: 500; color: #1f2937; line-height: 1.3;">${escapedName}</div>
                            ${escapedAddress ? `<div style="font-size: 13px; color: #6b7280; margin-top: 2px; line-height: 1.2;">${escapedAddress}</div>` : ''}
                        </div>
                    </div>
                </td>
                <td>${topFindings}</td>
                <td style="text-align: center;">${savedIcon}</td>
                <td style="text-align: center;">${statusIcon}</td>
            </tr>
        `;
    }

    getCleanAddress(address) {
        if (!address) return '';
        return address.includes(', CA') ? address.split(', CA')[0].trim() : address;
    }

    renderTopFindings(facility, index) {
        if (facility.saved && facility.violations) {
            const violations = facility.violations;
            if (violations.length === 0) {
                return '<div style="font-size: 12px; color: #059669;">✅ No violations found</div>';
            }

            const sortedViolations = violations.sort((a, b) => (b.severity_score || 0) - (a.severity_score || 0));
            const topViolations = sortedViolations.slice(0, 2);

            let findings = `<div style="font-size: 12px; cursor: pointer;" onclick="toggleFindings(${index})">`;
            findings += `<ul style="list-style-type: disc; padding-left: 16px; margin: 0;">`;

            topViolations.forEach((v, idx) => {
                let title = (v.title || 'Violation').replace(/^\d+\.\s*/, '').replace(/\nO$/, '');
                
                if (idx === 1 && violations.length > 2) {
                    findings += `<li style="margin-bottom: 4px; color: #374151;">${title} <span style="color: #6b7280; font-style: italic;">+${violations.length - 2} more...</span></li>`;
                } else {
                    findings += `<li style="margin-bottom: 4px; color: #374151;">${title}</li>`;
                }
            });

            findings += `</ul></div>`;
            return findings;
        } else if (facility.saved) {
            return '<div style="font-size: 12px; color: #6b7280;">Click to view violations</div>';
        } else {
            return '<div style="font-size: 12px; color: #6b7280;">Click Save to process...</div>';
        }
    }

    getSavedIcon(saved) {
        return saved ? 
            '<i data-lucide="check-circle" style="color: #10b981; width: 20px; height: 20px;" title="Saved"></i>' :
            '<i data-lucide="x-circle" style="color: #ef4444; width: 20px; height: 20px;" title="Not Saved"></i>';
    }

    getStatusIcon(closureStatus) {
        switch (closureStatus) {
            case 'closed':
                return '<i data-lucide="x-circle" style="color: #dc2626; width: 20px; height: 20px;" title="Closed"></i>';
            case 'operational':
                return '<i data-lucide="droplet" style="color: #2563eb; width: 20px; height: 20px;" title="Operational"></i>';
            default:
                return '<i data-lucide="help-circle" style="color: #6b7280; width: 20px; height: 20px;" title="Unknown"></i>';
        }
    }

    getFacilityTypeIcon(programIdentifier) {
        const isSpa = programIdentifier && programIdentifier.toUpperCase().includes('SPA');
        return isSpa ?
            '<i data-lucide="waves" style="color: #dc2626; width: 16px; height: 16px;" title="Spa"></i>' :
            '<i data-lucide="droplets" style="color: #2563eb; width: 16px; height: 16px;" title="Pool"></i>';
    }

    updateFacilityRow(index, facility) {
        const row = document.querySelector(`tr[data-facility-index="${index}"]`);
        if (!row) return;

        const savedCell = row.children[3];
        if (savedCell) {
            savedCell.innerHTML = this.getSavedIcon(facility.saved);
        }

        const statusCell = row.children[4];
        if (statusCell && facility.closure_status) {
            statusCell.innerHTML = this.getStatusIcon(facility.closure_status);
        }

        this.refreshIcons();

        if (facility.saved && !row.classList.contains('facility-newly-saved')) {
            row.style.backgroundColor = '#f0fdf4';
            row.classList.add('facility-newly-saved');
            setTimeout(() => {
                row.style.backgroundColor = '';
                row.classList.remove('facility-newly-saved');
            }, 4000);
        }
    }


   setFoundBadgeState(state) {
       const foundBadge = this.elements.resultsCount;
       if (!foundBadge) return;

       // Remove existing state classes
       foundBadge.classList.remove("badge-grey", "badge-active", "badge-empty");

       switch (state) {
           case "pre-search":
               foundBadge.classList.add("badge-grey");
               break;
           case "active":
               foundBadge.classList.add("badge-active");
               break;
           case "empty":
               foundBadge.classList.add("badge-empty");
               break;
       }
   }

    refreshIcons() {
        if (window.lucide) {
            window.lucide.createIcons();
        }
    }

    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, function(m) { return map[m]; });
    }

    setSaveButtonProcessing(isProcessing) {
        const saveButton = document.querySelector("#saveButton, .save-btn, .btn-save");
        if (saveButton) {
            if (isProcessing) {
                saveButton.disabled = true;
                saveButton.textContent = "Saving PDFs...";
                saveButton.classList.add("processing");
            } else {
                saveButton.disabled = false;
                saveButton.textContent = "Save PDFs";
                saveButton.classList.remove("processing");
            }
        }
    }
}

// Global UI manager instance
window.uiManager = new UIManager();
```

### templates/static/js/core/utilities.js
```javascript
/**
 * Utilities - Pool Scout Pro
 * 
 * Common utility functions used across the application.
 * Includes:
 * - Date validation and formatting
 * - Text normalization for comparisons
 * - General helper functions
 * - Constants and configuration values
 * 
 * These utilities are pure functions with no side effects.
 */

class Utilities {
    static isValidDate(dateString) {
        if (!dateString) return false;

        // Check YYYY-MM-DD format
        const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
        if (!dateRegex.test(dateString)) return false;

        // Check if it's a valid date
        const date = new Date(dateString);
        return date instanceof Date && !isNaN(date) && dateString === date.toISOString().split('T')[0];
    }

    static getTodayDate() {
        const today = new Date();
        const year = today.getFullYear();
        const month = String(today.getMonth() + 1).padStart(2, '0');
        const day = String(today.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    static normalizeName(name) {
        return name.toLowerCase().trim().replace(/\s+/g, ' ');
    }

    static debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    static formatTimestamp() {
        return new Date().toISOString();
    }

    static sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Global utilities
window.utils = Utilities;
```

### templates/static/js/core/violation-modal.js
```javascript
/**
 * Violation Modal - Pool Scout Pro
 * 
 * Handles violation detail modal dialogs.
 * Shows detailed violation information in popup overlays when users click on violation summaries.
 */

class ViolationModal {
    show(facilityIndex) {
        const currentResults = window.searchService.getCurrentResults();
        const facility = currentResults[facilityIndex];
        
        if (!facility || !facility.violations) return;

        const existingModal = document.getElementById('findings-modal');
        if (existingModal) {
            existingModal.remove();
            return;
        }

        const violations = facility.violations;
        let modalHtml = `
            <div id="findings-modal" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 1000; display: flex; align-items: center; justify-content: center;">
                <div style="background: white; border-radius: 12px; max-width: 800px; max-height: 80vh; overflow-y: auto; margin: 20px; box-shadow: 0 8px 32px rgba(0,0,0,0.3);">
                    <div style="padding: 20px; border-bottom: 1px solid #e5e7eb; display: flex; justify-content: space-between; align-items: center;">
                        <h3 style="margin: 0; color: #1f2937;">${facility.name} - Violations</h3>
                        <button onclick="document.getElementById('findings-modal').remove()" style="border: none; background: none; font-size: 24px; color: #6b7280; cursor: pointer;">&times;</button>
                    </div>
                    <div style="padding: 20px;">
                        <ul style="list-style-type: disc; padding-left: 20px; margin: 0;">`;

        violations.forEach((violation) => {
            let title = violation.title || 'Violation';
            title = title.replace(/^\d+\.\s*/, '').replace(/\nO$/, '');
            modalHtml += `
                <li style="margin-bottom: 12px; color: #374151;">
                    <div style="font-weight: 500; margin-bottom: 4px;">${title}</div>
                    ${violation.observations ? `<div style="font-size: 14px; color: #6b7280;">${violation.observations}</div>` : ''}
                </li>`;
        });

        modalHtml += `</ul></div></div></div>`;
        document.body.insertAdjacentHTML('beforeend', modalHtml);
    }
}

window.violationModal = new ViolationModal();
```

### templates/static/js/downloads/download-service.js
```javascript
/**
 * Download Service - Pool Scout Pro
 *
 * Handles PDF download functionality.
 * Responsibilities:
 * - Initiating download requests to backend
 * - Managing download state
 * - Coordinating with download poller for progress
 * - Error handling for download operations
 *
 * Works with DownloadUI and DownloadPoller for complete download experience.
 */
class DownloadService {
    constructor() {
        this.isDownloading = false;
    }

    async startDownload(facilities) {
        if (this.isDownloading) {
            console.log('Download already in progress, ignoring click');
            window.uiManager?.showStatusMessage('Download already in progress.', 'info');
            return;
        }

        const unsavedFacilities = facilities.filter(f => !f.saved);
        if (unsavedFacilities.length === 0) {
            const msg = 'All facilities are already saved.';
            window.uiManager?.showStatusMessage(msg, 'info');
            throw new Error(msg);
        }

        this.isDownloading = true;
        window.uiManager?.setSaveButtonProcessing(true);

        try {
            window.uiManager?.showStatusMessage('Starting download...', 'info');

            const data = await window.apiClient.startDownload(unsavedFacilities);

            // Backend returns { success:false, code:'ALREADY_RUNNING', message:'...' } if lock is held
            if (data && data.success === false && data.code === 'ALREADY_RUNNING') {
                window.uiManager?.showStatusMessage(data.message || 'A download is already in progress.', 'info');
                return data;
            }

            if (data?.success) {
                window.uiManager?.showStatusMessage('Download in progress! Watch for real-time updates below.', 'success');
                if (window.downloadPoller) {
                    window.downloadPoller.startPolling(window.searchService.getCurrentResults());
                }
                return data;
            } else {
                const emsg = (data && data.message) ? data.message : 'Download failed';
                throw new Error(emsg);
            }
        } catch (error) {
            console.error('Download error:', error);
            let errorMessage = 'Download failed. Please try again.';
            if (error?.message) errorMessage = `Download failed: ${error.message}`;
            window.uiManager?.showStatusMessage(errorMessage, 'error');
            window.downloadPoller?.stopPolling();
            throw error;
        } finally {
            this.isDownloading = false;
            window.uiManager?.setSaveButtonProcessing(false);
        }
    }

    getDownloadState() {
        return { isDownloading: this.isDownloading };
    }
}

window.downloadService = new DownloadService();
```

### templates/static/js/downloads/download-ui.js
```javascript
/**
 * Download UI - Pool Scout Pro
 * 
 * Manages the download user interface and interactions.
 * Note: Save button handling is now managed by SearchUI for single dynamic button
 */
class DownloadUI {
    constructor() {
        // No longer setting up separate event listeners
        // Button handling is managed by SearchUI
    }

    async handleSaveClick() {
        try {
            const currentResults = window.searchService.getCurrentResults();
            await window.downloadService.startDownload(currentResults);
        } catch (error) {
            console.error('Save click error:', error);
        }
    }
}

window.downloadUI = null;
```

### templates/static/js/search/search-service.js
```javascript
/**
 * Search Service - Pool Scout Pro
 * 
 * Handles search API calls to the Flask backend.
 * The actual EMD automation happens in Python - this just makes the API requests.
 */

class SearchService {
    constructor() {
        this.isSearching = false;
        this.currentResults = [];
        this.dateChangeTimeout = null;
    }

    async searchForReports(date) {
        if (this.isSearching) {
            console.log('Search already in progress, aborting');
            return;
        }

        this.isSearching = true;

        try {
            const response = await fetch('/api/v1/reports/search-with-duplicates', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    start_date: date,
                    end_date: date
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            if (data.success) {
                this.currentResults = data.facilities || [];
                return data;
            } else {
                throw new Error(data.message || 'Search failed');
            }

        } finally {
            this.isSearching = false;
        }
    }

    async loadExistingReportsForDate(date) {
        try {

            const response = await fetch('/api/v1/reports/existing-for-date', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    date: date
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            if (data.success && data.facilities && data.facilities.length > 0) {
                console.log('📊 Found', data.facilities.length, 'existing reports in database');

                data.facilities.forEach(facility => {
                    facility.saved = true;
                });

                this.currentResults = data.facilities;
                return data;
            } else {
                this.currentResults = [];
                return { success: true, facilities: [] };
            }

        } catch (error) {
            console.error('❌ Error loading existing reports:', error);
            this.currentResults = [];
            throw error;
        }
    }

    handleDateChange = () => {
        if (this.dateChangeTimeout) {
            clearTimeout(this.dateChangeTimeout);
        }

        this.dateChangeTimeout = setTimeout(() => {

            const dateInput = window.uiManager.elements.dateInput;
            if (!dateInput || !dateInput.value) {
                if (window.searchUI) {
                    window.searchUI.clearResults();
                }
                return;
            }

            if (!window.utils.isValidDate(dateInput.value)) {
                window.uiManager.showStatusMessage('Please enter a valid date in YYYY-MM-DD format.', 'error');
                if (window.searchUI) {
                    window.searchUI.clearResults();
                }
                return;
            }

            console.log('📅 Date changed to:', dateInput.value, '- Loading existing reports...');

            if (window.searchUI) {
                window.searchUI.loadExistingReportsForDate(dateInput.value);
            }

        }, 300);
    }

    getCurrentResults() {
        return this.currentResults;
    }

    updateCurrentResults(newResults) {
        this.currentResults = newResults;
    }
}

window.searchService = new SearchService();
```

### templates/static/js/search/search-ui.js
```javascript
/**
* Search UI - Pool Scout Pro
*
* Manages the search user interface and interactions.
* Handles progress bar animation and button state management.
*/

class SearchUI {
   constructor() {
       this.progressTimer = null;
       this.progressStartTime = null;
       this.estimatedDuration = 25;
       this.hasSearchResults = false;
       this.isSaveInProgress = false;

       this.setupEventListeners();
       this.initializePage();
   }

   setupEventListeners() {
       const button = document.getElementById('searchButton');
       if (button) {
           button.addEventListener('click', () => {
               if (button.textContent.trim() === 'Save') {
                   this.handleSaveClick();
               } else {
                   this.handleSearchClick();
               }
           });
       }

       const dateInput = document.getElementById('searchDate');
       if (dateInput) {
           dateInput.addEventListener('change', () => {
               this.resetButtonToSearch();
               window.searchService.handleDateChange();
           });
       }
   }

   initializePage() {
       const dateInput = document.getElementById('searchDate');
       if (!dateInput) return;

       const todayStr = window.utils.getTodayDate();
       dateInput.value = todayStr;

       this.resetButtonToSearch();

       setTimeout(() => {
           this.loadExistingReportsForDate(todayStr);
       }, 400);
   }

   setButtonDisabled(disabled) {
       const button = document.getElementById('searchButton');
       if (!button) return;
       
       button.disabled = disabled;
       if (disabled) {
           button.style.opacity = '0.6';
           button.style.cursor = 'not-allowed';
       } else {
           button.style.opacity = '1';
           button.style.cursor = 'pointer';
       }
   }

   resetButtonToSearch() {
       const button = document.getElementById('searchButton');
       if (!button) return;

       button.innerHTML = '<i data-lucide="search"></i> Search';
       button.className = 'btn btn-primary search-btn-refined';
       this.hasSearchResults = false;
       this.isSaveInProgress = false;
       this.setButtonDisabled(false);

       if (typeof lucide !== 'undefined') {
           lucide.createIcons();
       }
   }

   setButtonToSave() {
       const button = document.getElementById('searchButton');
       if (!button) return;

       button.innerHTML = '<i data-lucide="download"></i> Save';
       button.className = 'btn save-btn-refined';
       this.hasSearchResults = true;
       this.setButtonDisabled(false);

       if (typeof lucide !== 'undefined') {
           lucide.createIcons();
       }
   }

   async handleSearchClick() {
       try {
           // Disable button during search
           this.setButtonDisabled(true);

           const dateInput = document.getElementById('searchDate');
           if (!dateInput || !dateInput.value) {
               window.uiManager.showStatusMessage('Please select a date first.', 'error');
               return;
           }

           if (!window.utils.isValidDate(dateInput.value)) {
               window.uiManager.showStatusMessage('Please enter a valid date in YYYY-MM-DD format.', 'error');
               return;
           }

           const estimatedDuration = await this.getEstimatedDuration();
           this.estimatedDuration = estimatedDuration;

           this.showProgressBar();

           const animationDone = new Promise((resolve) => {
               this.animateTo95Percent(estimatedDuration, resolve);
           });

           const searchPromise = window.searchService.searchForReports(dateInput.value);

           const [data] = await Promise.all([searchPromise, animationDone]);

           this.completeProgressBar();
           this.displaySearchResults(data);

           if (data && data.facilities && data.facilities.length > 0) {
               this.setButtonToSave();
           }

       } catch (error) {
           console.error('Search error:', error);
           this.hideProgressBar();
           this.resetButtonToSearch();
           window.uiManager.showStatusMessage('Search failed. Please try again.', 'error');
       } finally {
           this.setButtonDisabled(false);
       }
   }

   async handleSaveClick() {
       if (this.isSaveInProgress) {
           console.debug('Save already in progress, ignoring click.');
           window.uiManager.showStatusMessage('Save already in progress.', 'info');
           return;
       }
       this.isSaveInProgress = true;

       try {
           // Disable button during save
           this.setButtonDisabled(true);

           const currentResults = window.searchService.getCurrentResults();

           if (!currentResults || currentResults.length === 0) {
               window.uiManager.showStatusMessage('No search results to save. Please search first.', 'error');
               this.isSaveInProgress = false;
               return;
           }

           await window.downloadService.startDownload(currentResults);
       } catch (error) {
           console.error('Save error:', error);
           window.uiManager.showStatusMessage(`Save failed: ${error.message}`, 'error');
       } finally {
           this.isSaveInProgress = false;
           this.setButtonDisabled(false);
       }
   }

   async getEstimatedDuration() {
       try {
           const response = await fetch('/api/v1/estimate', { method: 'POST' });
           if (response.ok) {
               const data = await response.json();
               return data.estimated_duration || 25;
           }
       } catch (error) {
           console.warn('Failed to fetch duration estimate. Using default.');
       }
       return 25;
   }

   async loadExistingReportsForDate(date) {
       try {
           const data = await window.searchService.loadExistingReportsForDate(date);

           if (data && data.facilities && data.facilities.length > 0) {
               // Show saved files: Found=0 (no search yet), On File=saved count
               window.uiManager.renderSearchResults(data.facilities);
               window.uiManager.updateResultsCounts(0, data.facilities.length);
               window.uiManager.setFoundBadgeState('pre-search');
               
               window.searchService.updateCurrentResults(data.facilities);
               this.resetButtonToSearch();
               
               console.log(`📁 Loaded ${data.facilities.length} existing reports for ${date}`);
           } else {
               // No saved files - clear everything
               window.uiManager.clearResults();
               this.resetButtonToSearch();
               console.log(`📁 No existing reports for ${date}`);
           }

           window.uiManager.setCurrentSearchDate(date);

       } catch (error) {
           console.error('Failed to load existing reports:', error);
           this.clearResults();
           this.resetButtonToSearch();
       }
   }

   displaySearchResults(data) {
       const results = data.facilities || [];
       
       // Get counts from backend response and current UI
       const foundCount = results.length;
       const savedInSearchResults = data.saved_count || 0;
       const currentOnFileFromUI = parseInt(document.getElementById("on-file-count")?.textContent) || 0;
       
       // Use the maximum of current UI count and search results saved count
       // This handles both existing saved files and newly found saved files
       const finalOnFileCount = Math.max(currentOnFileFromUI, savedInSearchResults);
       
       console.log(`📊 Count Logic: Found=${foundCount}, SavedInSearch=${savedInSearchResults}, CurrentOnFile=${currentOnFileFromUI}, Final=${finalOnFileCount}`);
       
       // Update counts with proper logic
       window.uiManager.updateResultsCounts(foundCount, finalOnFileCount);
       
       // Set badge state based on search results
       window.uiManager.setFoundBadgeState(foundCount > 0 ? 'active' : 'empty');
       
       // Render the actual results in table (this no longer updates counts)
       window.uiManager.renderSearchResults(results);
   }

   clearResults() {
       window.uiManager.clearResults();
       window.searchService.updateCurrentResults([]);
       this.resetButtonToSearch();
   }

   showProgressBar() {
       const container = document.getElementById('progress-container');
       const text = document.getElementById('progress-text');
       const bar = document.getElementById('progress-bar');

       if (!container || !text || !bar) {
           console.error('Progress bar elements missing');
           return;
       }

       container.style.display = 'block';
       text.textContent = 'Starting search...';
       bar.style.width = '5%';
       bar.style.transition = 'width 0.3s ease-out';
   }

   animateTo95Percent(duration, doneCallback) {
       this.stopProgressAnimation();
       this.progressStartTime = Date.now();

       const progressBar = document.getElementById('progress-bar');
       const progressText = document.getElementById('progress-text');

       const animate = () => {
           const elapsed = (Date.now() - this.progressStartTime) / 1000;
           const percent = Math.min(95, 5 + (elapsed / duration) * 90);

           if (progressBar) progressBar.style.width = `${percent}%`;
           if (progressText) progressText.textContent = `Searching... ${Math.round(percent)}%`;

           if (percent < 95) {
               this.progressTimer = setTimeout(animate, 200);
           } else {
               doneCallback();
           }
       };

       animate();
   }

   completeProgressBar() {
       const bar = document.getElementById('progress-bar');
       const text = document.getElementById('progress-text');
       if (bar) bar.style.width = '100%';
       if (text) text.textContent = 'Search completed!';

       setTimeout(() => this.hideProgressBar(), 1500);
   }

   stopProgressAnimation() {
       if (this.progressTimer) {
           clearTimeout(this.progressTimer);
           this.progressTimer = null;
       }
   }

   hideProgressBar() {
       this.stopProgressAnimation();

       const container = document.getElementById('progress-container');
       const text = document.getElementById('progress-text');
       const bar = document.getElementById('progress-bar');

       if (!container || !bar || !text) return;

       container.style.display = 'none';
       text.textContent = '';
       bar.style.width = '0%';
   }
}

// Global function for button handling
function handleMainAction() {
   if (!window.searchUI) {
       alert('UI not ready. Please wait.');
       return;
   }

   const button = document.getElementById('searchButton');
   if (button && button.textContent.trim() === 'Save') {
       window.searchUI.handleSaveClick();
   } else {
       window.searchUI.handleSearchClick();
   }
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
   if (window.searchUI) {
       window.searchUI.stopProgressAnimation();
   }
});

// Export for global access
window.handleMainAction = handleMainAction;
```

### templates/static/js/main.js
```javascript
/**
 * Pool Scout Pro - Main Application Coordinator
 * 
 * Single responsibility: Initialize services and coordinate application startup.
 * Clean separation from business logic - delegates to service classes.
 */

let appInitialized = false;

/**
 * Initialize all application services in correct dependency order
 */
function initializeApplication() {
    try {
        console.log('Initializing Pool Scout Pro services...');

        // Initialize core UI services
        if (!window.searchUI) {
            window.searchUI = new SearchUI();
        }

        if (!window.downloadUI) {
            window.downloadUI = new DownloadUI();
        }

        // Initialize icons
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }

        appInitialized = true;
        console.log('Pool Scout Pro initialized successfully');

    } catch (error) {
        console.error('Initialization error:', error);
        if (window.uiManager) {
            window.uiManager.showStatusMessage('Application failed to initialize. Please refresh.', 'error');
        }
    }
}

/**
 * Clean up resources when page unloads
 */
function cleanup() {
    console.log('Cleaning up application resources...');
    
    // Stop any running timers/animations
    if (window.searchUI) {
        window.searchUI.stopProgressAnimation();
    }

    // Additional cleanup can be added here as needed
    console.log('Cleanup completed');
}

/**
 * Handle page visibility changes for performance optimization
 */
function handleVisibilityChange() {
    if (document.hidden) {
        console.log('Page hidden - reducing activity');
        // Could pause non-critical operations here
    } else {
        console.log('Page visible - resuming normal operation');
        // Could resume operations here
    }
}

// Event Listeners
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded - preparing application...');
    
    // Small delay to ensure all DOM elements are ready
    setTimeout(initializeApplication, 150);
});

window.addEventListener('beforeunload', cleanup);
document.addEventListener('visibilitychange', handleVisibilityChange);

// Global application state accessor
window.poolScoutPro = {
    isInitialized: () => appInitialized,
    version: '1.0',
    cleanup: cleanup
};

// Legacy function stubs for HTML onclick handlers
function showAbout() {
    alert('Pool Scout Pro - Sacramento County Pool Inspection Tool\nVersion 1.0');
}

function showHelp() {
    alert('Help:\n1. Select a date\n2. Click Search\n3. Watch progress bar\n4. Click Save to download reports');
}

function showSettings() {
    alert('Settings coming soon...');
}

function toggleFindings(facilityIndex) {
    if (window.violationModal) {
        window.violationModal.show(facilityIndex);
    }
}
```


---
## Generation Complete

This document contains all source code from the Pool Scout Pro project's src/ and templates/ directories as specified in the milestone document.

**File Count Summary:**
- Python Core: 5 files (browser.py, database.py, error_handler.py, settings.py, utilities.py)
- Python Services: 10 files (database_service.py through violation_severity_service.py)
- Flask Web: 4 files (app.py, routes/, shared/services.py)
- Templates: 1 HTML file (search_reports.html)
- CSS: 1 file (search_reports.css)
- JavaScript: 9 files (core/, downloads/, search/, main.js)

**Total: 30 project files**

Generated from milestone-verified project structure.
