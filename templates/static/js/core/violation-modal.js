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
