PROJECT OVERVIEW
Sacramento County pool inspection automation system - EMD website search, PDF download, data extraction, compliance management.

MILESTONE MAINTENANCE INSTRUCTIONS FOR FUTURE CHATS
This milestone contains ONLY:
✅ Project structure and file purposes
✅ Development rules and standards
✅ System capabilities and configuration
✅ Deployment procedures
✅ Identified issues requiring attention

Do NOT add to this milestone:
❌ Resolved issues (transient information)
❌ Temporary status updates
❌ "Next phase priorities" or similar changing content
❌ Backup files, enhanced files, or dated suffixes in structure

UPDATE the file structure section whenever files are added/removed from the project.

PROJECT STRUCTURE - VERIFIED AND CLEANED
sapphire/pool_scout_pro/
├── backups/                          # Automated code backups (external to project)
├── config/                           # Configuration files
├── data/                            # Local data storage
│   ├── logs/                        # Application logs
│   ├── milestones/                  # Project milestone tracking
│   └── source_code/                 # Generated source code documentation
├── scripts/                         # Utility scripts
├── src/                            # Python source code
│   ├── core/                       # Core utilities and database
│   │   ├── browser.py              # Selenium WebDriver management
│   │   ├── database.py             # SQLite database connection and schema
│   │   ├── error_handler.py        # Centralized error handling and logging
│   │   ├── settings.py             # Configuration management
│   │   └── utilities.py            # Date, name, file, text utility functions
│   ├── services/                   # Business logic services
│   │   ├── database_service.py     # Database operations and queries
│   │   ├── download_lock_service.py # Single-flight download protection
│   │   ├── duplicate_prevention_service.py # Duplicate detection logic
│   │   ├── failed_download_service.py # Failed download tracking for retry
│   │   ├── pdf_downloader.py       # PDF download with transactional processing
│   │   ├── pdf_extractor.py        # PDF text extraction and database storage
│   │   ├── retry_service.py        # Background retry processing
│   │   ├── search_progress_service.py # Search progress tracking
│   │   ├── search_service.py       # EMD website search functionality
│   │   └── violation_severity_service.py # Violation severity analysis
│   └── web/                        # Flask web application
│       ├── app.py                  # Main Flask application with enterprise logging
│       ├── routes/                 # API and web routes
│       │   ├── api_routes.py       # Main API endpoints
│       │   └── downloads.py        # Download API endpoints
│       └── shared/                 # Shared web services
│           └── services.py         # Service factory and dependency injection
├── temp/                           # Temporary files
├── templates/                      # HTML templates and static assets
│   ├── search_reports.html         # Main search interface with sticky header design
│   └── static/                     # CSS, JavaScript, and media files
│       ├── css/
│       │   └── search_reports.css  # Responsive design with sticky search controls
│       └── js/
│           ├── core/               # Core JavaScript utilities
│           │   ├── api-client.js   # API communication layer
│           │   ├── ui-manager.js   # UI state management and display_address handling
│           │   ├── utilities.js    # Frontend utility functions
│           │   └── violation-modal.js # Violation detail modal
│           ├── downloads/          # Download management
│           │   ├── download-service.js # Download request handling
│           │   └── download-ui.js  # Download progress UI framework
│           ├── search/             # Search functionality
│           │   ├── search-service.js # Search API communication with display_address
│           │   └── search-ui.js    # Search interface management
│           └── main.js             # Main application initialization
├── trash/                          # Archive directory
└── venv/                          # Python virtual environment

MANDATORY DEVELOPMENT RULES (STRICTLY ENFORCED)

Project Cleanliness Rules
❌ NO backup files in project directories - use external backup systems only
❌ NO files with suffixes like: _backup, _enhanced, _fixed, _updated, _v2, etc.
❌ NO timestamp suffixes on active files (20250813_, etc.)
❌ NO duplicate files with similar names or purposes
✅ Clean, descriptive filenames that indicate purpose only
✅ Use external backup systems (Git, automated backups/ folder)
✅ Delete old files completely rather than renaming with suffixes
✅ One file per purpose - no duplicates allowed in project structure

File Structure Maintenance
✅ Update this milestone file structure section whenever files are added/removed
✅ Verify file locations match their logical purpose
✅ Ensure all referenced files in imports/templates actually exist
✅ Run cleanup scans regularly to prevent backup file accumulation

Code Update Strategy
❌ NO surgical code changes - leads to wasted time hunting syntax errors
❌ NO partial snippets or incomplete edits
❌ NO sed commands - breaks code syntax and indentation
❌ NO code generation without user permission - always ask first
❌ NO assumptions or "improvements" to working code - preserve exact logic
✅ Complete file rewrites using cat > filename << 'EOF'
✅ Complete functions/modules/classes as full units
✅ Terminal-ready commands for immediate copy/paste execution
✅ Targeted section replacements using cat with head/tail when appropriate

Service Boundaries (ENFORCED)
❌ NO business logic in route files - routes call services only
❌ NO mixed service concerns - one service, one responsibility
❌ NO "convenient" shortcuts - maintain clean boundaries
❌ NO code generation without backup - always backup before changes
✅ Services have single, clear purpose
✅ Easy to debug - problems isolated to correct service
✅ Clean separation of concerns
✅ No quick fixes or expedient shortcuts - all solutions must be enterprise-ready
✅ Architecture quality over delivery speed - proper solution design required
✅ Best practices mandatory - no sacrificing code quality for rapid implementation
✅ Clear file header documentation - every file must have purpose and dependencies documented
✅ File headers must explain: what the service does, key responsibilities, external dependencies
✅ No generic comments - documentation must be specific and actionable for developers

DATABASE STRUCTURE
facilities table:
- id INTEGER PRIMARY KEY AUTOINCREMENT
- name TEXT NOT NULL
- establishment_id TEXT
- permit_holder TEXT
- phone TEXT
- city TEXT
- zip_code TEXT
- program_identifier TEXT
- policy_announcements TEXT
- equipment_approvals TEXT
- facility_comments TEXT
- management_company_id INTEGER
- current_operational_status TEXT DEFAULT 'open'
- created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
- facility_type TEXT DEFAULT 'POOL'
- street_address TEXT
- state TEXT DEFAULT 'CA'

inspection_reports table - stores inspection report data with pdf_filename as unique identifier
violations table - stores violation details
pool_equipment table - stores equipment specifications
water_chemistry table - stores water test results
failed_downloads table - stores failed downloads for automatic retry

ADDRESS HANDLING ARCHITECTURE
Database Storage: Structured components (street_address, city, state, zip_code)
Frontend Display: Computed display_address field ("Street, City" format)
PDF Extraction: Multi-line parsing with "Facility City" and "Facility ZIP" artifact removal
Search Results: EMD provides complete address converted to display_address format
Separation of Concerns: Persistent structured data vs temporary display formatting

SYSTEM CAPABILITIES AND CONFIGURATION

Network Configuration
- Internal: 127.0.0.1:7001 (Gunicorn)
- Local HTTP: http://10.10.10.80/ (Nginx proxy)
- External HTTPS: https://sapphire-pools.dyndns.org/ (Standard port 443)
- Container: localhost:4444 (Selenium Firefox)
- NAS IP: 10.10.10.70
- NAS Share: //10.10.10.70/homes/brian/pool_scout_pro/data
- Server Mount: /mnt/nas-pool-data/
- PDF Storage: /mnt/nas-pool-data/reports/2025/

Port Configuration
- 80: HTTP (nginx) → HTTPS redirect
- 443: HTTPS (nginx) → proxy to gunicorn:7001
- 7001: Pool Scout Pro (gunicorn) - Timeout increased to 600s
- 7002: PT360 (gunicorn)
- 4444: Selenium WebDriver
- 7900: Selenium VNC access
- 22: SSH (via router port 2222)

Firewall Rules (UFW)
- OpenSSH: SSH access (port 22)
- 80/tcp: HTTP for nginx
- 443/tcp: HTTPS for nginx
- 445/tcp + 139/tcp: SMB/NetBIOS for NAS access (local LAN only)
- 7001: Pool Scout Pro internal access (127.0.0.1 and 10.10.10.0/24)
- 7002: PT360 internal access (127.0.0.1 and 10.10.10.0/24)

Timeout Configuration
- Gunicorn timeout: 600 seconds (10 minutes) for long downloads
- Nginx proxy_read_timeout: 600 seconds
- Nginx proxy_connect_timeout: 60 seconds
- Nginx proxy_send_timeout: 600 seconds

Active Services
- pool-scout-pro.service: ACTIVE (enterprise-ready with 10min timeouts)
- nginx.service: ACTIVE (configured for long downloads)
- pool-scout-health.timer: ACTIVE
- pool-scout-retry.timer: ACTIVE (enterprise retry system)
- selenium-firefox: AUTO-MANAGED (Docker)

Operational Systems
- EMD Search: Working - Date conversion with Pacific timezone, result extraction, correct date filtering
- PDF Download Backend: Working - Browser navigation, PDF link extraction, file storage with human-like timing, transactional processing
- PDF Text Extraction: Working - pypdfium2 integration with structured address parsing
- Database Storage: Working - Complete schema with structured address components
- UI System: Working - Sticky header design, responsive layout, clean address display
- Infrastructure: Active - Gunicorn, Nginx, health monitoring, timeout protection
- External HTTPS Access: Working - Standard port 443, clean URLs
- Local Network Access: Working - Direct IP access on port 80
- Failed Download Retry System: Working - Enterprise retry service with automatic processing

Enterprise Retry System
- failed_downloads table: Database table for tracking failed downloads
- FailedDownloadService: Service for managing retry logic with exponential backoff
- RetryService: Background service for automatic retry processing
- pool-scout-retry.timer: Systemd timer running every 15 minutes
- Trigger mechanism: Event-driven via /tmp/pool_scout_retry_needed file
- Health monitoring: JSON status files for operational monitoring
- Automatic cleanup: Removes old retry records after 7 days

Filename Format
- Current Implementation: YYYYMMDD_FACILITYNAME_SHORTID.pdf
- Example: 20250808_CRESTVIEWTOWNHOUSES_DDE1E71B5B38.pdf
- Date Source: Search date (inspection_date) passed from search service
- ID Extraction: Last segment after final dash in inspection ID
- Uniqueness: Naturally unique across dates and facilities

Timezone Handling
- Server Timezone: UTC
- EMD Timezone: America/Los_Angeles (Pacific)
- Conversion Method: DateUtilities.convert_to_pacific_date()
- Dependencies: pytz library required

User Interface Architecture
- Sticky Search Controls: Search form and table header remain fixed during scroll
- Responsive Design: Mobile-friendly navigation and layout adaptation
- Address Display: Consistent "Street, City" format across all interfaces
- Progress Indicators: Framework ready for real-time download progress
- Status Management: Clear separation between Found (search) and On File (saved) counts

DEPLOYMENT PROCEDURES
```bash
./manage.sh start    # Start system
./manage.sh status   # Check status
./manage.sh logs     # View logs
./manage.sh restart  # Restart services
```

Dependencies
Python: selenium, pytz, pypdfium2, requests, flask, gunicorn, aiohttp
System: docker (for Selenium), nginx, systemd
Storage: CIFS mount to NAS

IDENTIFIED ISSUES REQUIRING ATTENTION

Download Progress System Implementation
- Problem: No real-time progress indicators during downloads
- Impact: Poor user experience during long download operations
- Technical: Backend download system lacks progress reporting endpoints
- Framework: Frontend progress UI exists but not connected to backend status
- Priority: HIGH - Essential for user feedback during multi-facility downloads

Database Query Optimization
- Problem: Search results may show multiple reports per facility instead of unique facilities
- Impact: User confusion about actual facility count vs report count
- Evidence: 37 search results for 20 unique facilities suggests duplicate display
- Analysis Required: Determine if multiple reports per facility should show separately or be grouped
- Priority: MEDIUM - Affects data presentation clarity

Duplicate Prevention Service Boundaries
- Problem: Service mixing concerns between download prevention and UI display
- Impact: Confusion about which system determines "saved" status
- Architecture: Download prevention should only prevent duplicates, not set UI status
- Separation Required: Frontend should determine saved status by comparing data sources
- Priority: MEDIUM - Clean architecture separation needed

SOURCE CODE DOCUMENTATION GENERATION

When this milestone is uploaded to a new chat, the user likely wants to generate the complete source code documentation for project understanding. Ask if they want to generate this documentation before proceeding with other tasks.

The source code documentation script extracts all project files from src/ and templates/ directories into a single markdown file for easy upload and complete project understanding.

Command to generate (saves to data/source_code/ directory):
```bash
cd sapphire/pool_scout_pro/
OUTPUT_FILE="data/source_code/pool_scout_pro_complete_code_$(date +%Y%m%d_%H%M%S).md"

cat > "$OUTPUT_FILE" << 'HEADER'
# Pool Scout Pro - Complete Source Code Documentation
Generated: $(date '+%Y-%m-%d %H:%M:%S')
Project: Sacramento County Pool Inspection Automation System

## Table of Contents
- Python Source Code (src/)
- Web Templates and Assets (templates/)

---

HEADER

echo "## Python Source Code (src/)" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Core utilities and database
for file in src/core/browser.py src/core/database.py src/core/error_handler.py src/core/settings.py src/core/utilities.py; do
    if [[ -f "$file" ]]; then
        echo "### $file" >> "$OUTPUT_FILE"
        echo '```python' >> "$OUTPUT_FILE"
        cat "$file" >> "$OUTPUT_FILE"
        echo '```' >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"
    fi
done

# Business logic services
for file in src/services/database_service.py src/services/download_lock_service.py src/services/duplicate_prevention_service.py src/services/failed_download_service.py src/services/pdf_downloader.py src/services/pdf_extractor.py src/services/retry_service.py src/services/search_progress_service.py src/services/search_service.py src/services/violation_severity_service.py; do
    if [[ -f "$file" ]]; then
        echo "### $file" >> "$OUTPUT_FILE"
        echo '```python' >> "$OUTPUT_FILE"
        cat "$file" >> "$OUTPUT_FILE"
        echo '```' >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"
    fi
done

# Flask web application
echo "### src/web/app.py" >> "$OUTPUT_FILE"
echo '```python' >> "$OUTPUT_FILE"
cat "src/web/app.py" >> "$OUTPUT_FILE"
echo '```' >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# API and web routes
for file in src/web/routes/api_routes.py src/web/routes/downloads.py; do
    if [[ -f "$file" ]]; then
        echo "### $file" >> "$OUTPUT_FILE"
        echo '```python' >> "$OUTPUT_FILE"
        cat "$file" >> "$OUTPUT_FILE"
        echo '```' >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"
    fi
done

# Shared web services
echo "### src/web/shared/services.py" >> "$OUTPUT_FILE"
echo '```python' >> "$OUTPUT_FILE"
cat "src/web/shared/services.py" >> "$OUTPUT_FILE"
echo '```' >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

echo "## Web Templates and Assets (templates/)" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# HTML templates
echo "### templates/search_reports.html" >> "$OUTPUT_FILE"
echo '```html' >> "$OUTPUT_FILE"
cat "templates/search_reports.html" >> "$OUTPUT_FILE"
echo '```' >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# CSS files
echo "### templates/static/css/search_reports.css" >> "$OUTPUT_FILE"
echo '```css' >> "$OUTPUT_FILE"
cat "templates/static/css/search_reports.css" >> "$OUTPUT_FILE"
echo '```' >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Core JavaScript utilities
for file in templates/static/js/core/api-client.js templates/static/js/core/ui-manager.js templates/static/js/core/utilities.js templates/static/js/core/violation-modal.js; do
    if [[ -f "$file" ]]; then
        echo "### $file" >> "$OUTPUT_FILE"
        echo '```javascript' >> "$OUTPUT_FILE"
        cat "$file" >> "$OUTPUT_FILE"
        echo '```' >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"
    fi
done

# Download management JavaScript
for file in templates/static/js/downloads/download-service.js templates/static/js/downloads/download-ui.js; do
    if [[ -f "$file" ]]; then
        echo "### $file" >> "$OUTPUT_FILE"
        echo '```javascript' >> "$OUTPUT_FILE"
        cat "$file" >> "$OUTPUT_FILE"
        echo '```' >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"
    fi
done

# Search functionality JavaScript
for file in templates/static/js/search/search-service.js templates/static/js/search/search-ui.js; do
    if [[ -f "$file" ]]; then
        echo "### $file" >> "$OUTPUT_FILE"
        echo '```javascript' >> "$OUTPUT_FILE"
        cat "$file" >> "$OUTPUT_FILE"
        echo '```' >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"
    fi
done

# Main application JavaScript
echo "### templates/static/js/main.js" >> "$OUTPUT_FILE"
echo '```javascript' >> "$OUTPUT_FILE"
cat "templates/static/js/main.js" >> "$OUTPUT_FILE"
echo '```' >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Footer
cat >> "$OUTPUT_FILE" << 'FOOTER'

---
## Generation Complete

This document contains all source code from the Pool Scout Pro project's src/ and templates/ directories as specified in the milestone document.

**File Count Summary:**
- Python Core: 5 files (browser.py, database.py, error_handler.py, settings.py, utilities.py)
- Python Services: 10 files (database_service.py through violation_severity_service.py)
- Flask Web: 4 files (app.py, routes/, shared/services.py)
- Templates: 1 HTML file (search_reports.html)
- CSS: 1 file (search_reports.css)
- JavaScript: 9 files (core/, downloads/, search/, main.js)

**Total: 30 project files**

Generated from milestone-verified project structure.
FOOTER

echo "✅ Code documentation generated: $OUTPUT_FILE"
echo "📊 Contains all source files from src/ and templates/ directories"
echo "🎯 Ready for upload to provide complete project understanding"
```

This generates a comprehensive markdown file with all project source code that can be uploaded for complete project understanding.
