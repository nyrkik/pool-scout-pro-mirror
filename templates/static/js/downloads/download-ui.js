/**
 * Enhanced Download UI - Pool Scout Pro
 * Real-time download feedback with visual state management
 */
class DownloadUI {
    constructor() {
        this.progressContainer = document.getElementById('download-progress-container');
        this.progressList = document.getElementById('download-progress-list');
        this.downloadStates = new Map(); // Track individual facility states
        this.totalCount = 0;
        this.completedCount = 0;
        this.failedCount = 0;
    }

    async handleSaveClick() {
        try {
            const currentResults = window.searchService.getCurrentResults();
            const unsaved = currentResults.filter(f => !f.saved);
            
            // Initialize tracking for all unsaved facilities
            this.initializeDownloadTracking(unsaved);
            
            // Immediately update visual states to "downloading"
            this.setFacilitiesDownloading(unsaved);
            
            await window.downloadService.startDownload(currentResults);
        } catch (error) {
            console.error('Save click error:', error);
            // Reset visual states on error
            this.resetFacilityStates();
        }
    }

    initializeDownloadTracking(facilities) {
        this.downloadStates.clear();
        this.totalCount = facilities.length;
        this.completedCount = 0;
        this.failedCount = 0;

        facilities.forEach(facility => {
            this.downloadStates.set(facility.index, {
                name: facility.name,
                status: 'pending', // pending -> downloading -> completed/failed
                facility: facility
            });
        });

        this.updateProgressMessage();
    }

    setFacilitiesDownloading(facilities) {
        facilities.forEach(facility => {
            // Update internal state
            const state = this.downloadStates.get(facility.index);
            if (state) {
                state.status = 'downloading';
            }

            // Update visual state immediately
            this.updateFacilityRowState(facility.index, 'downloading');
            
            // Update in-memory facility data
            facility.saved = 'downloading';
        });

        // Update progress message
        this.updateProgressMessage();
    }

    updateFacilityRowState(facilityIndex, status) {
        const row = document.querySelector(`#reports-table-body tr[data-facility-index="${facilityIndex}"]`);
        if (!row) return;

        // Remove all state classes
        row.classList.remove('facility-row-unsaved', 'facility-row-downloading', 'facility-row-saved', 'facility-row-failed');
        
        // Add appropriate state class
        switch(status) {
            case 'downloading':
                row.classList.add('facility-row-downloading');
                break;
            case 'completed':
            case 'saved':
                row.classList.add('facility-row-saved');
                break;
            case 'failed':
                row.classList.add('facility-row-failed');
                break;
            default:
                row.classList.add('facility-row-unsaved');
        }
    }

    updateProgressMessage() {
        const inProgress = this.totalCount - this.completedCount - this.failedCount;
        let message;

        if (this.completedCount === 0 && this.failedCount === 0) {
            message = `Starting downloads... (${this.totalCount} facilities)`;
        } else if (this.completedCount + this.failedCount < this.totalCount) {
            message = `Downloading... (${this.completedCount + this.failedCount} of ${this.totalCount} completed)`;
        } else {
            message = `Download complete: ${this.completedCount} successful, ${this.failedCount} failed`;
        }

        window.uiManager?.showProgress(message, { 
            showActivity: inProgress > 0 
        });
    }

    handleFacilityCompleted(facilityIndex, success = true) {
        const state = this.downloadStates.get(facilityIndex);
        if (!state) return;

        // Update internal state
        state.status = success ? 'completed' : 'failed';
        
        // Update counters
        if (success) {
            this.completedCount++;
        } else {
            this.failedCount++;
        }

        // Update visual state
        this.updateFacilityRowState(facilityIndex, success ? 'completed' : 'failed');

        // Update in-memory facility data
        const facility = state.facility;
        if (facility) {
            facility.saved = success;
        }

        // Update progress message
        this.updateProgressMessage();

        // Check if all downloads are complete
        if (this.completedCount + this.failedCount >= this.totalCount) {
            this.handleAllDownloadsComplete();
        }
    }

    handleAllDownloadsComplete() {
        console.log('All downloads completed');
        
        // Final progress message
        this.updateProgressMessage();

        // Hide progress after delay
        setTimeout(() => {
            window.uiManager?.hideProgress();
        }, 5000);

        // Update button state back to search mode
        if (window.searchUI) {
            window.searchUI.setButtonToSearchMode();
        }

        // Refresh saved/unsaved counts
        this.updateResultsCounts();
    }

    updateResultsCounts() {
        const currentResults = window.searchService.getCurrentResults();
        const savedCount = currentResults.filter(f => f.saved === true).length;
        const unsavedCount = currentResults.filter(f => !f.saved || f.saved === 'downloading').length;
        
        window.uiManager?.updateResultsCounts(unsavedCount, savedCount);
    }

    resetFacilityStates() {
        // Reset all facilities back to unsaved state on error
        this.downloadStates.forEach((state, facilityIndex) => {
            this.updateFacilityRowState(facilityIndex, 'unsaved');
            if (state.facility) {
                state.facility.saved = false;
            }
        });

        this.downloadStates.clear();
        this.totalCount = 0;
        this.completedCount = 0;
        this.failedCount = 0;
    }

    // Legacy methods for compatibility
    initializeProgressDisplay(facilities) {
        // Legacy method - now handled by initializeDownloadTracking
        console.log('Legacy initializeProgressDisplay called');
    }

    updateProgressDisplay(progressData) {
        // Handle progress updates from polling system
        if (progressData.last_completed) {
            this.handleFacilityCompleted(progressData.last_completed.index, true);
        }

        // Handle failed facility updates if provided
        if (progressData.last_failed) {
            this.handleFacilityCompleted(progressData.last_failed.index, false);
        }
    }

    updateMainTableRow(completed) {
        // Legacy method - now handled by handleFacilityCompleted
        this.handleFacilityCompleted(completed.index, true);
    }

    handleDownloadComplete(progressData) {
        // Legacy method - now handled by handleAllDownloadsComplete
        this.handleAllDownloadsComplete();
    }

    escapeHtml(text = '') {
        const map = {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'};
        return text.replace(/[&<>"']/g, m => map[m]);
    }
}

window.downloadUI = new DownloadUI();
