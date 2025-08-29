/**
 * Search Service - Pool Scout Pro
 * 
 * Handles search API calls to the Flask backend.
 * The actual EMD automation happens in Python - this just makes the API requests.
 * 
 * Dependencies:
 * - window.apiClient (for API calls)
 */

class SearchService {
    constructor() {
        this.isSearching = false;
        this.currentResults = [];
    }

    async searchForReports(date) {
        if (this.isSearching) {
            console.log('Search already in progress, aborting');
            return;
        }

        this.isSearching = true;

        try {
            const response = await fetch('/api/v1/reports/search-with-duplicates', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    start_date: date,
                    end_date: date
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            // DEBUG: Log the API response
            console.log('API Response:', data);
            if (data.facilities && data.facilities.length > 0) {
                console.log('First facility saved property:', data.facilities[0].saved);
                console.log('All facilities saved status:', data.facilities.map(f => ({name: f.name, saved: f.saved})));
            }

            if (data.success) {
                this.currentResults = data.facilities || [];
                
                // DEBUG: Log what's stored in currentResults
                console.log('currentResults saved status:', this.currentResults.map(f => ({name: f.name, saved: f.saved})));
                
                return data;
            } else {
                throw new Error(data.message || 'Search failed');
            }

        } finally {
            this.isSearching = false;
        }
    }

    async getExistingReports(date) {
        try {
            const response = await fetch('/api/v1/reports/existing-for-date', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    date: date
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            if (data.success) {
                return data;
            } else {
                throw new Error(data.message || 'Failed to get existing reports');
            }

        } catch (error) {
            console.error('Error getting existing reports:', error);
            throw error;
        }
    }

    getCurrentResults() {
        console.log('getCurrentResults called, returning:', this.currentResults.map(f => ({name: f.name, saved: f.saved})));
        return this.currentResults;
    }

    updateCurrentResults(newResults) {
        this.currentResults = newResults;
    }
}

window.searchService = new SearchService();
