/**
 * Enhanced Date Utilities - Pool Scout Pro
 * 
 * Centralized date conversion and validation for all system formats.
 * Handles conversions between Frontend (YYYY-MM-DD), EMD (MM/DD/YYYY), 
 * Database (MM/DD/YYYY), and Filename (YYYYMMDD) formats.
 */

class DateUtilities {
    /**
     * Convert frontend date (YYYY-MM-DD) to EMD format (MM/DD/YYYY)
     */
    static frontendToEmd(frontendDate) {
        try {
            const [year, month, day] = frontendDate.split('-');
            return `${month}/${day}/${year}`;
        } catch (error) {
            throw new Error(`Invalid frontend date format: ${frontendDate}`);
        }
    }

    /**
     * Convert EMD/Database date (MM/DD/YYYY) to frontend format (YYYY-MM-DD)
     */
    static emdToFrontend(emdDate) {
        try {
            const [month, day, year] = emdDate.split('/');
            return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
        } catch (error) {
            throw new Error(`Invalid EMD date format: ${emdDate}`);
        }
    }

    /**
     * Convert any date to database format (MM/DD/YYYY)
     */
    static toDatabase(dateStr) {
        if (dateStr.includes('/')) {
            return dateStr; // Already in MM/DD/YYYY format
        }
        if (dateStr.includes('-')) {
            return this.frontendToEmd(dateStr); // Convert YYYY-MM-DD to MM/DD/YYYY
        }
        throw new Error(`Unknown date format: ${dateStr}`);
    }

    /**
     * Convert any date to frontend format (YYYY-MM-DD)
     */
    static toFrontend(dateStr) {
        if (dateStr.includes('-')) {
            return dateStr; // Already in YYYY-MM-DD format
        }
        if (dateStr.includes('/')) {
            return this.emdToFrontend(dateStr); // Convert MM/DD/YYYY to YYYY-MM-DD
        }
        throw new Error(`Unknown date format: ${dateStr}`);
    }

    /**
     * Convert frontend date to filename format (YYYYMMDD)
     */
    static toFilename(frontendDate) {
        try {
            return frontendDate.replace(/-/g, '');
        } catch (error) {
            throw new Error(`Invalid date for filename: ${frontendDate}`);
        }
    }

    /**
     * Normalize date for database comparison - always returns MM/DD/YYYY
     */
    static normalizeForComparison(dateStr) {
        return this.toDatabase(dateStr);
    }

    /**
     * Check if two dates are the same regardless of format
     */
    static datesEqual(date1, date2) {
        try {
            const normalized1 = this.normalizeForComparison(date1);
            const normalized2 = this.normalizeForComparison(date2);
            return normalized1 === normalized2;
        } catch (error) {
            return false;
        }
    }

    static isValidDate(dateString) {
        if (!dateString) return false;

        // Check YYYY-MM-DD format
        const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
        if (!dateRegex.test(dateString)) return false;

        // Check if it's a valid date
        const date = new Date(dateString);
        return date instanceof Date && !isNaN(date) && dateString === date.toISOString().split('T')[0];
    }

    static getTodayDate() {
        const today = new Date();
        const year = today.getFullYear();
        const month = String(today.getMonth() + 1).padStart(2, '0');
        const day = String(today.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    static normalizeName(name) {
        return name.toLowerCase().trim().replace(/\s+/g, ' ');
    }

    static debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    static formatTimestamp() {
        return new Date().toISOString();
    }

    static sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Global utilities
window.utils = DateUtilities;
