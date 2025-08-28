#!/bin/bash
case "$1" in
    finish)
        echo "🧪 Testing current changes..."
        if ! ./dev-tools/dev-workflow.sh restart; then
            echo "❌ Service failed to restart!"
            exit 1
        fi
        echo "✅ Service restart successful!"
        ;;
    *)
        echo "Available commands: finish"
        ;;
esac
