#!/bin/bash

# Pool Scout Pro - Enterprise Management Script
# Usage: ./manage.sh [command]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVICE_NAME="pool-scout-pro"
NGINX_SERVICE="nginx"
HEALTH_TIMER="pool-scout-health.timer"
CONTAINER_NAME="selenium-firefox"
LOG_DIR="/var/log/pool_scout_pro"
APP_URL="http://10.10.10.80"
DEV_PORT="5000"

print_header() {
    echo -e "${BLUE}=== Pool Scout Pro Management ===${NC}"
    echo ""
}

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_service_status() {
    local service=$1
    if systemctl is-active --quiet "$service"; then
        echo -e "${GREEN}ACTIVE${NC}"
    else
        echo -e "${RED}INACTIVE${NC}"
    fi
}

check_container_status() {
    if docker ps --format "table {{.Names}}" | grep -q "$CONTAINER_NAME"; then
        echo -e "${GREEN}RUNNING${NC}"
    else
        echo -e "${RED}STOPPED${NC}"
    fi
}

show_status() {
    print_header
    echo "Service Status:"
    echo "  Pool Scout Pro:    $(check_service_status $SERVICE_NAME)"
    echo "  Nginx:             $(check_service_status $NGINX_SERVICE)"
    echo "  Health Monitor:    $(check_service_status $HEALTH_TIMER)"
    echo "  Selenium Container: $(check_container_status)"
    echo ""
    echo "Access URLs:"
    echo "  Main App:      $APP_URL"
    echo "  Search Reports: $APP_URL/search-reports"
    echo ""
    echo "Log Files:"
    echo "  Error Log:     $LOG_DIR/error.log"
    echo "  Access Log:    $LOG_DIR/access.log"
}

start_services() {
    print_header
    print_status "Starting Pool Scout Pro Enterprise Stack..."
    
    # Start container first (auto-managed)
    print_status "Ensuring Selenium container is running..."
    if ! docker ps --format "table {{.Names}}" | grep -q "$CONTAINER_NAME"; then
        print_status "Starting Selenium container..."
        docker run -d --name $CONTAINER_NAME -p 4444:4444 --shm-size=2g selenium/standalone-firefox:latest || true
    fi
    
    # Start services
    print_status "Starting systemd services..."
    sudo systemctl start $NGINX_SERVICE
    sudo systemctl start $SERVICE_NAME
    sudo systemctl start $HEALTH_TIMER
    
    # Enable auto-start
    sudo systemctl enable $SERVICE_NAME
    sudo systemctl enable $HEALTH_TIMER
    
    sleep 3
    
    print_status "Enterprise stack started successfully!"
    echo ""
    show_status
    echo ""
    print_status "Access your application at: $APP_URL"
}

stop_services() {
    print_header
    print_status "Stopping Pool Scout Pro services..."
    
    sudo systemctl stop $SERVICE_NAME || true
    sudo systemctl stop $HEALTH_TIMER || true
    
    print_status "Services stopped successfully!"
}

restart_services() {
    print_header
    print_status "Restarting Pool Scout Pro..."
    
    sudo systemctl restart $SERVICE_NAME
    sudo systemctl restart $HEALTH_TIMER
    
    sleep 3
    print_status "Services restarted successfully!"
    show_status
}

show_logs() {
    print_header
    echo "Available log commands:"
    echo "  1. Live error log:    tail -f $LOG_DIR/error.log"
    echo "  2. Live access log:   tail -f $LOG_DIR/access.log"
    echo "  3. Service logs:      sudo journalctl -u $SERVICE_NAME -f"
    echo "  4. All recent errors: tail -50 $LOG_DIR/error.log"
    echo ""
    read -p "Enter choice (1-4) or press Enter to view recent errors: " choice
    
    case $choice in
        1) tail -f $LOG_DIR/error.log ;;
        2) tail -f $LOG_DIR/access.log ;;
        3) sudo journalctl -u $SERVICE_NAME -f ;;
        4|"") tail -50 $LOG_DIR/error.log ;;
        *) print_error "Invalid choice" ;;
    esac
}

dev_mode() {
    print_header
    print_warning "Switching to development mode..."
    print_warning "This will stop the enterprise stack!"
    
    read -p "Continue? (y/N): " confirm
    if [[ $confirm != [yY] ]]; then
        print_status "Cancelled."
        exit 0
    fi
    
    # Stop enterprise services
    print_status "Stopping enterprise services..."
    sudo systemctl stop $SERVICE_NAME || true
    sudo systemctl stop $NGINX_SERVICE || true
    
    print_status "Starting development server..."
    print_status "Access at: http://localhost:$DEV_PORT"
    print_warning "Press Ctrl+C to stop development server"
    echo ""
    
    cd "$(dirname "$0")"
    python3 src/web/app.py
}

backup_system() {
    print_header
    print_status "Creating system backup..."
    
    backup_dir="/tmp/pool-scout-backup-$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    
    # Backup code
    cp -r src/ "$backup_dir/" 2>/dev/null || true
    
    # Backup configs
    sudo cp /etc/systemd/system/$SERVICE_NAME.service "$backup_dir/" 2>/dev/null || true
    sudo cp /etc/nginx/sites-available/pool-scout-pro "$backup_dir/" 2>/dev/null || true
    
    # Backup database
    cp -r /mnt/nas-pool-data/ "$backup_dir/database/" 2>/dev/null || true
    
    print_status "Backup created at: $backup_dir"
}

show_help() {
    print_header
    echo "Usage: ./manage.sh [command]"
    echo ""
    echo "Commands:"
    echo "  start      Start Pool Scout Pro enterprise stack"
    echo "  stop       Stop Pool Scout Pro services"
    echo "  restart    Restart Pool Scout Pro services"
    echo "  status     Show system status"
    echo "  logs       View application logs"
    echo "  dev        Switch to development mode"
    echo "  backup     Create system backup"
    echo "  help       Show this help message"
    echo ""
    echo "Quick Start:"
    echo "  ./manage.sh start    # Start everything"
    echo "  ./manage.sh status   # Check status"
    echo "  ./manage.sh logs     # View logs"
}

# Main command handling
case "${1:-help}" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    dev)
        dev_mode
        ;;
    backup)
        backup_system
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
