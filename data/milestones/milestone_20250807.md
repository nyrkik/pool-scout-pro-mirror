# Pool Scout Pro - System Status & Configuration

## PROJECT OVERVIEW
Sacramento County pool inspection automation system - EMD website search, PDF download, data extraction, compliance management.

## PROJECT STRUCTURE
```
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
```

## 🔒 MANDATORY DEVELOPMENT RULES (STRICTLY ENFORCED)

### Code Update Strategy
❌ **NO surgical code changes** - leads to wasted time hunting syntax errors
❌ **NO partial snippets** or incomplete edits
❌ **NO sed commands** - breaks code syntax and indentation
❌ **NO "enhanced" code generation** without explicit request
❌ **NO code generation without user permission** - always ask first
❌ **NO assumptions or "improvements"** to working code - preserve exact logic

✅ **Complete file rewrites** using `cat > filename << 'EOF'`
✅ **Complete functions/modules/classes** as full units
✅ **Terminal-ready commands** for immediate copy/paste execution
✅ **Targeted section replacements** using cat with head/tail when appropriate

### Service Boundaries (ENFORCED)
❌ **NO business logic in route files** - routes call services only
❌ **NO mixed service concerns** - one service, one responsibility
❌ **NO "convenient" shortcuts** - maintain clean boundaries
❌ **NO code generation without backup** - always backup before changes

✅ **Services have single, clear purpose**
✅ **Easy to debug** - problems isolated to correct service
✅ **Clean separation of concerns**

### Backup Protocol (MANDATORY)
```bash
# Before ANY changes to critical files
python3 -c "from backup_system import CodeBackupSystem; backup = CodeBackupSystem(); backup.backup_file('filename.py', 'reason')"
```

### Quality Gates (ALL REQUIRED)
✅ Does service have single, clear responsibility?
✅ Are browser sessions guaranteed to clean up?
✅ Does workflow provide clear user feedback?
✅ Can phases fail independently without breaking system?
✅ Are we using real data from EMD (no fake IDs)?
✅ Are database names descriptive and clear?
✅ Do visual indicators provide immediate understanding?

## DATABASE STRUCTURE

### facilities table
```sql
CREATE TABLE facilities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    address TEXT,
    permit_id TEXT UNIQUE,
    program_identifier TEXT,
    current_operational_status TEXT DEFAULT 'unknown',
    closure_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### inspection_reports table
```sql
CREATE TABLE inspection_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    facility_id INTEGER,
    permit_id TEXT,
    inspection_id TEXT UNIQUE,
    inspection_date TEXT,
    inspection_type TEXT,
    total_violations INTEGER DEFAULT 0,
    major_violations INTEGER DEFAULT 0,
    severity_score REAL DEFAULT 0.0,
    closure_status TEXT DEFAULT 'operational',
    inspector_name TEXT,
    pdf_url TEXT,
    pdf_local_path TEXT,
    raw_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (facility_id) REFERENCES facilities (id)
);
```

### violations table
```sql
CREATE TABLE violations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER,
    violation_code TEXT,
    violation_title TEXT,
    violation_description TEXT,
    severity_level TEXT,
    severity_score REAL DEFAULT 0.0,
    is_repeat_violation BOOLEAN DEFAULT 0,
    corrected_date TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (report_id) REFERENCES inspection_reports (id)
);
```

### search_timings table
```sql
CREATE TABLE search_timings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    search_date TEXT,
    duration_seconds REAL,
    facility_count INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## CURRENT STATUS - August 07, 2025

### OPERATIONAL SYSTEMS
- EMD Search: ✅ Working - Date conversion, result extraction, debug logging
- UI System: ✅ Complete - Clean code, responsive design, proper button sizing  
- Infrastructure: ✅ Active - Gunicorn, Nginx, health monitoring
- Database: ✅ Ready - Schema created, local SQLite storage

### NETWORK CONFIGURATION
- Internal: 127.0.0.1:8765 (Gunicorn)
- Local: http://10.10.10.80 (Nginx proxy)
- Remote: http://parrotte.duckdns.org:8765
- Container: localhost:4444 (Selenium)
- Storage: data/reports.db

### SERVICES STATUS
- pool-scout-pro.service: ACTIVE
- nginx.service: ACTIVE
- pool-scout-health.timer: ACTIVE
- selenium-firefox: AUTO-MANAGED

### DEPLOYMENT COMMANDS
```bash
./manage.sh start    # Start system
./manage.sh status   # Check status  
./manage.sh logs     # View logs
```

### NEXT PHASE
**PDF Download System** - Ready for development
- Search provides facility data with PDF URLs
- Database schema supports report storage
- Infrastructure handles file processing
