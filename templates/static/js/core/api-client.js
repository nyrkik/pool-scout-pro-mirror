/**
 * API Client - Pool Scout Pro
 * 
 * Handles all communication with the Flask backend API.
 * CLEAN VERSION: Eliminates separate duplicate checking - search APIs return complete data.
 */

class ApiClient {
    constructor() {
        this.baseUrl = '';
    }

    async searchWithDuplicates(startDate, endDate) {
        const response = await fetch('/api/v1/reports/search-with-duplicates', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                start_date: startDate,
                end_date: endDate
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();
    }

    async startDownload(facilities) {
        console.log('🚀 API CLIENT: startDownload called with', facilities.length, 'facilities');
        
        try {
            console.log('📤 API CLIENT: About to make fetch request to /api/v1/downloads/start');
            
            const response = await fetch('/api/v1/downloads/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    facilities: facilities
                })
            });

            console.log('📨 API CLIENT: Fetch response received, status:', response.status);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            console.log('✅ API CLIENT: Download response:', result);
            return result;
            
        } catch (error) {
            console.error('💥 API CLIENT: startDownload error:', error);
            throw error;
        }
    }

    async getExistingReportsForDate(date) {
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

        return await response.json();
    }

    async getSystemStatus() {
        const response = await fetch('/api/status');

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();
    }

    async getSearchEstimate() {
        const response = await fetch('/api/v1/estimate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();
    }
}

// Initialize global instance
window.apiClient = new ApiClient();
