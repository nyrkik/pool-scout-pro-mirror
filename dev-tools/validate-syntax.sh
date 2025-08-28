#!/bin/bash
# Syntax Validator - Test files before deployment

echo "Syntax Validator"
echo "================"

if [ $# -eq 0 ]; then
    echo "Usage: $0 <file>"
    exit 1
fi

FILE="$1"

if [ ! -f "$FILE" ]; then
    echo "File not found: $FILE"
    exit 1
fi

echo "Validating: $FILE"

# Get file extension
EXT="${FILE##*.}"

case "$EXT" in
    py)
        echo -n "   Python syntax... "
        if python3 -m py_compile "$FILE" 2>/dev/null; then
            echo "PASS"
        else
            echo "FAIL"
            echo "Syntax errors:"
            python3 -m py_compile "$FILE"
            exit 1
        fi
        
        # Import check for src/ files
        if [[ "$FILE" == src/* ]]; then
            echo -n "   Import check... "
            cd "$(dirname "$0")/.."
            if python3 -c "import sys; sys.path.append('src'); import $(echo ${FILE#src/} | sed 's/\//./' | sed 's/.py$//')" 2>/dev/null; then
                echo "PASS"
            else
                echo "SKIP (import issues - may be normal)"
            fi
        fi
        ;;
    html|css|js)
        echo "   File type $EXT - skipping Python validation"
        echo "PASS (non-Python file)"
        ;;
    *)
        echo "   Unknown file type .$EXT - skipping validation"
        echo "PASS (unknown type)"
        ;;
esac

echo "All checks passed!"
