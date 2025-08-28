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
PROJECT STRUCTURE
sapphire/pool_scout_pro/
├── backups/                          # Automated code backups (external to project)
├── config/                           # Configuration files
├── data/                            # Local data storage
│   ├── logs/                        # Application logs
│   └── milestones/                  # Project milestone tracking
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
│   ├── search_reports.html         # Main search interface
│   └── static/                     # CSS, JavaScript, and media files
│       ├── css/
│       └── js/
│           ├── core/               # Core JavaScript utilities
│           │   ├── api-client.js   # API communication layer
│           │   ├── ui-manager.js   # UI state management
│           │   ├── utilities.js    # Frontend utility functions
│           │   └── violation-modal.js # Violation detail modal
│           ├── downloads/          # Download management
│           │   ├── download-service.js # Download request handling
│           │   └── download-ui.js  # Download progress UI
│           ├── search/             # Search functionality
│           │   ├── search-service.js # Search API communication
│           │   └── search-ui.js    # Search interface management
│           └── main.js             # Main application initialization
├── trash/                          # Archive directory
└── venv/                          # Python virtual environment
MANDATORY DEVELOPMENT RULES (STRICTLY ENFORCED)
Project Cleanliness Rules
❌ NO backup files in project directories - use external backup systems only
❌ NO files with suffixes like: _backup, _enhanced, _fixed, _updated, v2, etc.
❌ NO timestamp suffixes on active files (20250813, etc.)
❌ NO duplicate files with similar names (search-ui.js AND search/search-ui.js)
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
facilities table - stores facility information
inspection_reports table - stores inspection report data with pdf_filename as unique identifier
violations table - stores violation details
pool_equipment table - stores equipment specifications
water_chemistry table - stores water test results
failed_downloads table - stores failed downloads for automatic retry
SYSTEM CAPABILITIES AND CONFIGURATION
Network Configuration

Internal: 127.0.0.1:7001 (Gunicorn)
Local HTTP: http://10.10.10.80/ (Nginx proxy)
External HTTPS: https://sapphire-pools.dyndns.org/ (Standard port 443)
Container: localhost:4444 (Selenium Firefox)
NAS IP: 10.10.10.70
NAS Share: //10.10.10.70/homes/brian/pool_scout_pro/data
Server Mount: /mnt/nas-pool-data/
PDF Storage: /mnt/nas-pool-data/reports/2025/

Port Configuration

80: HTTP (nginx) → HTTPS redirect
443: HTTPS (nginx) → proxy to gunicorn:7001
7001: Pool Scout Pro (gunicorn) - Timeout increased to 600s
7002: PT360 (gunicorn)
4444: Selenium WebDriver
7900: Selenium VNC access
22: SSH (via router port 2222)

Firewall Rules (UFW)

OpenSSH: SSH access (port 22)
80/tcp: HTTP for nginx
443/tcp: HTTPS for nginx
445/tcp + 139/tcp: SMB/NetBIOS for NAS access (local LAN only)
7001: Pool Scout Pro internal access (127.0.0.1 and 10.10.10.0/24)
7002: PT360 internal access (127.0.0.1 and 10.10.10.0/24)

Timeout Configuration

Gunicorn timeout: 600 seconds (10 minutes) for long downloads
Nginx proxy_read_timeout: 600 seconds
Nginx proxy_connect_timeout: 60 seconds
Nginx proxy_send_timeout: 600 seconds

Active Services

pool-scout-pro.service: ACTIVE (enterprise-ready with 10min timeouts)
nginx.service: ACTIVE (configured for long downloads)
pool-scout-health.timer: ACTIVE
pool-scout-retry.timer: ACTIVE (enterprise retry system)
selenium-firefox: AUTO-MANAGED (Docker)

Operational Systems

EMD Search: Working - Date conversion with Pacific timezone, result extraction, correct date filtering
PDF Download Backend: Working - Browser navigation, PDF link extraction, file storage with human-like timing
PDF Text Extraction: Working - pypdfium2 integration, data parsing
Database Storage: Working - Complete schema, all required columns present
UI System: Working - Clean interface, responsive design, proper button sizing, improved badge colors
Infrastructure: Active - Gunicorn, Nginx, health monitoring, timeout protection
External HTTPS Access: Working - Standard port 443, clean URLs
Local Network Access: Working - Direct IP access on port 80
Failed Download Retry System: Working - Enterprise retry service with automatic processing

Enterprise Retry System

failed_downloads table: Database table for tracking failed downloads
FailedDownloadService: Service for managing retry logic with exponential backoff
RetryService: Background service for automatic retry processing
pool-scout-retry.timer: Systemd timer running every 15 minutes
Trigger mechanism: Event-driven via /tmp/pool_scout_retry_needed file
Health monitoring: JSON status files for operational monitoring
Automatic cleanup: Removes old retry records after 7 days

Filename Format

Current Implementation: YYYYMMDD_FACILITYNAME_SHORTID.pdf
Example: 20250808_CRESTVIEWTOWNHOUSES_DDE1E71B5B38.pdf
Date Source: Search date (inspection_date) passed from search service
ID Extraction: Last segment after final dash in inspection ID
Uniqueness: Naturally unique across dates and facilities

Timezone Handling

Server Timezone: UTC
EMD Timezone: America/Los_Angeles (Pacific)
Conversion Method: DateUtilities.convert_to_pacific_date()
Dependencies: pytz library required

DEPLOYMENT PROCEDURES
bash./manage.sh start    # Start system
./manage.sh status   # Check status
./manage.sh logs     # View logs
./manage.sh restart  # Restart services
Dependencies
Python: selenium, pytz, pypdfium2, requests, flask, gunicorn, aiohttp
System: docker (for Selenium), nginx, systemd
Storage: CIFS mount to NAS
IDENTIFIED ISSUES REQUIRING ATTENTION
Download Progress Indicators

Problem: No real-time progress indicators during downloads
Impact: Users cannot see download status or progress
Evidence: Frontend expects downloadPoller but backend provides no progress endpoints
Priority: HIGH - Poor user experience during long download operations
Technical: downloads.py fires background thread with no progress reporting mechanism

Download System Analysis from August 11 Failures

August 11 downloads failed due to 30-second HTTP timeout (now fixed to 60 seconds)
Current download system works but lacks progress feedback
Failed downloads are properly stored for retry but user gets no immediate feedback
Need real-time progress tracking and UI updates for user transparency

Database Integrity Monitoring
