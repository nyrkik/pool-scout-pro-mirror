/**
* Enhanced Download UI - Pool Scout Pro
* Real-time download feedback with visual state management using inspection_id
*/
class DownloadUI {
   constructor() {
       this.progressContainer = document.getElementById('download-progress-container');
       this.progressList = document.getElementById('download-progress-list');
       this.downloadStates = new Map(); // Track by inspection_id instead of index
       this.totalCount = 0;
       this.completedCount = 0;
       this.failedCount = 0;
   }

   async handleSaveClick() {
       try {
           const currentResults = window.searchService.getCurrentResults();
           const unsaved = currentResults.filter(f => !f.saved);
           
           // Initialize tracking for unsaved facilities
           this.initializeDownloadTracking(unsaved);
           
           // Start download with filtered unsaved facilities
           await window.downloadService.startDownload(unsaved);
           
           // Let polling handle all state changes - facilities stay orange until backend processes them
           
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
           const inspection_id = facility.inspection_id;
           if (inspection_id) {
               this.downloadStates.set(inspection_id, {
                   name: facility.name,
                   status: 'pending', // pending -> downloading -> completed/failed
                   facility: facility
               });
           }
       });

       this.updateProgressMessage();
   }

   updateFacilityRowState(inspection_id, status) {
       const row = document.querySelector(`#reports-table-body tr[data-inspection-id="${inspection_id}"]`);
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

   handleFacilityCompleted(inspection_id, success = true) {
       const state = this.downloadStates.get(inspection_id);
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
       this.updateFacilityRowState(inspection_id, success ? 'completed' : 'failed');

       // Update the original search results data
       const currentResults = window.searchService.getCurrentResults();
       const facilityIndex = currentResults.findIndex(f => f.inspection_id === inspection_id);
       if (facilityIndex !== -1) {
           currentResults[facilityIndex].saved = success;
           
           // Re-render the findings cell for this facility
           const row = document.querySelector(`#reports-table-body tr[data-inspection-id="${inspection_id}"]`);
           if (row) {
               const findingsCell = row.cells[3]; // 4th column (0-indexed)
               findingsCell.innerHTML = window.uiManager.renderTopFindings(currentResults[facilityIndex], facilityIndex);
           }
       }

       // Update in-memory facility data (keep for compatibility)
       const facility = state.facility;
       if (facility) {
           facility.saved = success;
       }

       // Update progress message
       this.updateProgressMessage();

       // Update badge counts in real-time after each facility completes
       this.updateResultsCounts();

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

       // Final badge count update (redundant but ensures accuracy)
       this.updateResultsCounts();
   }

   updateResultsCounts() {
       // FIXED: Use search results directly instead of separate database API call
       const currentResults = window.searchService.getCurrentResults();
       const savedCount = currentResults.filter(f => f.saved === true).length;
       const unsavedCount = currentResults.filter(f => !f.saved).length;
       
       window.uiManager?.updateResultsCounts(unsavedCount, savedCount);
   }

   resetFacilityStates() {
       // Reset all facilities back to unsaved state on error
       this.downloadStates.forEach((state, inspection_id) => {
           this.updateFacilityRowState(inspection_id, 'unsaved');
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
           this.handleFacilityCompleted(progressData.last_completed.inspection_id, true);
       }

       // Handle failed facility updates if provided
       if (progressData.last_failed) {
           this.handleFacilityCompleted(progressData.last_failed.inspection_id, false);
       }
   }

   updateMainTableRow(completed) {
       // Legacy method - now handled by handleFacilityCompleted
       this.handleFacilityCompleted(completed.inspection_id, true);
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
