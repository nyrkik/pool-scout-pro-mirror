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
       this.processedFacilities = new Set();
       this.prevStatuses = new Map();
       this.hasSeenActive = false;
       this.maxIdlePolls = 30; // Stop after 60 seconds of idle (30 * 2s)
       this.idlePollCount = 0;
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
       this.prevStatuses.clear();
       this.hasSeenActive = false;
       this.idlePollCount = 0;

       this.pollInterval = setInterval(() => {
           this.pollProgress();
       }, this.pollFrequency);

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
       this.prevStatuses.clear();
       this.hasSeenActive = false;
       this.idlePollCount = 0;
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
               this.currentErrors = 0;
           } else {
               throw new Error(data.error || 'Failed to get progress data');
           }

       } catch (error) {
           this.handlePollError(error);
       }
   }

   handleProgressUpdate(progressData) {
       this.lastProgressData = progressData;

       // Process facility status changes from the facilities array (not completed_facilities)
       if (progressData.facilities) {
           progressData.facilities.forEach(facilityData => {
               const inspection_id = facilityData.inspection_id;
               const currentStatus = this.prevStatuses.get(inspection_id) || "pending";
               
               // Only process if status actually changed
               if (currentStatus !== facilityData.status) {
                   this.prevStatuses.set(inspection_id, facilityData.status);
                   
                   if (facilityData.status === "completed") {
                       window.downloadUI?.handleFacilityCompleted(inspection_id, true);
                   } else if (facilityData.status === "failed") {
                       window.downloadUI?.handleFacilityCompleted(inspection_id, false);
                   }
               }
           });
       }
       
       // Add debug line here:
       console.log('DEBUG: hasSeenActive:', this.hasSeenActive, 'is_active:', progressData.is_active, 'status:', progressData.status);

       // Mark when backend reports active
       if (progressData.is_active) { 
           this.hasSeenActive = true; 
       }

       // Check if download is complete
       if (progressData.status === "completed" || (this.hasSeenActive && !progressData.is_active)) {
           console.log("Download completed, stopping polling");
           this.stopPolling();
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
