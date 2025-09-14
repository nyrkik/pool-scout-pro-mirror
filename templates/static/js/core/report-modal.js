/**
 * Report Modal - Pool Scout Pro
 * Handles detailed report modal dialogs with comprehensive inspection information.
 */

class ReportModal {
    show(index) {
        const currentResults = window.searchService.getCurrentResults();
        const reportData = currentResults[index];

        if (!reportData) return;

        // Close any existing modal
        this.close();

        const modalHtml = this._buildModalHtml(reportData);
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Add event listener to close modal on overlay click
        const overlay = document.getElementById('report-modal-overlay');
        if (overlay) {
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) {
                    this.close();
                }
            });
        }
    }

    close() {
        const existingModal = document.getElementById('report-modal-overlay');
        if (existingModal) {
            existingModal.remove();
        }
    }

    _buildModalHtml(data) {
        const facility = data.facility || {};
        const violations = data.violations || [];

        const violationsHtml = violations.length > 0
            ? violations.map(v => `
                <li class="violation-item">
                    <strong class="violation-summary">${this._escape(v.shorthand_summary || v.violation_title)}</strong>
                    <p class="violation-observation">${this._escape(v.observations)}</p>
                </li>
            `).join('')
            : '<li>No violations recorded.</li>';

        return `
            <div id="report-modal-overlay" class="report-modal-overlay">
                <div class="report-modal-content">
                    <div class="report-modal-header">
                        <div>
                            <h2 class="facility-name">${this._escape(facility.name)}</h2>
                            <p class="facility-address">${this._escape(facility.street_address)}, ${this._escape(facility.city)}</p>
                        </div>
                        <button onclick="window.reportModal.close()" class="close-button" aria-label="Close report details">&times;</button>
                    </div>
                    
                    <div class="report-modal-body">
                        <div class="report-modal-section">
                            <h3>Inspection Details</h3>
                            <ul>
                                <li><strong>Date:</strong> ${this._escape(data.inspection_date)}</li>
                                <li><strong>Type:</strong> ${this._escape(data.inspection_type)}</li>
                                <li><strong>Inspector:</strong> ${this._escape(data.inspector_name)}</li>
                            </ul>
                        </div>
                        <div class="report-modal-section">
                            <h3>Violations (${violations.length})</h3>
                            <ul class="violations-list">${violationsHtml}</ul>
                        </div>
                        <div class="report-modal-section">
                            <h3>Inspector Notes</h3>
                            <p class="report-notes">${this._escape(data.report_notes) || 'No notes provided.'}</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    _escape(text = '') {
        if (text === null || text === undefined) return '';
        const map = {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'};
        return String(text).replace(/[&<>"']/g, m => map[m]);
    }
}

window.reportModal = new ReportModal();
