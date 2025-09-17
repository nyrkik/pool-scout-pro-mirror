// Find the show() method and replace just the problematic section
// Change this line in the original modal:
// this.currentFacilityData = { ...reportData, index: index };
// To happen AFTER loadManagementCompanies() completes

async show(index) {
    const currentResults = window.searchService.getCurrentResults();
    const reportData = currentResults[index];

    if (!reportData) return;

    // Close any existing modal first
    this.close();

    // Load management companies first
    await this.loadManagementCompanies();

    // THEN store the data (after async operation completes)
    this.currentFacilityData = { ...reportData, index: index };

    const modalHtml = this._buildModalHtml(reportData);
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Add event listeners...
}
