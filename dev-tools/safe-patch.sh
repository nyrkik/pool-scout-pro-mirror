SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
#!/bin/bash
# Safe Patch - Apply git-style patches with validation

echo "🩹 SAFE PATCH TOOL"
echo "=================="

if [ $# -lt 2 ]; then
    echo "Usage: $0 <target-file> <patch-file>"
    echo "Example: $0 src/core/error_handler.py /tmp/error_handler.patch"
    exit 1
fi

TARGET="$1"
PATCH_FILE="$2"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

if [ ! -f "$TARGET" ]; then
    echo "❌ Target file not found: $TARGET"
    exit 1
fi

if [ ! -f "$PATCH_FILE" ]; then
    echo "❌ Patch file not found: $PATCH_FILE"
    exit 1
fi

# Step 1: Create backup
BACKUP_DIR="/mnt/nas/pool_scout_pro/backups"
mkdir -p "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/$(basename $TARGET).$TIMESTAMP"
cp "$TARGET" "$BACKUP_FILE"
echo "📦 Backup created: $BACKUP_FILE"

# Step 2: Apply patch
echo "🩹 Applying patch..."
if ! patch "$TARGET" < "$PATCH_FILE"; then
    echo "❌ Patch failed to apply!"
    cp "$BACKUP_FILE" "$TARGET"
    exit 1
fi

# Step 3: Validate patched file
echo "🔍 Validating patched file..."
if ! "$SCRIPT_DIR"/validate-syntax.sh "$TARGET"; then
    echo "❌ Patched file failed validation! Rolling back..."
    cp "$BACKUP_FILE" "$TARGET"
    echo "🔙 Rollback complete"
    exit 1
fi

echo "✅ Patch applied successfully!"
echo "🔙 Rollback command: cp $BACKUP_FILE $TARGET"
