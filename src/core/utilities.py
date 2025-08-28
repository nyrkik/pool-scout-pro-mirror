#!/usr/bin/env python3
"""
Core Utilities - Pool Scout Pro
Centralized utility functions for date handling, name processing, validation, and file operations
"""

import re
import os
import pytz
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict

class DateUtilities:
    """Date handling and conversion utilities"""
    
    @staticmethod
    def convert_to_pacific_date(date_str: str) -> str:
        """Convert date string to Pacific timezone format for EMD website (MM/DD/YYYY)"""
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            pacific = pytz.timezone('US/Pacific')
            pacific_date = pacific.localize(date_obj)
            return pacific_date.strftime('%m/%d/%Y')
        except ValueError as e:
            raise ValueError(f"Invalid date format. Expected YYYY-MM-DD, got: {date_str}") from e
    
    @staticmethod
    def normalize_date_format(date_str: str) -> Optional[str]:
        """Converts common date formats to the standard 'YYYY-MM-DD'."""
        if not date_str: return None
        try:
            if '/' in date_str:
                date_obj = datetime.strptime(date_str, '%m/%d/%Y')
                return date_obj.strftime('%Y-%m-%d')
            if '-' in date_str and len(date_str) == 10:
                datetime.strptime(date_str, '%Y-%m-%d')
                return date_str
            return None
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def extract_date_from_filename(filename: str) -> Optional[str]:
        """Extract date from filename and return in YYYY-MM-DD format."""
        try:
            match = re.search(r'^(\d{8})_', filename)
            if match:
                date_obj = datetime.strptime(match.group(1), '%Y%m%d')
                return date_obj.strftime('%Y-%m-%d')
            return None
        except Exception:
            return None
    
    @staticmethod
    def format_filename_date(date_str: str) -> str:
        """Convert date to YYYYMMDD format for filenames"""
        try:
            if '/' in date_str:
                date_obj = datetime.strptime(date_str, '%m/%d/%Y')
                return date_obj.strftime('%Y%m%d')
            if '-' in date_str:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                return date_obj.strftime('%Y%m%d')
            return date_str
        except Exception:
            return date_str

class NameUtilities:
    @staticmethod
    def clean_address_string(address: str) -> str:
        if not address: return "Unknown"
        cleaned = re.sub(r'\s+', ' ', address.strip())
        for artifact in ['Facility Address:', 'Address:', 'Located at:', 'Facility City', 'Facility ZIP']:
            cleaned = cleaned.replace(artifact, '').strip()
        cleaned = re.sub(r'^[,\s]+|[,\s]+$', '', cleaned)
        return cleaned if cleaned else "Unknown"
    @staticmethod
    def generate_filename_safe_name(name: str, max_length: int = 25) -> str:
        if not name: return "UNKNOWN"
        safe_name = re.sub(r'[^\w]', '', name.upper().replace(' ', ''))
        if len(safe_name) > max_length: safe_name = safe_name[:max_length]
        return safe_name if safe_name else "UNKNOWN"

class ValidationUtilities:
    """Validation utilities for various data types"""
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Validate URL format"""
        if not url:
            return False
        url_pattern = re.compile(
            r'^https?://'
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
            r'localhost|'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            r'(?::\d+)?'
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return url_pattern.match(url) is not None
    
    @staticmethod
    def is_valid_date(date_str: str) -> bool:
        """Validate date string in YYYY-MM-DD format"""
        if not date_str: return False
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError: return False

class TextUtilities:
    @staticmethod
    def extract_inspection_id_from_url(url: str) -> Optional[str]:
        if not url: return None
        match = re.search(r"inspectionID=([A-F0-9\-]{36})", url, re.IGNORECASE)
        return match.group(1) if match else None

class FileUtilities:
    """File operations and validation utilities"""

    @staticmethod
    def is_pdf_file(file_path: str) -> bool:
        """Check if file is a PDF based on extension"""
        return file_path.lower().endswith('.pdf')

    @staticmethod
    def get_file_size_mb(file_path: str) -> float:
        """Get file size in megabytes"""
        try:
            size_bytes = os.path.getsize(file_path)
            return size_bytes / (1024 * 1024)
        except (OSError, FileNotFoundError):
            return 0.0

    @staticmethod
    def generate_inspection_filename(facility_name: str, inspection_id: Optional[str], inspection_date: str) -> str:
        """Generate standardized filename for inspection PDFs"""
        safe_name = NameUtilities.generate_filename_safe_name(facility_name)
        formatted_date = DateUtilities.format_filename_date(inspection_date)
        short_id = "UNKNOWN"
        if inspection_id:
            if len(inspection_id) == 36 and inspection_id.count('-') == 4:
                short_id = inspection_id.split('-')[-1]
            else:
                short_id = inspection_id
        return f"{formatted_date}_{safe_name}_{short_id}.pdf"

    @staticmethod
    def ensure_directory_exists(directory_path: str) -> bool:
        """Ensure directory exists, create if necessary"""
        try:
            Path(directory_path).mkdir(parents=True, exist_ok=True)
            return True
        except Exception:
            return False

    @staticmethod
    def validate_pdf_content(file_path: str) -> bool:
        """Validate that file contains PDF content"""
        try:
            with open(file_path, 'rb') as f:
                header = f.read(8)
                return header.startswith(b'%PDF')
        except Exception:
            return False

    @staticmethod
    def clean_filename(filename: str) -> str:
        """Clean filename to remove invalid characters"""
        if not filename:
            return "unknown"
        cleaned = re.sub(r'[<>:"/\\|?*]', '', filename)
        cleaned = cleaned.replace(' ', '_')
        cleaned = re.sub(r'_+', '_', cleaned)
        cleaned = cleaned.strip('_')
        return cleaned if cleaned else "unknown"
