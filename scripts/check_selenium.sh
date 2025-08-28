#!/bin/bash
# scripts/check_selenium.sh
# Quick status check script for Pool Scout Pro

echo "🔍 POOL SCOUT PRO - SYSTEM STATUS CHECK"
echo "======================================="

# Check Docker daemon
echo -n "Docker Daemon: "
if sudo docker info > /dev/null 2>&1; then
    echo "✅ Running"
else
    echo "❌ Not running"
    echo "  Fix: sudo systemctl start docker"
    exit 1
fi

# Check Docker container
echo -n "Selenium Container: "
if sudo docker ps --filter "name=pool-scout-selenium" --format "{{.Status}}" | grep -q "Up"; then
    echo "✅ Running"
elif sudo docker ps -a --filter "name=pool-scout-selenium" --format "{{.Status}}" | grep -q "Exited"; then
    echo "⚠️  Stopped (can restart)"
    echo "  Fix: sudo docker start pool-scout-selenium"
else
    echo "❌ Not found"
    echo "  Fix: Create new container with:"
    echo "  sudo docker run -d --name pool-scout-selenium --restart unless-stopped -p 4444:4444 -v \$(pwd)/data/reports/downloads:/home/seluser/Downloads selenium/standalone-firefox:latest"
fi

# Check port 4444
echo -n "Port 4444: "
if netstat -ln 2>/dev/null | grep -q ":4444"; then
    echo "✅ Open"
else
    echo "❌ Closed"
fi

# Check Selenium Grid
echo -n "Selenium Grid: "
if curl -s -f http://localhost:4444/wd/hub/status > /dev/null 2>&1; then
    if curl -s http://localhost:4444/wd/hub/status | grep -q '"ready":true'; then
        echo "✅ Ready"
    else
        echo "⚠️  Starting up..."
    fi
else
    echo "❌ Not responding"
fi

# Check downloads directory
echo -n "Downloads Directory: "
if [ -d "data/reports/downloads" ]; then
    file_count=$(find data/reports/downloads -name "*.pdf" | wc -l)
    echo "✅ Exists ($file_count PDFs)"
else
    echo "⚠️  Missing"
    echo "  Fix: mkdir -p data/reports/downloads"
fi

echo ""
echo "📊 QUICK STATS:"
echo "  Container ID: $(sudo docker ps --filter 'name=pool-scout-selenium' --format '{{.ID}}' 2>/dev/null || echo 'N/A')"
echo "  Uptime: $(sudo docker ps --filter 'name=pool-scout-selenium' --format '{{.Status}}' 2>/dev/null || echo 'N/A')"
echo "  Port Status: $(netstat -ln 2>/dev/null | grep :4444 | head -1 || echo 'Port not bound')"

echo ""
echo "🔧 QUICK COMMANDS:"
echo "  Full health check: python src/utils/health_check.py"
echo "  Start container: sudo docker start pool-scout-selenium"
echo "  Container logs: sudo docker logs pool-scout-selenium"
echo "  Flask with health check: python src/web/app.py"
