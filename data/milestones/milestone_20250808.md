Pool Scout Pro - System Status & Configuration
PROJECT OVERVIEW
Sacramento County pool inspection automation system - EMD website search, PDF download, data extraction, compliance management.
PROJECT STRUCTURE
pool_scout_pro/
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
🔒 MANDATORY DEVELOPMENT RULES (STRICTLY ENFORCED)
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
Backup Protocol (MANDATORY)
bash# Before ANY changes to critical files
python3 -c "from backup_system import CodeBackupSystem; backup = CodeBackupSystem(); backup.backup_file('filename.py', 'reason')"
Quality Gates (ALL REQUIRED)
✅ Does service have single, clear responsibility?
✅ Are browser sessions guaranteed to clean up?
✅ Does workflow provide clear user feedback?
✅ Can phases fail independently without breaking system?
✅ Are we using real data from EMD (no fake IDs)?
✅ Are database names descriptive and clear?
✅ Do visual indicators provide immediate understanding?
Milestone Documentation Requirements
MUST INCLUDE:

Current technical status of all systems
Network configuration with IPs and ports
Database schema and any missing components
Service status and dependencies
Known issues with specific error details
File paths and storage configuration
Authentication and security setup

MUST NOT INCLUDE:

Congratulatory language or accomplishments
Marketing language or project praise
Historical progress narratives
Motivational content

DATABASE STRUCTURE
facilities table
sqlCREATE TABLE facilities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    address TEXT,
    establishment_id TEXT,
    permit_holder TEXT,
    phone TEXT,
    city TEXT,
    zip_code TEXT,
    program_identifier TEXT,
    policy_announcements TEXT,
    equipment_approvals TEXT,
    facility_comments TEXT,
    management_company_id INTEGER,
    current_operational_status TEXT DEFAULT 'open',
    facility_type TEXT DEFAULT 'POOL',
    street_address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (management_company_id) REFERENCES management_companies(id)
);
inspection_reports table
sqlCREATE TABLE inspection_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    facility_id INTEGER NOT NULL,
    permit_id TEXT,
    establishment_id TEXT,
    inspection_date TEXT,
    inspection_id TEXT,
    inspector_name TEXT,
    inspector_phone TEXT,
    accepted_by TEXT,
    total_violations INTEGER DEFAULT 0,
    major_violations INTEGER DEFAULT 0,
    severity_score REAL DEFAULT 0.0,
    closure_status TEXT DEFAULT 'operational',
    closure_reason TEXT,
    pdf_filename TEXT,
    report_notes TEXT,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (facility_id) REFERENCES facilities(id)
);
violations table
sqlCREATE TABLE violations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    facility_id INTEGER NOT NULL,
    violation_code TEXT,
    violation_title TEXT,
    violation_category TEXT,
    severity_level TEXT,
    observations TEXT,
    full_observations TEXT,
    code_description TEXT,
    full_code_description TEXT,
    correction_timeframe TEXT,
    repeat_violation BOOLEAN DEFAULT FALSE,
    repeat_count INTEGER DEFAULT 0,
    severity_score REAL DEFAULT 0.0,
    is_major_violation BOOLEAN DEFAULT FALSE,
    corrective_actions TEXT,
    FOREIGN KEY (report_id) REFERENCES inspection_reports(id),
    FOREIGN KEY (facility_id) REFERENCES facilities(id)
);
pool_equipment table
sqlCREATE TABLE pool_equipment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    facility_id INTEGER NOT NULL,
    capacity_gallons INTEGER,
    pump_gpm REAL,
    equipment_description TEXT,
    specialized_equipment TEXT,
    FOREIGN KEY (report_id) REFERENCES inspection_reports(id),
    FOREIGN KEY (facility_id) REFERENCES facilities(id)
);
water_chemistry table
sqlCREATE TABLE water_chemistry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    facility_id INTEGER NOT NULL,
    free_chlorine_ppm REAL,
    combined_chlorine_ppm REAL,
    ph_level REAL,
    cya_ppm REAL,
    pool_spa_temp_f REAL,
    flow_rate_gpm REAL,
    FOREIGN KEY (report_id) REFERENCES inspection_reports(id),
    FOREIGN KEY (facility_id) REFERENCES facilities(id)
);
CURRENT STATUS - August 08, 2025
NETWORK CONFIGURATION

Internal: 127.0.0.1:8765 (Gunicorn)
Local: http://10.10.10.80 (Nginx proxy)
Remote: http://parrotte.duckdns.org:8765
Container: localhost:4444 (Selenium)
NAS IP: 10.10.10.70
NAS Share: //10.10.10.70/homes/brian/pool_scout_pro/data
Server Mount: /mnt/nas-pool-data/
PDF Storage: /mnt/nas-pool-data/reports/2025/

SERVICES STATUS

pool-scout-pro.service: ACTIVE
nginx.service: ACTIVE
pool-scout-health.timer: ACTIVE
selenium-firefox: AUTO-MANAGED

OPERATIONAL SYSTEMS

EMD Search: ✅ Working - Date conversion with Pacific timezone, result extraction, debug logging
PDF Download Backend: ✅ Working - Browser navigation, PDF link extraction, file storage
PDF Text Extraction: ✅ Working - pypdfium2 integration, data parsing
Database Storage: ✅ Working - Complete schema, all required columns present
UI System: ✅ Working - Clean interface, responsive design, proper button sizing
Infrastructure: ✅ Active - Gunicorn, Nginx, health monitoring

CRITICAL ISSUES

Frontend Download Integration: ❌ FAILING - Downloads work via backend but UI reports 500 errors
Download Service Initialization: Frontend services (downloadService, apiClient) require manual instantiation
Real-time Progress: Missing download-poller.js for UI progress updates

FILENAME FORMAT

Current Implementation: YYYYMMDD_FACILITYNAME_SHORTID.pdf
Example: 20250807_LANDPARKVILLASLLC_EC63EEDCCFF2.pdf
Date Source: Search date (inspection_date) passed from search service
ID Extraction: Last segment after final dash in inspection ID

TIMEZONE HANDLING

Server Timezone: UTC
EMD Timezone: America/Los_Angeles (Pacific)
Conversion Method: DateUtilities.convert_to_pacific_date()
Dependencies: pytz library required

DEPLOYMENT COMMANDS
bash./manage.sh start    # Start system
./manage.sh status   # Check status
./manage.sh logs     # View logs
./manage.sh restart  # Restart services
DEPENDENCIES

Python: selenium, pytz, pypdfium2, requests, flask, gunicorn
System: docker (for Selenium), nginx, systemd
Storage: CIFS mount to NAS

NEXT PHASE
Frontend Download Integration - Fix UI/API connection for downloads, implement download progress polling
