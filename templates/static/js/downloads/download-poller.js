/**
 * Enhanced Download Poller - Pool Scout Pro
 * 
 * Polls backend for individual facility completion events and provides 
 * real-time updates to the enhanced download UI system.
 */

class DownloadPoller {
    constructor() {
        this.isPolling = false;
        this.pollInterval = null;
        this.pollFrequency = 2000; // 2 seconds
        this.maxPollErrors = 3;
        this.currentErrors = 0;
        this.lastProgressData = null;
        this.processedFacilities = new Set(); // Track which facilities we've already processed
    }

    startPolling() {
        if (this.isPolling) {
            console.log('Polling already active');
            return;
        }

        console.log('Starting enhanced download progress polling');
        this.isPolling = true;
        this.currentErrors = 0;
        this.lastProgressData = null;
        this.processedFacilities.clear();

        // Start polling
        this.pollInterval = setInterval(() => {
            this.pollProgress();
        }, this.pollFrequency);

        // Do first poll immediately
        this.pollProgress();
    }

    stopPolling() {
        if (!this.isPolling) {
            return;
        }

        console.log('Stopping download progress polling');
        this.isPolling = false;

        if (this.pollInterval) {
            clearInterval(this.pollInterval);
            this.pollInterval = null;
        }

        this.currentErrors = 0;
        this.lastProgressData = null;
        this.processedFacilities.clear();
    }

    async pollProgress() {
        try {
            const response = await fetch('/api/v1/downloads/progress');
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            if (data.success) {
                this.handleProgressUpdate(data.progress);
                this.currentErrors = 0; // Reset error count on success
            } else {
                throw new Error(data.error || 'Failed to get progress data');
            }

        } catch (error) {
            this.handlePollError(error);
        }
    }

    handleProgressUpdate(progressData) {
        this.lastProgressData = progressData;

        // Handle individual facility completions
        if (progressData.completed_facilities) {
            progressData.completed_facilities.forEach(facilityData => {
                const facilityKey = `${facilityData.index}_${facilityData.status}`;
                
                // Only process each facility completion once
                if (!this.processedFacilities.has(facilityKey)) {
                    this.processedFacilities.add(facilityKey);
                    
                    const success = facilityData.status === 'completed' || facilityData.status === 'success';
                    window.downloadUI?.handleFacilityCompleted(facilityData.index, success);
                }
            });
        }

        // Legacy support - handle single facility completion
        if (progressData.last_completed) {
            const facilityKey = `${progressData.last_completed.index}_completed`;
            if (!this.processedFacilities.has(facilityKey)) {
                this.processedFacilities.add(facilityKey);
                window.downloadUI?.handleFacilityCompleted(progressData.last_completed.index, true);
            }
        }

        if (progressData.last_failed) {
            const facilityKey = `${progressData.last_failed.index}_failed`;
            if (!this.processedFacilities.has(facilityKey)) {
                this.processedFacilities.add(facilityKey);
                window.downloadUI?.handleFacilityCompleted(progressData.last_failed.index, false);
            }
        }

        // Check if download is complete
        if (!progressData.is_active || progressData.status === 'completed') {
            console.log('Download completed, stopping polling');
            this.stopPolling();
            
            // Let the downloadUI handle completion - it will manage final states
            // Don't call handleDownloadComplete as the UI handles this automatically
        }

        // Log progress updates for debugging
        if (progressData.is_active && progressData.current_facility) {
            console.log(`Progress: ${progressData.completed_count || 0}/${progressData.total_count || 0} - ${progressData.current_facility}`);
        }
    }

    handlePollError(error) {
        console.error('Progress poll error:', error);
        this.currentErrors++;

        if (this.currentErrors >= this.maxPollErrors) {
            console.error('Too many polling errors, stopping');
            this.stopPolling();
            
            // Notify UI of polling failure
            window.uiManager?.showProgress('Lost connection to download progress. Downloads may still be running.', { showActivity: false });
        }
    }

    getLastProgress() {
        return this.lastProgressData;
    }

    isActive() {
        return this.isPolling;
    }

    async checkProgress() {
        try {
            const response = await fetch('/api/v1/downloads/progress');
            const data = await response.json();
            console.log('Manual progress check:', data);
            return data;
        } catch (error) {
            console.error('Manual progress check failed:', error);
            return null;
        }
    }
}

window.downloadPoller = new DownloadPoller();
