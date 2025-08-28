#!/bin/bash
# Pool Scout Pro Health Monitor
# Enterprise monitoring script for systemd integration

HEALTH_URL="http://127.0.0.1:7001/health"
LOG_FILE="/var/log/pool_scout_pro/health_monitor.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Test application health
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL" --max-time 10)

if [ "$HTTP_STATUS" = "200" ]; then
    echo "$TIMESTAMP [INFO] Health check passed (HTTP $HTTP_STATUS)" >> "$LOG_FILE"
    exit 0
else
    echo "$TIMESTAMP [ERROR] Health check failed (HTTP $HTTP_STATUS)" >> "$LOG_FILE"
    # Restart service on health failure
    systemctl restart pool-scout-pro.service
    echo "$TIMESTAMP [INFO] Service restarted due to health failure" >> "$LOG_FILE"
    exit 1
fi
