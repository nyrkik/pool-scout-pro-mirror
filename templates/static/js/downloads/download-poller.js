/**
 * Download Poller - Pool Scout Pro
 * 
 * Polls backend progress endpoints during downloads to provide real-time updates.
 * Responsibilities:
 * - Poll /api/v1/downloads/progress every 2 seconds during active downloads
 * - Update progress bar and facility status displays
 * - Stop polling when downloads complete
 * - Handle polling errors gracefully
 */

class DownloadPoller {
    constructor() {
        this.isPolling = false;
        this.pollInterval = null;
        this.pollFrequency = 2000; // 2 seconds
        this.maxPollErrors = 3;
        this.currentErrors = 0;
        this.lastProgressData = null;
    }

    startPolling(facilities) {
        if (this.isPolling) {
            console.log('📊 Polling already active');
            return;
        }

        console.log('🔄 Starting download progress polling');
        this.isPolling = true;
        this.currentErrors = 0;
        this.lastProgressData = null;

        // Initialize progress UI
        window.downloadUI?.initializeProgressDisplay(facilities);

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

        console.log('⏹️ Stopping download progress polling');
        this.isPolling = false;

        if (this.pollInterval) {
            clearInterval(this.pollInterval);
            this.pollInterval = null;
        }

        this.currentErrors = 0;
        this.lastProgressData = null;
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
        // Update last known progress
        this.lastProgressData = progressData;

        // Update progress display
        window.downloadUI?.updateProgressDisplay(progressData);

        // Check if download is complete
        if (!progressData.is_active || progressData.status === 'completed') {
            console.log('✅ Download completed, stopping polling');
            this.stopPolling();
            window.downloadUI?.handleDownloadComplete(progressData);
        }

        // Log progress updates (can be removed in production)
        if (progressData.is_active) {
            console.log(`📊 Progress: ${progressData.percentage}% - ${progressData.current_facility}`);
        }
    }

    handlePollError(error) {
        console.error('❌ Progress poll error:', error);
        this.currentErrors++;

        if (this.currentErrors >= this.maxPollErrors) {
            console.error('❌ Too many polling errors, stopping');
            this.stopPolling();
            window.downloadUI?.handlePollingError('Failed to get download progress updates');
        }
    }

    getLastProgress() {
        return this.lastProgressData;
    }

    isActive() {
        return this.isPolling;
    }

    // Manual progress check (for testing)
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

// Global download poller instance
window.downloadPoller = new DownloadPoller();
