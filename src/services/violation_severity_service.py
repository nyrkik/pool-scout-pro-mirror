#!/usr/bin/env python3
"""
Violation Severity Assessment Service - Pool Scout Pro
Assigns severity levels to pool inspection violations based on public safety impact.
"""
import sqlite3
import re
import logging
import sys
import os
from core.database_config import db_config

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class ViolationSeverityService:
    def __init__(self):
        self.db_path = db_config.inspection_db_path
        self.logger = logging.getLogger(__name__)
        self.severity_patterns = self._get_severity_patterns()
        
    def _get_severity_patterns(self):
        """
        Define severity patterns for pool safety violations.
        Scale: 1-10, where 10 = immediate facility closure, 1 = minor administrative
        """
        return {
            # Level 10: Immediate facility closure/suspension
            10: [
                r'(facility|pool|spa).*?(closed|closure|suspended|shutdown)',
                r'immediate.*?(closure|suspension|shutdown)',
                r'emergency.*?(closure|shutdown)',
                r'public.*?health.*?(hazard|emergency)',
                r'imminent.*?(danger|hazard|threat)'
            ],
            
            # Level 9: Critical safety hazards
            9: [
                r'(main|safety).*?drain.*?(missing|broken|damaged|non.?compliant)',
                r'electrical.*?(hazard|shock|exposed|unsafe)',
                r'chemical.*?(leak|spill|hazard|exposure)',
                r'drowning.*?(hazard|risk)',
                r'entrapment.*?(hazard|risk)',
                r'suction.*?(entrapment|hazard)'
            ],
            
            # Level 8: Major equipment/safety failures
            8: [
                r'pump.*?(not.*?working|failed|broken|inoperative)',
                r'filtration.*?(not.*?working|failed|broken)',
                r'circulation.*?(inadequate|failed|poor)',
                r'safety.*?(equipment|barrier).*?(missing|broken|inadequate)',
                r'fence.*?(missing|broken|inadequate|non.?compliant)',
                r'gate.*?(missing|broken|self.?closing|self.?latching)'
            ],
            
            # Level 7: Serious code violations
            7: [
                r'major.*?violation',
                r'repeat.*?violation',
                r'life.*?(guard|safety).*?(missing|absent|unqualified)',
                r'emergency.*?equipment.*?(missing|broken|inadequate)',
                r'first.*?aid.*?(missing|expired|inadequate)',
                r'depth.*?marker.*?(missing|incorrect|illegible)'
            ],
            
            # Level 6: Equipment maintenance issues
            6: [
                r'filter.*?(dirty|clogged|needs.*?cleaning)',
                r'skimmer.*?(not.*?working|clogged|broken)',
                r'vacuum.*?(not.*?working|broken)',
                r'equipment.*?(maintenance|repair).*?(needed|required)',
                r'pool.*?equipment.*?(malfunction|problem)'
            ],
            
            # Level 5: Water quality issues requiring correction
            5: [
                r'chlorine.*?(low|high|out.*?of.*?range)',
                r'ph.*?(low|high|out.*?of.*?range)',
                r'alkalinity.*?(low|high|out.*?of.*?range)',
                r'water.*?quality.*?(poor|unacceptable)',
                r'chemical.*?(imbalance|out.*?of.*?range)',
                r'disinfectant.*?(low|inadequate|insufficient)'
            ],
            
            # Level 4: Maintenance and cleanliness
            4: [
                r'pool.*?(dirty|needs.*?cleaning|debris)',
                r'deck.*?(dirty|needs.*?cleaning|slippery)',
                r'tile.*?(dirty|needs.*?cleaning)',
                r'surface.*?(rough|needs.*?repair)',
                r'gutter.*?(dirty|clogged)',
                r'algae.*?(present|growth|visible)'
            ],
            
            # Level 3: Documentation and operational issues
            3: [
                r'log.*?(incomplete|missing|not.*?maintained)',
                r'record.*?(incomplete|missing|not.*?maintained)',
                r'documentation.*?(missing|incomplete|inadequate)',
                r'permit.*?(expired|missing|not.*?posted)',
                r'certificate.*?(expired|missing|not.*?posted)',
                r'hours.*?(not.*?posted|incorrect)'
            ],
            
            # Level 2: Minor equipment/facility issues
            2: [
                r'light.*?(burned.*?out|not.*?working)',
                r'sign.*?(missing|faded|needs.*?replacement)',
                r'paint.*?(peeling|needs.*?touch.*?up)',
                r'minor.*?(repair|maintenance).*?(needed|required)',
                r'cosmetic.*?(issue|problem)'
            ],
            
            # Level 1: Administrative/minor issues
            1: [
                r'administrative.*?(violation|issue)',
                r'paperwork.*?(missing|incomplete)',
                r'minor.*?(documentation|record).*?(issue|problem)',
                r'filing.*?(issue|problem|late)',
                r'notification.*?(issue|late|missing)'
            ]
        }
    
    def assess_violation_severity(self, violation_title="", observations="", violation_code=""):
        """
        Assess the severity level of a violation based on title and observations.
        Returns dict with severity_level, reasoning, and matched_pattern.
        """
        try:
            # Combine all text for pattern matching
            full_text = f"{violation_title} {observations}".lower().strip()
            
            if not full_text:
                return self._default_severity("No violation text provided")
            
            # Try pattern matching from highest to lowest severity
            for severity_level in sorted(self.severity_patterns.keys(), reverse=True):
                patterns = self.severity_patterns[severity_level]
                
                for pattern in patterns:
                    if re.search(pattern, full_text, re.IGNORECASE):
                        return {
                            'severity_level': severity_level,
                            'reasoning': self._get_severity_reasoning(severity_level),
                            'matched_pattern': pattern,
                            'source': 'pattern_matching'
                        }
            
            # Fallback: Try to infer from violation code or keywords
            return self._assess_by_keywords(full_text, violation_code)
            
        except Exception as e:
            self.logger.error(f"Error assessing violation severity: {e}")
            return self._default_severity(f"Error during assessment: {str(e)}")
    
    def _assess_by_keywords(self, text, violation_code=""):
        """Fallback assessment using general keywords when patterns don't match."""
        
        # High-priority keywords
        high_keywords = ['closure', 'suspended', 'hazard', 'emergency', 'major', 'critical']
        medium_keywords = ['repair', 'maintenance', 'equipment', 'safety', 'broken']
        low_keywords = ['log', 'documentation', 'sign', 'minor', 'cosmetic']
        
        if any(keyword in text for keyword in high_keywords):
            return {
                'severity_level': 7,
                'reasoning': 'Contains high-priority safety keywords',
                'matched_pattern': 'keyword_fallback_high',
                'source': 'keyword_fallback'
            }
        elif any(keyword in text for keyword in medium_keywords):
            return {
                'severity_level': 5,
                'reasoning': 'Contains medium-priority operational keywords',
                'matched_pattern': 'keyword_fallback_medium',
                'source': 'keyword_fallback'
            }
        elif any(keyword in text for keyword in low_keywords):
            return {
                'severity_level': 2,
                'reasoning': 'Contains low-priority administrative keywords',
                'matched_pattern': 'keyword_fallback_low',
                'source': 'keyword_fallback'
            }
        
        # Ultimate fallback
        return self._default_severity("No matching patterns or keywords found")
    
    def _get_severity_reasoning(self, level):
        """Get human-readable reasoning for severity levels."""
        reasoning_map = {
            10: "Immediate facility closure or public health emergency",
            9: "Critical safety hazard requiring immediate attention",
            8: "Major equipment failure affecting safety or operations", 
            7: "Serious code violation or repeat offense",
            6: "Equipment maintenance issue affecting functionality",
            5: "Water quality issue requiring correction",
            4: "Maintenance and cleanliness issue",
            3: "Documentation or operational compliance issue",
            2: "Minor equipment or facility issue",
            1: "Administrative or minor documentation issue"
        }
        return reasoning_map.get(level, f"Severity level {level}")
    
    def _default_severity(self, reason):
        """Return default severity when assessment fails."""
        return {
            'severity_level': 4,  # Mid-range default
            'reasoning': f"Default severity assigned: {reason}",
            'matched_pattern': 'default',
            'source': 'default'
        }
    
    def bulk_assess_violations(self, limit=None):
        """
        Assess severity for all violations that don't have severity_level assigned.
        Returns count of processed violations.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get violations without severity
            query = "SELECT id, violation_title, observations, violation_code FROM violations WHERE severity_level IS NULL"
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query)
            violations = cursor.fetchall()
            
            processed_count = 0
            for violation_id, title, observations, code in violations:
                assessment = self.assess_violation_severity(
                    violation_title=title or "",
                    observations=observations or "",
                    violation_code=code or ""
                )
                
                cursor.execute(
                    "UPDATE violations SET severity_level = ? WHERE id = ?",
                    (assessment['severity_level'], violation_id)
                )
                processed_count += 1
                
                if processed_count % 100 == 0:
                    self.logger.info(f"Processed {processed_count} violations...")
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Successfully assessed severity for {processed_count} violations")
            return processed_count
            
        except Exception as e:
            self.logger.error(f"Error in bulk assessment: {e}")
            return 0

# Convenience function for use in other modules
def assess_violation_severity(violation_title="", observations="", violation_code=""):
    """Standalone function to assess violation severity."""
    service = ViolationSeverityService()
    return service.assess_violation_severity(violation_title, observations, violation_code)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Test the severity assessment
    service = ViolationSeverityService()
    
    test_cases = [
        ("Pool closure required", "Facility must be closed immediately due to safety hazard", "12a"),
        ("Low chlorine level", "Chlorine level at 0.8 ppm, below required 1.0 ppm minimum", "8c"),
        ("Missing log entries", "Daily maintenance log has missing entries for past week", "15b")
    ]
    
    print("Testing Severity Assessment:")
    for title, obs, code in test_cases:
        result = service.assess_violation_severity(title, obs, code)
        print(f"\nViolation: {title}")
        print(f"Severity: {result['severity_level']}/10")
        print(f"Reasoning: {result['reasoning']}")
