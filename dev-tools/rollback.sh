#!/bin/bash
# Quick Rollback - Restore from latest backup

echo "🔙 QUICK ROLLBACK"
echo "================"

if [ $# -eq 0 ]; then
    echo "Usage: $0 <target-file>"
    echo "Example: $0 src/core/error_handler.py"
    exit 1
fi

TARGET="$1"
BACKUP_DIR="/mnt/nas/pool_scout_pro/backups"

if [ ! -f "$TARGET" ]; then
    echo "❌ Target file not found: $TARGET"
    exit 1
fi

# Find latest backup
LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/$(basename $TARGET).* 2>/dev/null | head -n1)

if [ -z "$LATEST_BACKUP" ]; then
    echo "❌ No backup found for $(basename $TARGET)"
    exit 1
fi

echo "🔙 Rolling back $TARGET"
echo "📦 Using backup: $LATEST_BACKUP"

cp "$LATEST_BACKUP" "$TARGET"

echo "✅ Rollback complete!"
echo "🔍 Validating restored file..."
./dev-tools/validate-syntax.sh "$TARGET"
