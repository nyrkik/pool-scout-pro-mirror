/**
* Search UI - Pool Scout Pro
* Manages the search user interface and interactions.
*/
class SearchUI {
 constructor() {
     this.searchButton = document.getElementById('searchButton');
     this.searchButtonText = this.searchButton?.querySelector('span');
     this.searchButtonIcon = this.searchButton?.querySelector('i');
     this.dateInput = document.getElementById('searchDate');
     this.isSearchMode = true; // true = Search, false = Save
     this.setupEventListeners();
 }

 setupEventListeners() {
     if (this.searchButton) {
         this.searchButton.addEventListener('click', () => this.handleSearchClick());
     }
     
     if (this.dateInput) {
         this.dateInput.addEventListener('change', () => this.handleDateChange());
     }
 }

 async handleDateChange() {
     if (!this.dateInput || !this.dateInput.value) {
         window.uiManager.clearResults();
         window.uiManager.setCurrentSearchDate('');
         return;
     }

     const searchDate = this.dateInput.value;
     window.uiManager.setCurrentSearchDate(searchDate);
     
     try {
         const data = await window.searchService.getExistingReports(searchDate);
         if (data && data.reports && data.reports.length > 0) {
             window.uiManager.renderSavedReports(data.reports);
             window.uiManager.updateResultsCounts(0, data.saved_count || 0);
         } else {
             window.uiManager.clearResults();
             window.uiManager.updateResultsCounts(0, 0);
         }
     } catch (error) {
         console.error("Failed to load existing reports:", error);
         window.uiManager.clearResults();
         window.uiManager.showProgress('Failed to load existing reports for this date.', {showActivity: false});
         setTimeout(() => window.uiManager.hideProgress(), 3000);
     }
 }

 async handleSearchClick() {
     if (!this.dateInput || !this.dateInput.value) {
         window.uiManager.showProgress('Please select a date first.', {showActivity: false});
         setTimeout(() => window.uiManager.hideProgress(), 3000);
         return;
     }

     if (this.isSearchMode) {
         await this.performSearch();
     } else {
         await this.performSave();
     }
 }

 async performSearch() {
     const searchDate = this.dateInput.value;
     this.setButtonState(false, 'Searching...', 'loader');
     window.uiManager.showProgress("Searching EMD Site...please wait", {showActivity: true});
     
     try {
         const data = await window.searchService.searchForReports(searchDate);
         if (data && data.facilities !== undefined) {
             const facilityCount = data.facilities.length;
             let message;
             
             if (facilityCount === 0) {
                 message = 'No new reports found';
             } else if (facilityCount === 1) {
                 message = '1 new report found';
             } else {
                 message = `${facilityCount} new reports found`;
             }
             
             window.uiManager.showProgress(message, {showActivity: false});
             setTimeout(() => window.uiManager.hideProgress(), 3000);
             
             // REMOVED: window.uiManager.updateUnsavedCount(facilityCount);
             // Let the download UI calculate correct badges from search results
             
             if (facilityCount > 0) {
                 window.uiManager.renderSearchResults(data.facilities);
                 // Calculate badges from actual search results after rendering
                 if (window.downloadUI) {
                     window.downloadUI.updateResultsCounts();
                 }
                 this.setButtonToSaveMode();
             } else {
                 this.setButtonToSearchMode();
             }
         } else {
             throw new Error("Invalid response from server.");
         }
     } catch (error) {
         console.error("Search failed:", error);
         window.uiManager.showProgress('Search failed or returned no results.', {showActivity: false});
         setTimeout(() => window.uiManager.hideProgress(), 3000);
         this.setButtonToSearchMode();
     }
 }

 async performSave() {
     this.setButtonState(false, 'Saving...', 'loader');
     
     try {
         if (window.downloadUI) {
             await window.downloadUI.handleSaveClick();
             this.setButtonToSearchMode();
         } else {
             throw new Error('Download service not available');
         }
     } catch (error) {
         console.error("Save failed:", error);
         this.setButtonToSaveMode();
     }
 }

 setButtonToSearchMode() {
     this.isSearchMode = true;
     this.setButtonState(true, 'Search', 'search');
 }

 setButtonToSaveMode() {
     this.isSearchMode = false;
     this.setButtonState(true, 'Save', 'save');
 }

 setButtonState(enabled, text, iconName) {
     if (this.searchButton) {
         this.searchButton.disabled = !enabled;
     }
     if (this.searchButtonText) {
         this.searchButtonText.textContent = text;
     }
     if (this.searchButtonIcon) {
         this.searchButtonIcon.setAttribute('data-lucide', iconName);
         if (window.lucide) {
             window.lucide.createIcons();
         }
     }
 }

 stopProgressAnimation() {
     // Placeholder for any cleanup logic
 }
}

window.searchUI = new SearchUI();
