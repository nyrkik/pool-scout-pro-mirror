/**
 * Download UI - Pool Scout Pro
 */
class DownloadUI {
    constructor() {
        this.progressContainer = document.getElementById('download-progress-container');
        this.progressList = document.getElementById('download-progress-list');
    }

    async handleSaveClick() {
        try {
            const currentResults = window.searchService.getCurrentResults();
            const unsaved = currentResults.filter(f => !f.saved);
            this.initializeProgressDisplay(unsaved);
            await window.downloadService.startDownload(currentResults);
        } catch (error) {
            console.error('Save click error:', error);
        }
    }

    initializeProgressDisplay(facilities) {
        if (!this.progressContainer) return;
        this.progressContainer.style.display = 'block';
        
        let html = '';
        facilities.forEach((facility, index) => {
            html += `
                <div class="download-item" data-facility-index="${facility.index}">
                    <div class="download-item-name">${this.escapeHtml(facility.name)}</div>
                    <div class="download-item-status"><span class="download-status-pending">Pending</span></div>
                </div>
            `;
        });
        this.progressList.innerHTML = html;
        this.updateProgressSummary(0, facilities.length);
    }

    updateProgressDisplay(progressData) {
        this.updateProgressSummary(
            progressData.completed_count,
            progressData.total_count
        );

        if (progressData.last_completed) {
            this.updateMainTableRow(progressData.last_completed);
            this.updateProgressListItem(progressData.last_completed, 'completed');
        }
        
        if (progressData.current_facility_name) {
             const item = document.querySelector(`.download-item[data-facility-index="${progressData.current_facility_index}"]`);
             if(item) item.classList.add('current-facility');
        }
    }
    
    updateProgressListItem(completed, status) {
        const item = document.querySelector(`.download-item[data-facility-index="${completed.index}"]`);
        if (!item) return;
        
        const statusEl = item.querySelector('.download-item-status span');
        statusEl.className = `download-status-${status === 'completed' ? 'success' : 'failed'}`;
        statusEl.textContent = status === 'completed' ? 'Completed' : 'Failed';
        
        // Remove current highlight when an item is done
        document.querySelectorAll('.download-item.current-facility').forEach(el => el.classList.remove('current-facility'));
    }

    updateMainTableRow(completed) {
        const index = completed.index;
        const row = document.querySelector(`#reports-table-body tr[data-facility-index="${index}"]`);
        if (!row) return;

        row.style.color = '#1f2937'; // Saved color
        const findingsCell = row.cells[3];
        if (findingsCell) {
            findingsCell.innerHTML = 'Click to view details';
        }

        const facilityData = window.searchService.getCurrentResults().find(f => f.index === index);
        if (facilityData) {
            facilityData.saved = true;
        }
    }

    updateProgressSummary(completed, total) {
        document.getElementById('download-completed').textContent = completed;
        document.getElementById('download-total').textContent = total;
        const percentage = total > 0 ? Math.round((completed / total) * 100) : 0;
        const headerElement = this.progressContainer.querySelector('.download-progress-header h3');
        if (headerElement) {
            headerElement.textContent = `Download Progress (${percentage}%)`;
        }
    }

    handleDownloadComplete(progressData) {
        console.log('🎉 Download complete!');
        const message = `Download completed: ${progressData.completed_count} successful, ${progressData.failed_count} failed`;
        
        // FIXED: Call showProgress and ensure the activity spinner is hidden
        window.uiManager?.showProgress(message, { showActivity: false });

        setTimeout(() => {
            if(this.progressContainer) this.progressContainer.style.display = 'none';
        }, 5000);
    }

    escapeHtml(text = '') {
        const map = {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'};
        return text.replace(/[&<>"']/g, m => map[m]);
    }
}
window.downloadUI = new DownloadUI();
