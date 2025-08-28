#!/usr/bin/env python3
"""
Standardized Error Handling for Pool Scout Pro
Provides consistent logging, error responses, and resource cleanup
ENHANCED: Proper logging configuration with stdout and file handlers
"""

import logging
import logging.handlers
import os
import traceback
from functools import wraps
from typing import Dict, Any, Optional, Callable

class ErrorHandler:
    """Centralized error handling with consistent patterns"""
    
    def __init__(self, logger_name: str = __name__):
        self.logger = self._setup_logger(logger_name)
    
    def _setup_logger(self, logger_name: str) -> logging.Logger:
        """Configure logger with stdout and file handlers"""
        logger = logging.getLogger(logger_name)
        
        # Prevent duplicate handlers if already configured
        if logger.handlers:
            return logger
            
        logger.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Add stdout handler for systemd/journalctl
        stdout_handler = logging.StreamHandler()
        stdout_handler.setLevel(logging.INFO)
        stdout_handler.setFormatter(formatter)
        logger.addHandler(stdout_handler)
        
        # Add file handler if possible
        try:
            # Create logs directory
            os.makedirs('data/logs', exist_ok=True)
            
            # Add rotating file handler
            file_handler = logging.handlers.RotatingFileHandler(
                'data/logs/pool_scout_pro.log',
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            # If file logging fails, continue with stdout only
            print(f"⚠️ Could not setup file logging: {e}")
        
        return logger
    
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
    
    def log_info(self, operation: str, message: str, context: Dict[str, Any] = None):
        """Standardized info logging for operational tracking"""
        context_str = f" | Context: {context}" if context else ""
        info_msg = f"ℹ️ {operation}: {message}{context_str}"
        
        self.logger.info(info_msg)
        # Note: No print() here to avoid console spam - this is for log files/systemd
    
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
