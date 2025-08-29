/**
 * Enhanced Download Service - Pool Scout Pro
 *
 * Integrates with real-time progress polling and visual feedback system.
 */
class DownloadService {
    constructor() {
        this.isDownloading = false;
    }

    async startDownload(facilities) {
        console.log('DOWNLOAD SERVICE: startDownload called');
        console.log('DOWNLOAD SERVICE: facilities parameter:', facilities);

        if (this.isDownloading) {
            console.log('Download already in progress, ignoring click');
            window.uiManager?.showProgress('Download already in progress.', { showActivity: false });
            return;
        }

        const unsavedFacilities = facilities.filter(f => !f.saved);
        console.log('DOWNLOAD SERVICE: filtered to', unsavedFacilities.length, 'unsaved facilities');
        
        if (unsavedFacilities.length === 0) {
            const msg = 'All facilities are already saved.';
            window.uiManager?.showProgress(msg, { showActivity: false });
            throw new Error(msg);
        }

        this.isDownloading = true;
        window.uiManager?.setSaveButtonProcessing(true);

        try {
            console.log('DOWNLOAD SERVICE: About to call apiClient.startDownload with:', unsavedFacilities);
            const data = await window.apiClient.startDownload(unsavedFacilities);
            console.log('DOWNLOAD SERVICE: Received response:', data);

            if (data && data.success === false && data.code === 'ALREADY_RUNNING') {
                window.uiManager?.showProgress(data.message || 'A download is already in progress.', { showActivity: false });
                return data;
            }

            if (data?.success) {
                console.log('Download started, beginning progress polling');
                
                // Start real-time polling for progress updates
                window.downloadPoller?.startPolling();
                
                return data;
            } else {
                const emsg = (data && data.message) ? data.message : 'Download failed';
                throw new Error(emsg);
            }
        } catch (error) {
            console.error('DOWNLOAD SERVICE: Download error:', error);
            let errorMessage = 'Download failed. Please try again.';
            if (error?.message) errorMessage = `Download failed: ${error.message}`;
            
            window.uiManager?.showProgress(errorMessage, { showActivity: false });
            
            throw error;
        } finally {
            this.isDownloading = false;
            window.uiManager?.setSaveButtonProcessing(false);
        }
    }

    getDownloadState() {
        return { 
            isDownloading: this.isDownloading,
            isPolling: window.downloadPoller?.isActive() || false
        };
    }

    async checkProgress() {
        return window.downloadPoller?.checkProgress() || null;
    }

    stopProgress() {
        console.log('stopProgress called');
        window.downloadPoller?.stopPolling();
    }
}

window.downloadService = new DownloadService();
