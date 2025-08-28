PROJECT OVERVIEW
Sacramento County pool inspection automation system - EMD website search, PDF download, data extraction, compliance management.

PROJECT STRUCTURE
sapphire/pool_scout_pro/
├── backups/                          # Automated code backups
├── config/                           # Configuration files
├── data/                            # Local data storage
│   ├── logs/                        # Application logs
│   └── milestones/                  # Project milestone tracking
├── scripts/                         # Utility scripts
├── src/                            # Python source code
│   ├── core/                       # Core utilities and database
│   ├── services/                   # Business logic services
│   ├── web/                        # Flask web application
│   │   ├── routes/                 # API and web routes
│   │   └── shared/                 # Shared web services
├── temp/                           # Temporary files
├── templates/                      # HTML templates and static assets
│   └── static/                     # CSS, JavaScript, and media files
│       ├── css/
│       └── js/
│           ├── core/               # Core JavaScript utilities
│           ├── downloads/          # Download management
│           └── search/             # Search functionality
├── trash/                          # Archive directory
└── venv/                          # Python virtual environment

MANDATORY DEVELOPMENT RULES (STRICTLY ENFORCED)
Code Update Strategy
❌ NO surgical code changes - leads to wasted time hunting syntax errors
❌ NO partial snippets or incomplete edits
❌ NO sed commands - breaks code syntax and indentation
❌ NO "enhanced" code generation without explicit request
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

CURRENT STATUS - August 11, 2025

NETWORK CONFIGURATION
- Internal: 127.0.0.1:7001 (Gunicorn)
- Local HTTP: http://10.10.10.80/ (Nginx proxy)
- External HTTPS: https://sapphire-pools.dyndns.org/ (Standard port 443)
- Container: localhost:4444 (Selenium Firefox)
- NAS IP: 10.10.10.70
- NAS Share: //10.10.10.70/homes/brian/pool_scout_pro/data
- Server Mount: /mnt/nas-pool-data/
- PDF Storage: /mnt/nas-pool-data/reports/2025/

PORT CONFIGURATION
- 80: HTTP (nginx) → HTTPS redirect
- 443: HTTPS (nginx) → proxy to gunicorn:7001
- 7001: Pool Scout Pro (gunicorn) - Timeout increased to 600s
- 7002: PT360 (gunicorn)
- 4444: Selenium WebDriver
- 7900: Selenium VNC access
- 22: SSH (via router port 2222)

FIREWALL RULES (UFW)
- OpenSSH: SSH access (port 22)
- 80/tcp: HTTP for nginx
- 443/tcp: HTTPS for nginx
- 445/tcp + 139/tcp: SMB/NetBIOS for NAS access (local LAN only)
- 7001: Pool Scout Pro internal access (127.0.0.1 and 10.10.10.0/24)
- 7002: PT360 internal access (127.0.0.1 and 10.10.10.0/24)

TIMEOUT CONFIGURATION
- Gunicorn timeout: 600 seconds (10 minutes) for long downloads
- Nginx proxy_read_timeout: 600 seconds
- Nginx proxy_connect_timeout: 60 seconds
- Nginx proxy_send_timeout: 600 seconds

SERVICES STATUS
- pool-scout-pro.service: ACTIVE (enterprise-ready with 10min timeouts)
- nginx.service: ACTIVE (configured for long downloads)
- pool-scout-health.timer: ACTIVE
- pool-scout-retry.timer: ACTIVE (enterprise retry system)
- selenium-firefox: AUTO-MANAGED (Docker)

OPERATIONAL SYSTEMS
- EMD Search: ✅ Working - Date conversion with Pacific timezone, result extraction, debug logging
- PDF Download Backend: ✅ Working - Browser navigation, PDF link extraction, file storage with human-like timing
- PDF Text Extraction: ✅ Working - pypdfium2 integration, data parsing
- Database Storage: ✅ Working - Complete schema, all required columns present
- UI System: ✅ Working - Clean interface, responsive design, proper button sizing, improved badge colors
- Infrastructure: ✅ Active - Gunicorn, Nginx, health monitoring, timeout protection
- External HTTPS Access: ✅ Working - Standard port 443, clean URLs
- Local Network Access: ✅ Working - Direct IP access on port 80
- Failed Download Retry System: ✅ Working - Enterprise retry service with automatic processing

ENTERPRISE RETRY SYSTEM
- failed_downloads table: Database table for tracking failed downloads
- FailedDownloadService: Service for managing retry logic with exponential backoff
- EnterpriseRetryService: Background service for automatic retry processing
- pool-scout-retry.timer: Systemd timer running every 15 minutes
- Trigger mechanism: Event-driven via /tmp/pool_scout_retry_needed file
- Health monitoring: JSON status files for operational monitoring
- Automatic cleanup: Removes old retry records after 7 days

DATABASE OPTIMIZATION
- Database records: 82 (matches PDF files exactly)
- PDF files on disk: 82 (perfect alignment)
- Duplicate database entries: RESOLVED (cleaned up orphaned records)
- Database-to-file consistency: ✅ Perfect match

CURRENT ISSUES
- Duplicate Detection: Incorrectly marking facilities as saved (47/51 instead of 26/51)
- Search Performance: search-with-duplicates endpoint experiencing timeout issues
- PDF Filename Matching: Short ID matching too broad, causing false positives

ASYNC DEVELOPMENT STATUS
- Step 1: Async HTTP Downloads - IMPLEMENTED but not tested due to duplicate detection issues
- AsyncPDFDownloader: Created with aiohttp integration for parallel HTTP downloads
- Performance Target: 2-3x speed improvement for batch downloads
- Testing Status: Blocked pending duplicate detection fix

FILENAME FORMAT
- Current Implementation: YYYYMMDD_FACILITYNAME_SHORTID.pdf
- Example: 20250808_CRESTVIEWTOWNHOUSES_DDE1E71B5B38.pdf
- Date Source: Search date (inspection_date) passed from search service
- ID Extraction: Last segment after final dash in inspection ID
- Uniqueness: Naturally unique across dates and facilities

TIMEZONE HANDLING
- Server Timezone: UTC
- EMD Timezone: America/Los_Angeles (Pacific)
- Conversion Method: DateUtilities.convert_to_pacific_date()
- Dependencies: pytz library required

DEPLOYMENT COMMANDS
```bash
./manage.sh start    # Start system
./manage.sh status   # Check status
./manage.sh logs     # View logs
./manage.sh restart  # Restart services
DEPENDENCIES

Python: selenium, pytz, pypdfium2, requests, flask, gunicorn, aiohttp
System: docker (for Selenium), nginx, systemd
Storage: CIFS mount to NAS

RESOLVED ISSUES

Project path migration: /home/brian/pool_scout_pro/ → /home/brian/sapphire/pool_scout_pro/
Virtual environment recreation with correct dependencies
NAS storage path restoration: /mnt/nas-pool-data/reports/2025/
Port configuration: 8765 → 7001 (internal application port)
External HTTPS access: Working on standard port 443
Nginx configuration: Cleaned up conflicts, proper routing
Static file serving: CSS and JavaScript loading correctly
DynDNS configuration: Automatic IP updates via router
Database duplicates: Cleaned orphaned records, perfect file-to-database alignment
Gunicorn timeouts: Extended to 10 minutes for long downloads
Nginx timeouts: Extended to match Gunicorn configuration
504 Gateway timeouts: RESOLVED with proper timeout configuration
Date format mismatch: RESOLVED (frontend YYYY-MM-DD to database MM/DD/YYYY)
Badge behavior: RESOLVED (Found=0 on date selection, proper colors)

PRIORITY FIXES NEEDED

Duplicate Detection Logic: Fix false positive matching causing incorrect saved counts
Search Performance: Optimize search-with-duplicates endpoint timeout issues
Async Testing: Complete Step 1 async downloader testing once duplicate detection fixed
Transactional Downloads: Implement database-after-success pattern to prevent orphaned records

NEXT PHASE
Duplicate Detection Fix - Correct PDF filename matching logic to show accurate saved counts, then proceed with async downloader testing
EOF
echo "✅ Milestone updated - August 11, 2025"
echo "📊 Current status: Systems operational, duplicate detection needs fix"
