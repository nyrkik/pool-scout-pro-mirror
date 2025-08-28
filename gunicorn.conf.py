# Gunicorn configuration for Pool Scout Pro

# Server socket
bind = "127.0.0.1:7001"
backlog = 2048

# Worker processes - FIXED: Use reasonable number instead of CPU * 2
workers = 1
worker_class = "sync"
worker_connections = 1000
timeout = 600
keepalive = 60
max_requests = 10000
max_requests_jitter = 50

# Restart workers after this many requests to prevent memory leaks
preload_app = True

# Logging
accesslog = "/var/log/pool_scout_pro/access.log"
errorlog = "/var/log/pool_scout_pro/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "pool_scout_pro"

# Daemon mode
daemon = False  # Systemd will handle daemonization

# User/group (will be set by systemd)
# user = "pool_scout"
# group = "pool_scout"

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Performance
enable_stdio_inheritance = True
