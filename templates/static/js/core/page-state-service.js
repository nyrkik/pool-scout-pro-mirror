/**
 * Page State Service - Pool Scout Pro
 *
 * Manages page state and saved report counts for date selection.
 * Handles initialization, date changes, and count updates without interfering with user inputs.
 *
 * Dependencies:
 * - window.apiClient (for API calls)
 * - window.uiManager (for UI updates)
 * - window.utils (for date validation)
 */

class PageStateService {
    constructor() {
        this.isInitialized = false;
        this.currentDate = null;
    }

    /**
     * Check if service and dependencies are ready
     */
    _validateDependencies() {
        const missing = [];
        if (!window.apiClient) missing.push('apiClient');
        if (!window.uiManager) missing.push('uiManager');
        if (!window.utils) missing.push('utils');

        if (missing.length > 0) {
            console.error(`PageStateService missing dependencies: ${missing.join(', ')}`);
            return false;
        }
        return true;
    }

    /**
     * Check if service is initialized
     */
    _ensureInitialized(methodName) {
        if (!this.isInitialized) {
            console.error(`PageStateService.${methodName}() called before initialization`);
            return false;
        }
        if (!this._validateDependencies()) {
            return false;
        }
        return true;
    }

    /**
     * Initialize page on load - sets date to today and loads initial counts
     * Only called once on page load/refresh
     */
    /**
     * Initialize page on load - sets date to today and loads initial counts
     * Only called once on page load/refresh
     */
    async initializePage() {
        if (this.isInitialized) {
            console.log('Page already initialized');
            return;
        }

        if (!this._validateDependencies()) {
            console.error('Cannot initialize PageStateService - missing dependencies');
            return;
        }

        try {
            // Wait for DOM to be ready
            await this._waitForDateInput();

            const dateInput = document.getElementById('searchDate');
            if (!dateInput) {
                console.error('Date input element not found after waiting - cannot initialize');
                return;
            }

            // Set date to today (only time we modify the date input)
            const todayDate = window.utils.getTodayDate();
            dateInput.value = todayDate;
            this.currentDate = todayDate;
            this.isInitialized = true; // Set before calling updateSavedCount

            // Load saved count for today
            await this.updateSavedCount(todayDate);

            // Set up date change listener

            this.isInitialized = true;
            console.log(`✅ PageStateService initialized with date: ${todayDate}`);

        } catch (error) {
            console.error('Failed to initialize PageStateService:', error);
            if (window.uiManager) {
                window.uiManager.showProgress('Failed to initialize page state');
            }
        }
    }

    /**
     * Wait for date input element to be available in DOM
     */
    async _waitForDateInput() {
        return new Promise((resolve, reject) => {
            const maxAttempts = 20; // 2 seconds max
            let attempts = 0;

            const checkElement = () => {
                const dateInput = document.getElementById('searchDate');
                if (dateInput) {
                    resolve();
                    return;
                }

                attempts++;
                if (attempts >= maxAttempts) {
                    reject(new Error('Date input element not found after 2 seconds'));
                    return;
                }

                setTimeout(checkElement, 100);
            };

            checkElement();
        });
    }

    /**
     * Handle date input changes - reads date and updates counts
     */
    async handleDateChange() {
        if (!this._ensureInitialized('handleDateChange')) {
            return;
        }

        try {
            const newDate = this.getCurrentDate();
            if (!newDate) {
                this.clearCounts();
                return;
            }

            if (!window.utils.isValidDate(newDate)) {
                window.uiManager.showProgress('Please enter a valid date in YYYY-MM-DD format.');
                this.clearCounts();
                return;
            }

            this.currentDate = newDate;
            await this.updateSavedCount(newDate);
            console.log(`📅 Date changed to: ${newDate}`);

        } catch (error) {
            console.error('Error handling date change:', error);
            window.uiManager.showProgress('Failed to update counts for selected date');
            this.clearCounts();
        }
    }

    /**
     * Refresh current state - called by other services when they complete
     * Reads current date from input and updates counts
     */
    async refreshCurrentState() {
        if (!this._ensureInitialized('refreshCurrentState')) {
            return;
        }

        try {
            const currentDate = this.getCurrentDate();
            if (currentDate && window.utils.isValidDate(currentDate)) {
                await this.updateSavedCount(currentDate);
                console.log(`🔄 Refreshed state for date: ${currentDate}`);
            }
        } catch (error) {
            console.error('Error refreshing current state:', error);
            // Don't show user error message for background refresh failures
        }
    }

    /**
     * Update saved count display for specific date
     */
    async updateSavedCount(date) {
        if (!this._ensureInitialized('updateSavedCount')) {
            return;
        }

        try {
            const response = await window.apiClient.getExistingReportsForDate(date);

            if (response?.success) {
                const savedCount = response.facilities?.length || 0;

                // Update only the saved count, keep found count as-is
                const currentFoundCount = this.getCurrentFoundCount();
                window.uiManager.updateResultsCounts(currentFoundCount, savedCount);
                window.uiManager.setCurrentSearchDate(date);

                // Load and display existing reports if any
                if (savedCount > 0) {
                    window.uiManager.renderSearchResults(response.facilities);
                } else {
                    window.uiManager.clearResults();
                }

                console.log(`📊 Updated saved count: ${savedCount} for ${date}`);
            } else {
                throw new Error(response?.error || 'Failed to get existing reports');
            }

        } catch (error) {
            console.error('Failed to update saved count:', error);
            window.uiManager.showProgress('Failed to load saved reports');
            this.clearCounts();
        }
    }

    /**
     * Get current date from input field
     */
    getCurrentDate() {
        const dateInput = document.getElementById('searchDate');
        return dateInput?.value || null;
    }

    /**
     * Get current found count from display
     */
    getCurrentFoundCount() {
        const foundElement = document.getElementById('results-count');
        return foundElement ? parseInt(foundElement.textContent) || 0 : 0;
    }

    /**
     * Clear all counts and results
     */
    clearCounts() {
        if (window.uiManager) {
            window.uiManager.updateResultsCounts(0, 0);
            window.uiManager.clearResults();
            window.uiManager.setCurrentSearchDate('-');
        }
    }

    /**
     * Get current page state
     */
    getState() {
        return {
            isInitialized: this.isInitialized,
            currentDate: this.currentDate,
            inputDate: this.getCurrentDate(),
            dependenciesReady: this._validateDependencies()
        };
    }
}
