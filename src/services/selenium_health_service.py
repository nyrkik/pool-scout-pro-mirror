#!/usr/bin/env python3
"""
Selenium Health Service - Pool Scout Pro
Monitors Selenium container health and provides recovery capabilities
"""

import time
import requests
import subprocess
from typing import Dict, Any, Optional
from core.error_handler import ErrorHandler

class SeleniumHealthService:
    """Service for monitoring and maintaining Selenium container health"""
    
    def __init__(self):
        self.error_handler = ErrorHandler(__name__)
        self.selenium_url = "http://localhost:4444"
        self.container_name = "selenium-firefox"
        self.health_check_timeout = 10
        self.max_restart_attempts = 3
    
    def check_selenium_health(self) -> bool:
        """Check if Selenium is healthy and ready"""
        try:
            response = requests.get(f"{self.selenium_url}/status", timeout=self.health_check_timeout)
            
            if response.status_code == 200:
                status_data = response.json()
                is_ready = status_data.get('value', {}).get('ready', False)
                
                if is_ready:
                    self.error_handler.log_info("Selenium Health Check", "Selenium container healthy and ready")
                    return True
                else:
                    self.error_handler.log_warning("Selenium Health Check", "Selenium responding but not ready")
                    return False
            else:
                self.error_handler.log_warning("Selenium Health Check", f"Selenium status check failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.error_handler.log_warning("Selenium Health Check", f"Selenium health check failed: {e}")
            return False
    
    def restart_selenium_container(self) -> bool:
        """Attempt to restart Selenium container"""
        try:
            self.error_handler.log_info("Selenium Restart", f"Attempting to restart container {self.container_name}")
            
            result = subprocess.run(
                ["docker", "restart", self.container_name],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                self.error_handler.log_info("Selenium Restart", "Container restart command successful")
                
                for attempt in range(12):
                    time.sleep(5)
                    if self.check_selenium_health():
                        self.error_handler.log_info("Selenium Restart", "Container healthy after restart")
                        return True
                
                self.error_handler.log_warning("Selenium Restart", "Container restarted but not responding after 60s")
                return False
            else:
                self.error_handler.log_error("Selenium Restart", Exception(f"Container restart failed: {result.stderr}"))
                return False
                
        except Exception as e:
            self.error_handler.log_error("Selenium Restart", e)
            return False
    
    def ensure_selenium_ready(self, max_attempts: int = 3) -> bool:
        """Ensure Selenium is ready, with restart attempts if needed"""
        for attempt in range(1, max_attempts + 1):
            self.error_handler.log_info("Selenium Ready Check", f"Attempt {attempt}/{max_attempts} - Checking Selenium health")
            
            if self.check_selenium_health():
                return True
            
            if attempt < max_attempts:
                self.error_handler.log_info("Selenium Recovery", f"Attempt {attempt}: Selenium unhealthy, attempting restart")
                if self.restart_selenium_container():
                    return True
                
                wait_time = 10 * attempt
                self.error_handler.log_info("Selenium Recovery", f"Waiting {wait_time}s before next attempt")
                time.sleep(wait_time)
        
        self.error_handler.log_error("Selenium Ready", Exception(f"Selenium not ready after {max_attempts} attempts"))
        return False
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status information"""
        try:
            is_healthy = self.check_selenium_health()
            status_info = {"healthy": is_healthy, "timestamp": time.time()}
            
            if is_healthy:
                try:
                    response = requests.get(f"{self.selenium_url}/status", timeout=5)
                    if response.status_code == 200:
                        status_data = response.json()
                        status_info.update({
                            "selenium_version": status_data.get("value", {}).get("build", {}).get("version"),
                            "ready": status_data.get("value", {}).get("ready"),
                            "message": status_data.get("value", {}).get("message")
                        })
                except:
                    pass
            
            return status_info
            
        except Exception as e:
            self.error_handler.log_error("Health Status", e)
            return {"healthy": False, "error": str(e), "timestamp": time.time()}
