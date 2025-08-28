#!/bin/bash
# Monitor and clean stuck Selenium sessions

while true; do
    # Check if Selenium is ready
    READY=$(curl -s http://localhost:4444/status | jq -r '.value.ready')
    
    if [ "$READY" = "false" ]; then
        echo "$(date): Selenium not ready, restarting..."
        docker restart pool-scout-selenium
        sleep 15
    fi
    
    sleep 30  # Check every 30 seconds
done
