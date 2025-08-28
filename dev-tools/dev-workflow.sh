#!/bin/bash

echo "🛠️ DEV WORKFLOW COORDINATOR"
echo "=========================="

echo ""
echo "Available commands:"
echo "  validate <file>           - Check syntax only"
echo "  edit <target> <new>       - Safe file replacement"
echo "  patch <target> <patch>    - Apply patch with validation" 
echo "  rollback <file>           - Restore from latest backup"
echo "  restart                   - Restart the service"
echo "  status                    - Check service status"
echo ""

case "$1" in
    validate)
        ./dev-tools/validate-syntax.sh "$2"
        ;;
    edit)
        ./dev-tools/safe-edit.sh "$2" "$3"
        if [ $? -eq 0 ]; then
            case "$2" in
                *.js|*.py|*.html)
                    echo "Auto-restarting service after $2 modification..."
                    ./manage.sh restart
                    ;;
            esac
        fi
        ;;
    patch)
        ./dev-tools/safe-patch.sh "$2" "$3"
        ;;
    rollback)
        ./dev-tools/rollback.sh "$2"
        ;;
    restart)
        ./manage.sh restart
        ;;
    status)
        ./manage.sh status
        ;;
    *)
        echo "Unknown command: $1"
        echo "Use one of: validate, edit, patch, rollback, restart, status"
        exit 1
        ;;
esac
