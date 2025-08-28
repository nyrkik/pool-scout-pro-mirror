#!/usr/bin/env python3
"""
Robust Selenium Monitor - Pool Scout Pro
Comprehensive health monitoring with session management and proactive cleanup
"""

import time
import requests
import subprocess
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from core.error_handler import ErrorHandler

class RobustSeleniumMonitor:
    """Comprehensive Selenium monitoring with session management"""
    
    def __init__(self):
        self.error_handler = ErrorHandler(__name__)
        self.selenium_url = "http://localhost:4444"
        self.container_name = "selenium-firefox"
        self.health_check_timeout = 10
        self.max_session_age_minutes = 15  # Kill sessions older than 30 minutes
        self.max_idle_session_minutes = 5  # Kill sessions idle for 10+ minutes
        self.session_cleanup_threshold = 0.6  # Cleanup when 80% of max sessions used
        
    def comprehensive_health_check(self) -> Dict[str, Any]:
        """Comprehensive health assessment with detailed diagnostics"""
        health_report = {
            'timestamp': datetime.now().isoformat(),
            'overall_healthy': False,
            'selenium_responsive': False,
            'selenium_ready': False,
            'container_running': False,
            'session_health': {},
            'resource_status': {},
            'issues_detected': [],
            'actions_taken': []
        }
        
        try:
            # 1. Check container status
            health_report['container_running'] = self._check_container_running()
            
            if not health_report['container_running']:
                health_report['issues_detected'].append('Container not responding - external monitor will handle')
                return health_report
            
            # 2. Check Selenium API responsiveness
            selenium_status = self._get_selenium_status()
            health_report['selenium_responsive'] = selenium_status is not None
            
            if not health_report['selenium_responsive']:
                health_report['issues_detected'].append('Selenium API not responding')
                return health_report
            
            # 3. Analyze Selenium status in detail
            health_report['selenium_ready'] = selenium_status.get('value', {}).get('ready', False)
            
            # 4. Deep session analysis
            session_analysis = self._analyze_sessions(selenium_status)
            health_report['session_health'] = session_analysis
            
            # 5. Check for session issues and cleanup if needed
            cleanup_actions = self._proactive_session_cleanup(session_analysis)
            health_report['actions_taken'].extend(cleanup_actions)
            
            # 6. Resource monitoring
            resource_status = self._check_resource_status(selenium_status)
            health_report['resource_status'] = resource_status
            
            # 7. Determine overall health
            health_report['overall_healthy'] = self._determine_overall_health(health_report)
            
            # 8. Log health summary
            self._log_health_summary(health_report)
            
            return health_report
            
        except Exception as e:
            self.error_handler.log_error("Comprehensive Health Check", e)
            health_report['issues_detected'].append(f"Health check failed: {str(e)}")
            return health_report
    
    def _get_selenium_status(self) -> Optional[Dict[str, Any]]:
        """Get Selenium status with timeout and error handling"""
        try:
            response = requests.get(f"{self.selenium_url}/status", timeout=self.health_check_timeout)
            if response.status_code == 200:
                return response.json()
            else:
                self.error_handler.log_warning("Selenium Status", f"Non-200 response: {response.status_code}")
                return None
        except Exception as e:
            self.error_handler.log_warning("Selenium Status", f"Request failed: {e}")
            return None
    
    def _analyze_sessions(self, selenium_status: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive session analysis"""
        session_analysis = {
            'total_sessions': 0,
            'active_sessions': 0,
            'stuck_sessions': [],
            'old_sessions': [],
            'idle_sessions': [],
            'max_sessions': 0,
            'session_utilization': 0.0,
            'session_details': []
        }
        
        try:
            nodes = selenium_status.get('value', {}).get('nodes', [])
            
            for node in nodes:
                max_sessions = node.get('maxSessions', 1)
                session_analysis['max_sessions'] = max_sessions
                
                slots = node.get('slots', [])
                
                for slot in slots:
                    session = slot.get('session')
                    if session:
                        session_analysis['active_sessions'] += 1
                        session_details = self._analyze_individual_session(session, slot)
                        session_analysis['session_details'].append(session_details)
                        
                        # Check for problematic sessions
                        if session_details['is_stuck']:
                            session_analysis['stuck_sessions'].append(session_details)
                        if session_details['is_old']:
                            session_analysis['old_sessions'].append(session_details)
                        if session_details['is_idle']:
                            session_analysis['idle_sessions'].append(session_details)
            
            session_analysis['total_sessions'] = session_analysis['active_sessions']
            session_analysis['session_utilization'] = session_analysis['active_sessions'] / max(max_sessions, 1)
            
        except Exception as e:
            self.error_handler.log_error("Session Analysis", e)
        
        return session_analysis
    
    def _analyze_individual_session(self, session: Dict[str, Any], slot: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze individual session for issues"""
        session_id = session.get('sessionId', 'unknown')
        start_time_str = session.get('start', slot.get('lastStarted', '1970-01-01T00:00:00Z'))
        
        try:
            start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
            age_minutes = (datetime.now(start_time.tzinfo) - start_time).total_seconds() / 60
        except:
            age_minutes = 0
        
        session_details = {
            'session_id': session_id,
            'start_time': start_time_str,
            'age_minutes': age_minutes,
            'is_stuck': age_minutes > self.max_session_age_minutes,
            'is_old': age_minutes > self.max_session_age_minutes * 0.7,  # 70% of max age
            'is_idle': age_minutes > self.max_idle_session_minutes,
            'capabilities': session.get('capabilities', {}),
            'uri': session.get('uri', '')
        }
        
        return session_details
    
    def _proactive_session_cleanup(self, session_analysis: Dict[str, Any]) -> List[str]:
        """Proactive session cleanup based on analysis"""
        actions_taken = []
        
        try:
            # 1. Clean up stuck sessions (highest priority)
            for stuck_session in session_analysis['stuck_sessions']:
                if self._kill_session(stuck_session['session_id']):
                    actions_taken.append(f"Killed stuck session {stuck_session['session_id']} (age: {stuck_session['age_minutes']:.1f}m)")
            
            # 2. Clean up idle sessions if utilization is high
            if session_analysis['session_utilization'] > self.session_cleanup_threshold:
                for idle_session in session_analysis['idle_sessions']:
                    if self._kill_session(idle_session['session_id']):
                        actions_taken.append(f"Killed idle session {idle_session['session_id']} (idle: {idle_session['age_minutes']:.1f}m)")
            
            # 3. Clean up old sessions if at capacity
            if session_analysis['session_utilization'] >= 1.0:
                for old_session in session_analysis['old_sessions']:
                    if self._kill_session(old_session['session_id']):
                        actions_taken.append(f"Killed old session {old_session['session_id']} (age: {old_session['age_minutes']:.1f}m)")
            
        except Exception as e:
            self.error_handler.log_error("Session Cleanup", e)
        
        return actions_taken
    
    def _kill_session(self, session_id: str) -> bool:
        """Kill a specific Selenium session"""
        try:
            response = requests.delete(f"{self.selenium_url}/session/{session_id}", timeout=10)
            success = response.status_code in [200, 404]  # 404 means already gone
            
            if success:
                self.error_handler.log_info("Session Cleanup", f"Successfully killed session {session_id}")
            else:
                self.error_handler.log_warning("Session Cleanup", f"Failed to kill session {session_id}: {response.status_code}")
            
            return success
            
        except Exception as e:
            self.error_handler.log_error("Session Kill", e)
            return False
    
    def _check_resource_status(self, selenium_status: Dict[str, Any]) -> Dict[str, Any]:
        """Check resource utilization and health"""
        resource_status = {
            'node_availability': 'unknown',
            'memory_status': 'unknown',
            'session_capacity': 'unknown'
        }
        
        try:
            nodes = selenium_status.get('value', {}).get('nodes', [])
            
            for node in nodes:
                resource_status['node_availability'] = node.get('availability', 'unknown')
                
                # Calculate session capacity
                max_sessions = node.get('maxSessions', 1)
                active_sessions = len([slot for slot in node.get('slots', []) if slot.get('session')])
                capacity_percent = (active_sessions / max_sessions) * 100
                
                if capacity_percent >= 100:
                    resource_status['session_capacity'] = 'at_capacity'
                elif capacity_percent >= 80:
                    resource_status['session_capacity'] = 'high'
                elif capacity_percent >= 50:
                    resource_status['session_capacity'] = 'medium'
                else:
                    resource_status['session_capacity'] = 'low'
        
        except Exception as e:
            self.error_handler.log_error("Resource Status Check", e)
        
        return resource_status
    
    def _check_container_running(self) -> bool:
        """Check if Selenium container is running via API availability"""
        # Skip docker commands from application - use API responsiveness instead
        return self._get_selenium_status() is not None
    
    def _restart_container(self) -> bool:
        """Restart Selenium container"""
        try:
            self.error_handler.log_info("Container Restart", f"Attempting to restart {self.container_name}")
            
            result = subprocess.run(
                ["docker", "restart", self.container_name],
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode == 0:
                # Wait for container to be ready
                for attempt in range(12):
                    time.sleep(5)
                    if self._get_selenium_status():
                        self.error_handler.log_info("Container Restart", "Container restarted and responsive")
                        return True
                
                self.error_handler.log_warning("Container Restart", "Container restarted but not responsive")
                return False
            else:
                self.error_handler.log_error("Container Restart", Exception(f"Restart failed: {result.stderr}"))
                return False
                
        except Exception as e:
            self.error_handler.log_error("Container Restart", e)
            return False
    
    def _determine_overall_health(self, health_report: Dict[str, Any]) -> bool:
        """Determine overall system health for multiple sessions"""
        session_health = health_report['session_health']
        stuck_sessions = len(session_health.get('stuck_sessions', []))
        utilization = session_health.get('session_utilization', 0.0)
        
        critical_issues = [
            not health_report['container_running'],
            not health_report['selenium_responsive'],
            stuck_sessions > 2,  # Allow 1-2 stuck sessions with 5 total
            utilization >= 1.0   # All sessions occupied
        ]
        
        # System is healthy if no critical issues and some capacity available
        return not any(critical_issues) and health_report['selenium_responsive']
    
    def _log_health_summary(self, health_report: Dict[str, Any]) -> None:
        """Log comprehensive health summary"""
        status = "✅ HEALTHY" if health_report['overall_healthy'] else "❌ UNHEALTHY"
        
        session_health = health_report['session_health']
        active_sessions = session_health.get('active_sessions', 0)
        stuck_sessions = len(session_health.get('stuck_sessions', []))
        utilization = session_health.get('session_utilization', 0.0) * 100
        
        summary = f"{status} | Sessions: {active_sessions} active, {stuck_sessions} stuck, {utilization:.1f}% utilization"
        
        if health_report['actions_taken']:
            summary += f" | Actions: {', '.join(health_report['actions_taken'])}"
        
        if health_report['issues_detected']:
            summary += f" | Issues: {', '.join(health_report['issues_detected'])}"
        
        if health_report['overall_healthy']:
            self.error_handler.log_info("Robust Monitor", summary)
        else:
            self.error_handler.log_warning("Robust Monitor", summary)
