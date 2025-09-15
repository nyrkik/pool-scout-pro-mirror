/**
 * Violation Modal - Pool Scout Pro
 * 
 * Handles violation detail modal dialogs.
 * Shows ALL violations sorted by severity when users click on violation summaries.
 */

class ViolationModal {
    show(facilityIndex) {
        const currentResults = window.searchService.getCurrentResults();
        const facility = currentResults[facilityIndex];
        
        if (!facility || !facility.violations || facility.violations.length === 0) return;

        // Close existing modal if open
        const existingModal = document.getElementById('violations-modal');
        if (existingModal) {
            existingModal.remove();
            return;
        }

        // Sort violations by severity (highest first), then alphabetically
        const sortedViolations = [...facility.violations].sort((a, b) => {
            const severityA = a.severity_level || 0;
            const severityB = b.severity_level || 0;
            if (severityB !== severityA) {
                return severityB - severityA;
            }
            
            const titleA = a.violation_title || '';
            const titleB = b.violation_title || '';
            return titleA.localeCompare(titleB);
        });

        const modalHtml = this._buildViolationsModalHtml(facility, sortedViolations);
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Add event listener to close modal on overlay click
        const overlay = document.getElementById('violations-modal');
        if (overlay) {
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) {
                    this.close();
                }
            });
        }
    }

    close() {
        const existingModal = document.getElementById('violations-modal');
        if (existingModal) {
            existingModal.remove();
        }
    }

    _buildViolationsModalHtml(facility, violations) {
        const violationsHtml = violations.map(violation => {
            const code = violation.violation_code || '';
            const title = violation.violation_title || 'Unknown Violation';
            const observations = violation.observations || 'No observations recorded.';
            const severity = violation.severity_level || 0;
            
            // Add severity indicator
            const severityIndicator = severity >= 8 ? ' 🚨' : severity >= 6 ? ' ⚠️' : '';
            
            return `
                <li class="violation-item" style="margin-bottom: 20px; border-bottom: 1px solid #e5e7eb; padding-bottom: 16px;">
                    <div class="violation-header" style="display: flex; justify-content: between; align-items: center; margin-bottom: 8px;">
                        <strong class="violation-code-title" style="color: #1f2937; font-size: 16px;">
                            ${this._escape(code)}. ${this._escape(title)}${severityIndicator}
                        </strong>
                        ${severity > 0 ? `<span class="severity-badge" style="background: ${this._getSeverityColor(severity)}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px; margin-left: 10px;">Level ${severity}</span>` : ''}
                    </div>
                    <div class="violation-observations" style="color: #6b7280; font-size: 14px; line-height: 1.5; margin-left: 0;">
                        <strong>Observations:</strong> ${this._escape(observations)}
                    </div>
                </li>
            `;
        }).join('');

        return `
            <div id="violations-modal" class="modal-overlay" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 1000; display: flex; align-items: center; justify-content: center;">
                <div class="modal-content" style="background: white; border-radius: 12px; max-width: 900px; max-height: 85vh; overflow-y: auto; margin: 20px; box-shadow: 0 8px 32px rgba(0,0,0,0.3);">
                    <div class="modal-header" style="padding: 20px; border-bottom: 1px solid #e5e7eb; display: flex; justify-content: space-between; align-items: center; position: sticky; top: 0; background: white; border-radius: 12px 12px 0 0;">
                        <div>
                            <h2 style="margin: 0; color: #1f2937; font-size: 20px;">${this._escape(facility.name)}</h2>
                            <p style="margin: 4px 0 0 0; color: #6b7280; font-size: 14px;">All Violations (${violations.length}) - Sorted by Severity</p>
                        </div>
                        <button onclick="window.violationModal.close()" style="border: none; background: none; font-size: 24px; color: #6b7280; cursor: pointer; padding: 4px;">&times;</button>
                    </div>
                    
                    <div class="modal-body" style="padding: 20px;">
                        <ul style="list-style: none; padding: 0; margin: 0;">
                            ${violationsHtml}
                        </ul>
                    </div>
                </div>
            </div>
        `;
    }

    _getSeverityColor(severity) {
        if (severity >= 9) return '#dc2626'; // Red for critical
        if (severity >= 7) return '#ea580c'; // Orange for serious
        if (severity >= 5) return '#d97706'; // Amber for moderate
        if (severity >= 3) return '#65a30d'; // Green for minor
        return '#6b7280'; // Gray for lowest
    }

    _escape(text = '') {
        if (text === null || text === undefined) return '';
        const map = {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'};
        return String(text).replace(/[&<>"']/g, m => map[m]);
    }
}

window.violationModal = new ViolationModal();
