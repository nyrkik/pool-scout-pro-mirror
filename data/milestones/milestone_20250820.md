# Pool Scout Pro - System Milestone Documentation

## System Overview

Pool Scout Pro is an inspection report management for Sacramento County pool inspections. The system searches EMD (Environmental Management Department) records, downloads PDF inspection reports, extracts data, and stores it in a normalized database with inspection ID-based duplicate detection and date verification.

**Core Philosophy**: Download → Extract → Database (transactional flow ensures data consistency)

**Current System Status**: Enterprise-ready system with comprehensive resilience architecture. Search and download systems operational with intelligent failure recovery, health monitoring, automatic retry mechanisms, separated database architecture for scalability, and multi-session Selenium configuration for concurrent operations.

!!! ALWAYS INCLUDE THE FOLLOWING IN EVERY MILESTONE UPDATE !!!

**DEVELOPMENT RULES - MANDATORY ADHERENCE**
1. **ALWAYS GET PERMISSION BEFORE GENERATING CODE** - Confirm understanding before any code generation
2. **USE INTEGRATED DEVELOPMENT SYSTEM** - ALWAYS use dev-tools workflow, never manual file editing
3. **INCREMENTAL DEVELOPMENT** - One step at a time, confirm each change works
4. **COPY-PASTE READY COMMANDS** - All commands must run from project root
5. **HYBRID FILE EDITING APPROACH** - Short files (<100 lines): complete replacement, Medium (100-500): section replacement, Long (>500): external snippets
6. **NEVER MODIFY FILES WITHOUT SEEING THEM FIRST** - Always examine current content
7. **CLEAR STEP DELINEATION** - Structure commands with clear step comments
8. **USE DEV-TOOLS FOR ALL CHANGES** - Apply changes via safe-edit.sh or safe-patch.sh, never direct file modification
9. **ALWAYS VALIDATE SYNTAX** - Use dev-workflow.sh validate before any changes
10. **EFFICIENT CONTENT HANDLING** - For large files, generate commands without showing full content
11: **NEVER USE TEST/SAMPLE DATA IN PRODUCTION. Do not create test/sample reports, or dummy data in the production database or file system. Use real data from search results only, or work in a separate development environment.
12: Keep responses short and to the point, avoiding detailed explanations unless explicitly requested, to conserve chat space.

**🛠️ MANDATORY DEV-TOOLS WORKFLOW**
- `./dev-tools/dev-workflow.sh validate <file>` - Check syntax BEFORE changes
- `./dev-tools/dev-workflow.sh edit <target> <new>` - Safe file replacement with auto-backup
- `./dev-tools/dev-workflow.sh patch <target> <patch>` - Apply git patches safely
- `./dev-tools/dev-workflow.sh rollback <file>` - Emergency restore from backup
- `./dev-tools/dev-workflow.sh restart` - Test changes with service restart
- **NEVER manually edit files** - Use dev-tools for ALL modifications

MILESTONE MAINTENANCE INSTRUCTIONS FOR FUTURE CHATS
This milestone contains ONLY:
✅ Project structure and file purposes
✅ Development rules and standards
✅ System capabilities and configuration
✅ Deployment procedures
✅ Current status and identified issues

Do NOT add to this milestone:
❌ Resolved issues (transient information)
❌ Temporary status updates
❌ "Next phase priorities" or similar changing content
❌ Backup files, enhanced files, or dated suffixes in structure

!!! ALWAYS INCLUDE THE ABOVE IN EVERY MILESTONE UPDATE !!!

---

## Integrated Development System

### **🛠️ Safe Development Workflow**

Pool Scout Pro includes a comprehensive development toolkit that enforces safety protocols and prevents code corruption. **ALL CODE CHANGES MUST USE THIS SYSTEM**.

### **Development Toolkit Structure**
```
dev-tools/
├── dev-workflow.sh          # Main workflow coordinator - PRIMARY INTERFACE
├── validate-syntax.sh       # Python syntax validation with import testing
├── safe-edit.sh            # Safe file replacement with automatic backups
├── safe-patch.sh           # Git-style patch application with rollback
├── rollback.sh             # Quick restore from timestamped backups
├── setup-git-workflow.sh   # Git branch setup for development
└── workflow.sh             # Testing and deployment coordination
```

### **🔄 Mandatory Development Process**
1. **Git Branch Strategy**: All changes on development branch
2. **Pre-flight Validation**: Syntax check before ANY file modification
3. **Automatic Backups**: Every change creates `filename.YYYYMMDD_HHMMSS` backup in `data/backups/`
4. **Atomic Operations**: Backup → Validate → Apply → Verify → Success/Rollback
5. **Zero-Downtime Recovery**: Instant rollback if validation fails
6. **Service Integration**: Direct testing via service restart commands

### **⚡ Required Workflow Commands**

**NEVER manually edit files - ALWAYS use these commands:**

```bash
# Step 1: ALWAYS validate syntax first
./dev-tools/dev-workflow.sh validate src/services/pdf_downloader.py

# Step 2: Apply changes via safe replacement
./dev-tools/dev-workflow.sh edit src/services/pdf_downloader.py /tmp/updated_file.py

# Alternative: Apply git-style patches for large files
./dev-tools/dev-workflow.sh patch src/services/pdf_downloader.py /tmp/changes.patch

# Step 3: Test changes immediately
./dev-tools/dev-workflow.sh restart

# Emergency: Rollback if issues detected
./dev-tools/dev-workflow.sh rollback src/services/pdf_downloader.py
```

### **🛡️ Safety Features**
- **Pre-flight Validation**: Python compilation + import testing before application
- **Automatic Backups**: Timestamped backups prevent data loss
- **Rollback on Failure**: Auto-restore if post-application validation fails
- **Import Testing**: Ensures modified Python modules can be imported correctly
- **Service Integration**: Immediate testing via `manage.sh` integration
- **Git Integration**: Development branch isolation from production code

### **🚫 Prohibited Actions**
- **NEVER** manually edit files with nano/vim/sed
- **NEVER** apply changes without pre-validation
- **NEVER** skip the backup process
- **NEVER** modify files on main branch directly
- **NEVER** ignore validation failures

### **✅ Development Workflow Example**
```bash
# 1. Examine current file
cat src/services/pdf_downloader.py

# 2. Create new version in /tmp/
cat > /tmp/updated_downloader.py << 'EOF'
# Updated content here
EOF

# 3. Validate before applying
./dev-tools/dev-workflow.sh validate /tmp/updated_downloader.py

# 4. Apply safely with automatic backup
./dev-tools/dev-workflow.sh edit src/services/pdf_downloader.py /tmp/updated_downloader.py

# 5. Test immediately
./dev-tools/dev-workflow.sh restart

# 6. Verify functionality
./dev-tools/dev-workflow.sh status
```

### **🔙 Emergency Recovery**
```bash
# View available backups
ls -la data/backups/pdf_downloader.py.*

# Restore from latest backup
./dev-tools/dev-workflow.sh rollback src/services/pdf_downloader.py

# Restart service after rollback
./dev-tools/dev-workflow.sh restart
```

**CRITICAL**: This development system is **MANDATORY** for all code changes. It prevents the production system corruption that the development rules are designed to avoid.

---

### ⚠️ **IDENTIFIED ISSUES REQUIRING ATTENTION**
- **Frontend Download Integration**: `window.searchService.getCurrentResults()` may not return data to download service
- **Progress Polling**: Download progress endpoint functional but frontend polling disabled due to hanging issues
- **Debug Logging**: Print statements don't appear in systemd logs (need proper Python logging)
- **Message Display**: Large message box restored accidentally (should be small inline message)

---

## System Architecture

### **Separation of Operations**

The system maintains strict separation between:

1. **Search Operations** (`SearchService`) - EMD website interaction and facility discovery
2. **Download Operations** (`PDFDownloader`) - PDF file acquisition and transactional processing with enterprise resilience
3. **Extraction Operations** (`PDFExtractor`) - PDF content parsing and date verification
4. **Database Operations** (`DatabaseService`) - Data persistence and integrity with enterprise architecture
5. **Web Interface** (`Flask`) - User interaction and API endpoints
6. **Health Monitoring** (`SeleniumHealthService`) - Container health verification and recovery
7. **External Monitoring** - Independent Selenium monitoring with restart capability and alerting
8. **Retry Management** - Dead letter queue processing and scheduled retry operations
9. **Multi-Session Management** - Concurrent session handling with intelligent resource management

**Critical**: Each operation is isolated and can fail independently without corrupting others.

---

## Enhanced Features

### **Multi-Session Selenium Architecture**
- **Purpose**: Eliminate single session bottleneck and enable concurrent PDF downloads
- **Configuration**: 5 concurrent sessions (increased from 1) with resource management
- **Benefits**:
  - **5x Download Speed**: Concurrent PDF downloads instead of sequential
  - **Fault Tolerance**: Single stuck session doesn't block other operations
  - **Resource Optimization**: Better utilization of Firefox container capacity
  - **Graceful Degradation**: System remains functional with partial session failures
- **Session Management**: Automatic cleanup of idle and stuck sessions with configurable thresholds
- **Health Monitoring**: Per-session health tracking with utilization monitoring

### **Hybrid Monitoring Architecture**
- **Application Monitor** (`robust_selenium_monitor.py`):
  - **Scope**: Session management, cleanup, pre-download health verification
  - **Speed**: Immediate detection and resolution of session issues
  - **Capabilities**: Session cleanup, stuck session detection, resource management
  - **Limitation**: No container restart capability (runs inside container)
- **External Monitor** (`/usr/local/bin/selenium_monitor.sh`):
  - **Scope**: Container health, infrastructure restarts, system-level recovery
  - **Frequency**: Every 3 minutes via cron job
  - **Capabilities**: Container restart, failure alerting, infrastructure management
  - **Docker Access**: Full container management from host system
- **Division of Labor**: Fast session issues handled by application, infrastructure issues by external monitor

### **Enterprise Database Architecture**
- **Purpose**: Separate business data from operational data for scalability and data lifecycle management
- **Implementation**: Two-database architecture with clear separation of concerns
- **Databases**:
  - `inspection_data.db` - Business data (facilities, reports, violations, equipment, chemistry)
  - `system_management.db` - Operational data (failed downloads, health status, search timing, retry queues)
- **Benefits**: Independent backup strategies, different retention policies, scalable to multiple counties

### **Comprehensive External Monitoring System**
- **Purpose**: Ensure system availability and automatic recovery from infrastructure failures
- **Components**:
  - **Selenium Health Monitor** (`/usr/local/bin/selenium_monitor.sh`) - Runs every 3 minutes
  - **Container Restart Capability** - Automatically restarts unhealthy Selenium containers
  - **Alerting System** - Logs alerts to `/var/log/pool_scout_alerts.log` for persistent failures
  - **Scheduled Retry Processing** (`/usr/local/bin/retry_job.sh`) - Runs every hour
- **Health Checks**: HTTP status endpoint monitoring with container readiness verification
- **Recovery Actions**: Automatic container restart, exponential backoff retry, failure escalation

### **Intelligent Download Retry Logic**
- **Purpose**: Comprehensive failure recovery with infrastructure health awareness
- **Implementation**:
  - **3 immediate retry attempts** with Selenium health checks on each failure
  - **Selenium recovery** - Restart container and retry if infrastructure issue detected
  - **Mark for later retry** - Store persistent failures in system database for scheduled processing
  - **Dead letter queue** - Failed downloads tracked with retry counts and scheduling
- **Retry Scheduling**: 1-hour delay for later retry attempts with retry_candidates view for processing
- **Failure Classification**: Distinguishes infrastructure failures (Selenium) from content failures (network/PDF)

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

### **Transactional Download Processing with Enterprise Resilience**
- **Single-Flight Lock**: Prevents concurrent downloads via `DownloadLockService`
- **Atomic Operations**: Download → Extract → Database (all succeed or all fail)
- **Failure Recovery**: Failed downloads stored for enterprise retry via `FailedDownloadService`
- **File Integrity**: PDF validation and proper cleanup on errors
- **Progress Tracking**: Real-time download progress with frontend polling system (currently disabled)
- **Health Monitoring**: Pre-flight Selenium health checks with automatic recovery
- **Multi-Level Retry**:
  - Level 1: 3 immediate attempts with Selenium health checks per failure
  - Level 2: Automatic container restart and immediate retry for infrastructure issues
  - Level 3: Mark for later retry (1-hour delay) for persistent failures
  - Level 4: Scheduled retry processing via cron job (hourly)
- **Queue Management**: Failed facility tracking with intelligent retry scheduling
- **Enterprise Recovery**: Comprehensive failure classification and appropriate response actions
- **Concurrent Processing**: Multiple PDF downloads with session management and resource optimization

### **Comprehensive Resilience Architecture**
- **4-Level Resilience Strategy**:
  - **Level 1**: Application retry logic (3 immediate attempts with health checks)
  - **Level 2**: Infrastructure recovery (automatic Selenium container restart)
  - **Level 3**: Scheduled retry processing (hourly cron job for persistent failures)
  - **Level 4**: External monitoring and alerting (3-minute health checks with restart capability)
- **Session-Level Resilience**: Multi-session architecture prevents single point of failure
- **Proactive Protection**: Selenium health verification before download initiation
- **Reactive Recovery**: Immediate container restart and retry for infrastructure failures
- **Intelligence Failure Classification**: Distinguish infrastructure vs content failures for appropriate response
- **Enterprise Monitoring**: External monitoring script with container management and alerting
- **Dead Letter Queue**: Persistent failure tracking with retry_candidates view for efficient processing
- **Comprehensive Logging**: Detailed visibility into all failure modes and recovery actions

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
├── dev-tools/                          # MANDATORY DEVELOPMENT SYSTEM
│   ├── dev-workflow.sh                 # Main development workflow coordinator
│   ├── validate-syntax.sh              # Python syntax and import validation
│   ├── safe-edit.sh                    # Safe file replacement with backups
│   ├── safe-patch.sh                   # Git patch application with rollback
│   ├── rollback.sh                     # Emergency restore from backups
│   ├── setup-git-workflow.sh           # Git development branch setup
│   └── workflow.sh                     # Testing and deployment coordination
│
├── data/
│   ├── backups/                        # Automatic timestamped file backups
│   ├── reports.db                      # SQLite database
│   └── reports/                        # PDF file storage organized by year
│       └── 2025/
│
├── src/
│   ├── core/                           # Core system utilities
│   │   ├── browser.py                  # Selenium WebDriver management with health checks
│   │   ├── error_handler.py            # Centralized error logging and handling
│   │   ├── settings.py                 # Configuration management
│   │   └── utilities.py                # File operations, date conversion, validation
│   │
│   ├── services/                       # Business logic services
│   │   ├── search_service.py           # EMD website search and facility discovery
│   │   ├── pdf_downloader.py           # PDF download with transactional processing and resilience
│   │   ├── pdf_extractor.py            # PDF parsing and date verification
│   │   ├── database_service.py         # Database operations and queries
│   │   ├── download_lock_service.py    # Single-flight download locking
│   │   ├── failed_download_service.py  # Failed download tracking and retry
│   │   ├── saved_status_service.py     # Track which reports are already saved
│   │   ├── duplicate_prevention_service.py # Inspection ID-based duplicate prevention
│   │   ├── download_progress_service.py # Real-time download progress tracking
│   │   ├── health_monitor_service.py   # Selenium container health monitoring
│   │   ├── resilience_service.py       # Failure recovery and retry coordination
│   │   └── robust_selenium_monitor.py  # Multi-session monitoring and cleanup
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
│       │       └── download-poller.js  # Real-time progress polling (disabled)
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
    total_violations INTEGER, major_violations INTEGER,
    pdf_filename TEXT, pdf_path TEXT,
    created_at TEXT, updated_at TEXT
)

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

-- Failed download tracking for enterprise retry system
failed_downloads (
    id INTEGER PRIMARY KEY,
    facility_name TEXT, pdf_url TEXT,
    inspection_id TEXT, inspection_date TEXT,
    failure_reason TEXT, failure_details TEXT,
    batch_id TEXT, created_at TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 2,
    next_retry_at TEXT, resolved_at TEXT,
    status TEXT DEFAULT 'pending'
)

-- Retry queue management for scheduled processing
retry_queue (
    id INTEGER PRIMARY KEY,
    failed_download_id INTEGER REFERENCES failed_downloads(id),
    retry_count INTEGER DEFAULT 0,
    next_retry_at TEXT,
    status TEXT DEFAULT 'PENDING',
    last_attempt_at TEXT,
    created_at TEXT, updated_at TEXT
)

-- System health monitoring
health_status (
    id INTEGER PRIMARY KEY,
    component TEXT,  -- 'selenium', 'downloads', 'database'
    status TEXT,     -- 'healthy', 'degraded', 'failed'
    last_check TEXT,
    failure_count INTEGER DEFAULT 0,
    details TEXT, updated_at TEXT
)

-- Performance monitoring (dual tables for historical data)
search_timing (
    id INTEGER PRIMARY KEY,
    search_date TEXT, duration_seconds REAL,
    facility_count INTEGER, created_at TEXT
)

search_timings (
    id INTEGER PRIMARY KEY,
    search_date TEXT, duration REAL,
    timestamp TEXT
)
```

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
- `POST /api/v1/reports/download/start` - Initiate PDF downloads with resilience
  - Input: `{"facilities": [...]}`
  - Output: Download results with success/failure counts and retry queue status

### **Progress Tracking**
- `GET /api/v1/downloads/progress` - Real-time download progress
- `GET /api/v1/downloads/status` - Download system status

---

## Frontend Architecture

### **Modular JavaScript Design**
- **Separation of Concerns**: Each JS file has single responsibility
- **Service Layer**: API communication abstracted into services
- **UI Layer**: DOM manipulation separated from business logic
- **Progress System**: Real-time updates via polling architecture (currently disabled)

### **Key Components**
- **SearchUI**: Manages search interface and button state transitions
- **DownloadService**: Handles download initiation and management
- **DownloadPoller**: Polls backend for real-time progress updates (disabled)
- **UIManager**: Centralized DOM manipulation and state management
- **PageStateService**: Manages page state and saved report counts

---

## Production Deployment

### **Server Configuration**
- **Application Server**: Gunicorn WSGI server
- **Entry Point**: `wsgi.py` → `create_app()` factory pattern
- **Port Configuration**: 7001 (internal application port)
- **Process Management**: systemd service (`pool-scout-pro.service`)

### **Selenium Configuration**
- **Container**: `selenium/standalone-firefox:latest`
- **Sessions**: 5 concurrent sessions (SE_NODE_MAX_SESSIONS=5)
- **Session Timeout**: 300 seconds
- **Session Management**: Automatic cleanup with configurable thresholds
- **Resource Limits**: Session utilization monitoring and proactive cleanup
- **Health Endpoints**: HTTP status monitoring at localhost:4444/status

### **Network Configuration**
- Internal: 127.0.0.1:7001 (Gunicorn)
- Local HTTP: http://10.10.10.80/ (Nginx proxy)
- External HTTPS: https://sapphire-pools.dyndns.org/ (Standard port 443)
- Container: localhost:4444 (Selenium Firefox)
- NAS IP: 10.10.10.70
- NAS Share: //10.10.10.70/homes/brian/pool_scout_pro/data
- Server Mount: /mnt/nas-pool-data/
- PDF Storage: /mnt/nas-pool-data/reports/2025/

### **Service Management**
- `./manage.sh start` - Start system
- `./manage.sh status` - Check status
- `./manage.sh logs` - View logs
- `./manage.sh restart` - Restart services

### **Monitoring and Resilience**
- **External Monitoring**: Independent Selenium container health monitoring (`/usr/local/bin/selenium_monitor.sh`)
  - **Frequency**: Every 3 minutes via cron job
  - **Capabilities**: Health check, automatic container restart, failure alerting
  - **Alert Log**: `/var/log/pool_scout_alerts.log` for persistent failure tracking
- **Application Monitoring**: Real-time session health monitoring (`robust_selenium_monitor.py`)
  - **Scope**: Session cleanup, stuck session detection, resource management
  - **Speed**: Immediate response to session issues
  - **Limitations**: No container restart capability (separated concerns)
- **Scheduled Retry Processing**: Automated retry job (`/usr/local/bin/retry_job.sh`)
  - **Frequency**: Every hour via cron job
  - **Function**: Process failed downloads from dead letter queue
  - **Retry Log**: `/var/log/pool_scout_retry.log` for retry processing history
- **Health Monitoring**: Application-level Selenium health checks before and during downloads
- **Retry Queues**: Failed downloads tracked in system database for scheduled processing
- **Database Views**: `retry_candidates` view for efficient retry queue processing

### **Real-time Logging**
- `journalctl -u pool-scout-pro -f` - Live systemd service logs
- `/var/log/selenium_monitor.log` - External Selenium monitoring logs
- `/var/log/pool_scout_alerts.log` - System health alerts and persistent failures
- `/var/log/pool_scout_retry.log` - Scheduled retry processing logs
- Note: Python print() statements don't appear in systemd logs

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
- Health monitoring prevents system instability
- Multi-session architecture prevents single points of failure

---

## Future Development Notes

### **Architecture Ready For**
- Real-time WebSocket progress updates
- Multiple data source integration
- Advanced reporting and analytics
- Automated scheduling and monitoring
- Enterprise authentication systems
- External monitoring integration
- Horizontal scaling with load balancing

### **Extension Points**
- Additional PDF format support via `PDFExtractor`
- Multiple county support via service abstraction
- Advanced search filters via `SearchService`
- Notification systems via event hooks (email/SMS alerting framework ready)
- Backup and disaster recovery via service patterns
- Container orchestration integration for health management
- Advanced retry strategies and failure analysis
- Real-time dashboard for system health monitoring
- Load balancing across multiple Selenium containers
