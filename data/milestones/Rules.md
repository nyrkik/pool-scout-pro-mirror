# Development Rules - Pool Scout Pro

## Code Generation and Permission
**#1: ALWAYS GET PERMISSION BEFORE GENERATING CODE**
Before any code is generated, confirm you understand the intent and get explicit permission. Never assume what code changes are needed.

## File Management and Backups
**#2: MANDATORY BACKUP WITH HARDCODED TIMESTAMPS**
When changing files, create a backup in `pool_scout_pro/backups/` with the original filename appended with a hardcoded datetime (not auto-generated). Format: `filename.YYYYMMDD_HHMMSS`
Example: `api_routes.py.20250819_203000`

**#3: INCREMENTAL DEVELOPMENT**
Execute one step at a time, confirming each change works before proceeding to the next step.

## Terminal Commands
**#4: COPY-PASTE READY COMMANDS**
Provide commands that can be copied directly from chat and pasted into terminal. All commands must run from project root directory. Combine logical steps into single terminal commands with proper error handling.

## File Editing Strategy
**#5: HYBRID FILE EDITING APPROACH**
- **Short files (<100 lines)**: Complete file replacement for reliability
- **Medium files (100-500 lines)**: Method/section replacement using line boundaries
- **Long files (>500 lines)**: External snippet files or extracted methods
- **Never use sed commands** - they cause syntax and indentation errors
- **Always use complete module/section replacements** to eliminate syntax errors

## Code Inspection Requirement
**#6: NEVER MODIFY FILES WITHOUT SEEING THEM FIRST**
Always examine the current file content before making changes. Never assume file structure or content. Ask to see files if not provided.

## Command Structure
**#7: CLEAR STEP DELINEATION**
Structure commands with clear step comments:
```bash
# Step 1: Backup the file
echo "Backing up api_routes.py..." && \
cp src/web/routes/api_routes.py backups/api_routes.py.20250819_203000 && \
# Step 2: Apply changes
cat > src/web/routes/api_routes.py << 'EOF' && \
[content]
EOF
# Step 3: Validate and restart if needed
python3 -c "import py_compile; py_compile.compile('file.py')" && \
./manage.sh restart
```

## File Editing Methods
**#8: NO sed COMMANDS FOR CODE CHANGES**
- ❌ Never use `sed` for multi-line code changes
- ❌ Never use surgical line edits that can break syntax
- ✅ Use complete file replacement with `cat > file << 'EOF'`
- ✅ Use head/tail/cat for section replacement when appropriate
- ✅ Create temporary files when needed, remove at end of script

## Syntax and Validation
**#9: ALWAYS VALIDATE SYNTAX**
After code changes, include syntax validation:
- Python: `python3 -c "import py_compile; py_compile.compile('file.py')"`
- JavaScript: `node -c file.js`
- Restart services if needed: `./manage.sh restart`

## Memory Efficiency
**#10: EFFICIENT CONTENT HANDLING**
For large files, generate commands without showing full content in chat. Use `cat > file << 'EOF'` approach to create files without consuming chat memory with large code blocks.
