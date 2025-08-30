SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
#!/bin/bash
# Safe Edit - Apply changes with validation and rollback

echo "⚡ SAFE EDIT TOOL"
echo "================"

if [ $# -lt 2 ]; then
   echo "Usage: $0 <target-file> <new-content-file>"
   echo "Example: $0 src/core/error_handler.py /tmp/new_error_handler.py"
   exit 1
fi

TARGET="$1"
NEW_CONTENT="$2"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

if [ ! -f "$TARGET" ]; then
   echo "❌ Target file not found: $TARGET"
   exit 1
fi

if [ ! -f "$NEW_CONTENT" ]; then
   echo "❌ New content file not found: $NEW_CONTENT"
   exit 1
fi

echo "🎯 Target: $TARGET"
echo "📝 New content: $NEW_CONTENT"

# Step 1: Create backup
BACKUP_DIR="/mnt/nas/pool_scout_pro/backups"
mkdir -p "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/$(basename $TARGET).$TIMESTAMP"
cp "$TARGET" "$BACKUP_FILE"
echo "📦 Backup created: $BACKUP_FILE"

# Step 2: Validate new content
echo "🔍 Validating new content..."
if ! "$SCRIPT_DIR"/validate-syntax.sh "$NEW_CONTENT"; then
   echo "❌ New content failed validation!"
   exit 1
fi

# Step 3: Apply change
echo "⚡ Applying change..."
cp "$NEW_CONTENT" "$TARGET"

# Step 4: Validate applied change
echo "🔍 Validating applied change..."
if ! "$SCRIPT_DIR"/validate-syntax.sh "$TARGET"; then
   echo "❌ Applied change failed validation! Rolling back..."
   cp "$BACKUP_FILE" "$TARGET"
   echo "🔙 Rollback complete"
   exit 1
fi

echo "✅ Change applied successfully!"
echo "🔙 Rollback command: cp $BACKUP_FILE $TARGET"
