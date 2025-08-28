/**
 * Pool Scout Pro - Main Application Coordinator
 * * Single responsibility: Initialize services and coordinate application startup.
 */

let appInitialized = false;

/**
 * Initialize all application services in correct dependency order
 */
function initializeApplication() {
    try {
        console.log('Initializing Pool Scout Pro services...');

        // Initialize core UI services
        if (!window.searchUI) {
            window.searchUI = new SearchUI();
        }

        if (!window.downloadUI) {
            window.downloadUI = new DownloadUI();
        }


        // Initialize page state service after dependencies are ready
        if (!window.pageStateService) {
            window.pageStateService = new PageStateService();
        }

        // Initialize page state service and page
        if (window.pageStateService) {
            window.pageStateService.initializePage();
        }

        // Initialize icons
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }

        appInitialized = true;
        console.log('✅ Pool Scout Pro initialized successfully');
        console.log('📊 Download progress system ready');

    } catch (error) {
        console.error('Initialization error:', error);
        if (window.uiManager) {
            window.uiManager.showProgress('Application failed to initialize. Please refresh.');
        }
    }
}

/**
 * Clean up resources when page unloads
 */
function cleanup() {
    console.log('Cleaning up application resources...');

    // Stop any running timers/animations
    if (window.searchUI) {
    }

    // Stop download polling
    if (window.downloadPoller) {
        window.downloadPoller.stopPolling();
    }

    console.log('Cleanup completed');
}

/**
 * Handle page visibility changes for performance optimization
 */
function handleVisibilityChange() {
    if (document.hidden) {
        console.log('Page hidden - reducing activity');
        // Don't stop download polling when page is hidden - downloads should continue
    } else {
        console.log('Page visible - resuming normal operation');
        // Resume normal operations
    }
}

// Event Listeners
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded - preparing application...');

    // Small delay to ensure all DOM elements are ready
    setTimeout(initializeApplication, 150);
});

window.addEventListener('beforeunload', cleanup);
document.addEventListener('visibilitychange', handleVisibilityChange);

// Global application state accessor
window.poolScoutPro = {
    isInitialized: () => appInitialized,
    version: '1.0',
    cleanup: cleanup,
    getDownloadState: () => window.downloadService ? window.downloadService.getDownloadState() : null
};

// Legacy function stubs for HTML onclick handlers
function showAbout() {
    alert('Pool Scout Pro - Sacramento County Pool Inspection Tool\nVersion 1.0\n\n✨ Features real-time download progress!');
}

function showHelp() {
    alert('Help:\n1. Select a date\n2. Click Search\n3. Watch progress bar\n4. Click Save to download reports\n5. Watch real-time download progress!');
}

function showSettings() {
    alert('Settings coming soon...');
}

function toggleFindings(facilityIndex) {
    if (window.violationModal) {
        window.violationModal.show(facilityIndex);
    }
}

/**
 * Show full report details popup
 * Called when user clicks on facility name
 */
function showFullReport(facilityIndex) {
    if (window.violationModal) {
        window.violationModal.show(facilityIndex);
    } else {
        // Fallback for basic info
        const currentResults = window.searchService ? window.searchService.getCurrentResults() : [];
        const facility = currentResults[facilityIndex];

        if (facility) {
            alert(`${facility.name}\n${facility.display_address || 'Address not available'}\nInspection Date: ${facility.inspection_date || 'Unknown'}`);
        }
    }
}
