# Pool Scout Pro - System Milestone Documentation

## System Overview

Pool Scout Pro is an inspection report management for Sacramento County pool inspections. The system searches EMD (Environmental Management Department) records, downloads PDF inspection reports, extracts data, and stores it in a normalized database with inspection ID-based duplicate detection and date verification.

**Core Philosophy**: Download → Extract → Database (transactional flow ensures data consistency)

**Current System Status**: Fully operational with complete search, download, extraction, and progress tracking capabilities. Backend APIs functioning correctly with inspection ID-based duplicate detection and proper date verification.

!!! ALWAYS INCLUDE THE FOLLOWING IN EVERY MILESTONE UPDATE !!!

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

!!! ALWAYS INCLUDE THE ABOVE IN EVERY MILESTONE UPDATE !!!

---

## System Architecture

### **Separation of Operations**

The system maintains strict separation between:

1. **Search Operations** (`SearchService`) - EMD website interaction and facility discovery
2. **Download Operations** (`PDFDownloader`) - PDF file acquisition and transactional processing
3. **Extraction Operations** (`PDFExtractor`) - PDF content parsing and date verification
4. **Database Operations** (`DatabaseService`) - Data persistence and integrity
5. **Web Interface** (`Flask`) - User interaction and API endpoints

**Critical**: Each operation is isolated and can fail independently without corrupting others.

---

## Enhanced Features

### **Inspection ID-Based Duplicate Detection**
- **Purpose**: Prevent duplicate downloads using precise inspection ID matching
- **Implementation**: Extracts inspection ID from PDF URLs for accurate duplicate checking
- **Logic**: Primary check via inspection_id, fallback to facility name with permissive threshold
- **Pattern**: Multiple inspection reports per facility are supported and expected

### **Date Verification System**
- **Purpose**: Ensure inspection reports are saved with correct dates
- **Implementation**: Extracts actual inspection date from PDF content (`Date Entered: MM/DD/YYYY`)
- **Verification**: Compares PDF date vs search parameters with mismatch logging
- **File Naming**: Uses actual inspection date in filename (not search date)

### **Transactional Download Processing**
- **Single-Flight Lock**: Prevents concurrent downloads via `DownloadLockService`
- **Atomic Operations**: Download → Extract → Database (all succeed or all fail)
- **Failure Recovery**: Failed downloads stored for enterprise retry via `FailedDownloadService`
- **File Integrity**: PDF validation and proper cleanup on errors
- **Progress Tracking**: Real-time download progress with frontend polling system

### **Multiple Reports Per Facility**
- **Business Logic**: Facilities commonly have multiple inspection reports on the same date
- **Valid Scenarios**: Multiple features (pool + spa), re-inspections, follow-up compliance checks
- **Database Design**: inspection_reports table stores individual reports (many-to-one with facilities)
- **Counting Logic**: COUNT(*) = Total reports, COUNT(DISTINCT facility_id) = Unique facilities
- **Frontend Display**: Shows facility count, not report count

---

## Directory Structure & File Purposes

```
pool_scout_pro/
├── src/
│   ├── core/                           # Core system utilities
│   │   ├── browser.py                  # Selenium WebDriver management
│   │   ├── error_handler.py            # Centralized error logging and handling
│   │   ├── settings.py                 # Configuration management
│   │   └── utilities.py                # File operations, date conversion, validation
│   │
│   ├── services/                       # Business logic services
│   │   ├── search_service.py           # EMD website search and facility discovery
│   │   ├── pdf_downloader.py           # PDF download with transactional processing
│   │   ├── pdf_extractor.py            # PDF parsing and date verification
│   │   ├── database_service.py         # Database operations and queries
│   │   ├── download_lock_service.py    # Single-flight download locking
│   │   ├── failed_download_service.py  # Failed download tracking and retry
│   │   ├── saved_status_service.py     # Track which reports are already saved
│   │   ├── duplicate_prevention_service.py # Inspection ID-based duplicate prevention
│   │   └── download_progress_service.py # Real-time download progress tracking
│   │
│   └── web/                            # Web application layer
│       ├── app.py                      # Flask application factory (enterprise pattern)
│       ├── wsgi.py                     # Production WSGI entry point
│       ├── routes/
│       │   ├── api_routes.py           # API endpoints for search/download
│       │   └── downloads.py            # Download management endpoints
│       └── shared/
│           └── services.py             # Service factory and dependency injection
│
├── templates/                          # Web interface
│   ├── search_reports.html             # Main application interface
│   └── static/
│       ├── js/
│       │   ├── main.js                 # Application coordinator and initialization
│       │   ├── core/                   # Core frontend services
│       │   │   ├── api-client.js       # HTTP API communication
│       │   │   ├── ui-manager.js       # DOM manipulation and UI state
│       │   │   └── page-state-service.js # Page state management
│       │   ├── search/                 # Search functionality
│       │   │   ├── search-service.js   # Search API calls
│       │   │   └── search-ui.js        # Search interface and results display
│       │   └── downloads/              # Download functionality
│       │       ├── download-service.js # Download initiation and management
│       │       ├── download-ui.js      # Download progress display
│       │       └── download-poller.js  # Real-time progress polling
│       └── css/
│           └── styles.css              # Application styling
│
├── gunicorn.conf.py                    # Production server configuration
├── wsgi.py                             # WSGI application entry point
└── data/                               # Data storage
    ├── reports.db                      # SQLite database
    └── reports/                        # PDF file storage organized by year
        └── 2025/
```

---

## Database Schema

### **Core Tables**

```sql
-- Facility master data
facilities (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    program_identifier TEXT,
    facility_type TEXT DEFAULT 'POOL',
    street_address TEXT,
    city TEXT, state TEXT, zip_code TEXT,
    permit_holder TEXT, phone TEXT
)

-- Inspection reports with date verification
inspection_reports (
    id INTEGER PRIMARY KEY,
    facility_id INTEGER REFERENCES facilities(id),
    permit_id TEXT, establishment_id TEXT,
    inspection_date TEXT,              -- Actual date from PDF
    inspection_id TEXT,                -- Unique inspection identifier
    inspector_name TEXT, inspector_phone TEXT,
    total_violations INTEGER, majorADDRESS HANDLING ARCHITECTURE
Database Storage: Structured components (street_address, city, state, zip_code)
Frontend Display: Computed display_address field ("Street, City" format)
PDF Extraction: Multi-line parsing with "Facility City" and "Facility ZIP" artifact removal
Search Results: EMD provides complete address converted to display_address format
Separation of Concerns: Persistent structured data vs temporary display formatting



-- Violation details
violations (
    id INTEGER PRIMARY KEY,
    report_id INTEGER REFERENCES inspection_reports(id),
    facility_id INTEGER REFERENCES facilities(id),
    violation_code TEXT, violation_title TEXT,
    observations TEXT, code_description TEXT,
    is_major_violation BOOLEAN DEFAULT FALSE,
    severity_score REAL DEFAULT 1.0
)

-- Failed download tracking for retry
failed_downloads (
    id INTEGER PRIMARY KEY,
    facility_name TEXT, pdf_url TEXT,
    inspection_id TEXT, inspection_date TEXT,
    failure_reason TEXT, failure_details TEXT,
    batch_id TEXT, created_at TEXT,
    retry_count INTEGER DEFAULT 0,
    last_retry_at TEXT, resolved_at TEXT
)
```

### **Current Data Patterns**

**August 11th, 2025 Example:**
- **Total Reports**: 32 individual inspection reports
- **Unique Facilities**: 24 facilities
- **Multiple Reports**: 7 facilities have multiple inspections (2-3 reports each)
- **Average**: 1.3 reports per facility
- **Inspection IDs**: 32 unique inspection identifiers

---

## API Endpoints

### **Search Operations**
- `POST /api/v1/reports/search-with-duplicates` - Search EMD with inspection ID-based duplicate detection
  - Input: `{"start_date": "YYYY-MM-DD"}`
  - Output: Facilities with `saved` status based on inspection_id matching

- `POST /api/v1/reports/existing-for-date` - Retrieve saved reports for date
  - Input: `{"date": "YYYY-MM-DD"}`
  - Output: All existing inspection reports from database

### **Download Operations**
- `POST /api/v1/reports/download/start` - Initiate PDF downloads
  - Input: `{"facilities": [...]}`
  - Output: Download results with success/failure counts

### **Progress Tracking**
- `GET /api/v1/downloads/progress` - Real-time download progress
- `GET /api/v1/downloads/status` - Download system status

### **Data Operations**
- `GET /api/v1/reports/saved-count` - Count of saved reports for date
  - Input: `?date=YYYY-MM-DD`
  - Output: `{"saved_count": N}`

---

## Frontend Architecture

### **Modular JavaScript Design**
- **Separation of Concerns**: Each JS file has single responsibility
- **Service Layer**: API communication abstracted into services
- **UI Layer**: DOM manipulation separated from business logic
- **Progress System**: Real-time updates via polling architecture

### **Key Components**
- **SearchUI**: Manages search interface and results display
- **DownloadService**: Handles download initiation and management
- **DownloadPoller**: Polls backend for real-time progress updates
- **UIManager**: Centralized DOM manipulation and state management
- **PageStateService**: Manages page state and saved report counts

---

## System Flows

### **Search Flow**
1. User selects date → `SearchUI.handleSearch()`
2. `SearchService.searchForReports()` → `POST /api/v1/reports/search-with-duplicates`
3. `SearchService.search_emd_for_date()` - EMD website interaction
4. `DuplicatePreventionService` - Check existing reports using inspection_id
5. Return facilities with saved status to frontend

### **Download Flow**
1. User clicks Save → `DownloadUI.handleSaveClick()`
2. `DownloadService.startDownload()` → `POST /api/v1/reports/download/start`
3. `PDFDownloader.download_pdfs_from_facilities()` - Transactional processing
4. For each facility:
   - **Download**: Selenium + HTTP session to get PDF
   - **Extract**: `PDFExtractor.extract_and_save()` with date verification
   - **Database**: Atomic save to all tables
5. `DownloadPoller` provides real-time progress updates

### **Date Verification Flow**
1. Search EMD for date X → get facility list with inspection_ids
2. Download PDF → contains actual inspection date Y
3. Extract date Y from PDF content (`Date Entered: MM/DD/YYYY`)
4. Compare X vs Y → log warnings if mismatch
5. Save to database with actual date Y
6. Use actual date Y in filename

### **Duplicate Detection Flow**
1. Extract inspection_id from PDF URL
2. Check if inspection_id exists in database
3. Primary: inspection_id match = duplicate
4. Fallback: facility name with permissive threshold (3+ reports)
5. Mark facility as saved/new for download filtering

---

## Production Deployment

### **Server Configuration**
- **Application Server**: Gunicorn WSGI server
- **Entry Point**: `wsgi.py` → `create_app()` factory pattern
- **Port Configuration**: 7001 (internal application port)
- **Process Management**: systemd service (`pool-scout-pro.service`)

### **Application Structure**
- **Pattern**: Flask application factory (enterprise-level)
- **Configuration**: External config files (`gunicorn.conf.py`, `settings.yaml`)
- **Logging**: Structured logging with performance middleware
- **Security**: Process isolation, proper user/group settings

### **Network Architecture**
- **Internal**: 127.0.0.1:7001 (Gunicorn)
- **External**: Reverse proxy to domain
- **Health Checks**: `/health` endpoint available
- **Monitoring**: Performance and error logging

---

## Configuration & Settings

### **Environment Variables**
- `PDF_DOWNLOAD_PATH`: PDF storage directory
- `SELENIUM_URL`: Remote Selenium server (if used)
- `DATABASE_PATH`: SQLite database location

### **System Settings** (`core/settings.py`)
- Download timeouts and retry counts
- Human-like timing patterns for EMD interaction
- File validation parameters
- Error handling configurations

---

## Error Handling & Recovery

### **Layered Error Management**
- **Service Level**: Each service handles its own errors with context
- **Transaction Level**: Rollback on failure, cleanup resources
- **System Level**: Centralized logging via `ErrorHandler`
- **User Level**: Friendly error messages with actionable guidance

### **Failure Recovery**
- Failed downloads stored in `failed_downloads` table
- Enterprise retry service triggered on batch failures
- Automatic cleanup of incomplete operations
- Manual retry capabilities for administrators

---

## Performance & Scalability

### **Current Optimizations**
- Single-flight download locking prevents resource conflicts
- Shared browser sessions reduce overhead
- Transactional processing ensures data consistency
- Real-time progress updates improve user experience
- Inspection ID-based duplicate detection improves accuracy

### **Scalability Considerations**
- Database indexes on frequently queried fields (inspection_id, facility_id)
- File storage organized by year for management
- Modular service architecture supports horizontal scaling
- Clean separation allows individual component optimization

---

## Security & Compliance

### **Data Protection**
- No sensitive credential storage in code
- Session management for EMD website interaction
- Input validation on all API endpoints
- Safe file handling with validation

### **System Integrity**
- PDF content validation before storage
- Date verification prevents data corruption
- Atomic transactions ensure consistency
- Comprehensive audit logging
- Inspection ID verification prevents duplicate processing

---

## Future Development Notes

### **Architecture Ready For**
- Real-time WebSocket progress updates
- Multiple data source integration
- Advanced reporting and analytics
- Automated scheduling and monitoring
- Enterprise authentication systems

### **Extension Points**
- Additional PDF format support via `PDFExtractor`
- Multiple county support via service abstraction
- Advanced search filters via `SearchService`
- Notification systems via event hooks
- Backup and disaster recovery via service patterns
