#!/bin/bash
set -e

cmd=$1
shift || true

case $cmd in
  validate)
    ./validate-syntax.sh "$@"
    ;;
  edit)
    ./safe-edit.sh "$@"
    ;;
  patch)
    ./safe-patch.sh "$@"
    ;;
  rollback)
    ./rollback.sh "$@"
    ;;
  restart)
    ./workflow.sh restart
    ;;
  status)
    ./workflow.sh status
    ;;
  push)
    if [ -z "$1" ]; then
      echo "Usage: $0 push \"commit message\""
      exit 1
    fi
    COMMIT_MSG="$1"
    git add .
    git commit -m "$COMMIT_MSG"
    git push origin main
    git push mirror main
    ;;
  *)
    echo "Available commands:"
    echo "  validate <file>           - Check syntax only"
    echo "  edit <target> <new>       - Safe file replacement"
    echo "  patch <target> <patch>    - Apply patch with validation"
    echo "  rollback <file>           - Restore from latest backup"
    echo "  restart                   - Restart the service"
    echo "  status                    - Check service status"
    echo "  push \"msg\"               - Commit all changes and push to origin+mirror"
    echo
    echo "Unknown command: $cmd"
    echo "Use one of: validate, edit, patch, rollback, restart, status, push"
    ;;
esac
