#!/bin/bash
# Setup Git Development Workflow

echo "🌳 GIT WORKFLOW SETUP"
echo "===================="

# Create development branch
echo "🌿 Creating development branch..."
git checkout -b development 2>/dev/null || git checkout development

echo "✅ Development toolkit created!"
echo ""
echo "📋 USAGE EXAMPLES:"
echo "  ./dev-tools/dev-workflow.sh validate src/core/error_handler.py"
echo "  ./dev-tools/dev-workflow.sh edit src/core/error_handler.py /tmp/new_version.py"
echo "  ./dev-tools/dev-workflow.sh rollback src/core/error_handler.py"
echo "  ./dev-tools/dev-workflow.sh restart"
echo ""
echo "🎯 WORKFLOW:"
echo "1. Make changes on development branch"
echo "2. Validate with 'dev-workflow.sh validate'"
echo "3. Apply with 'dev-workflow.sh edit' or 'dev-workflow.sh patch'"
echo "4. Test with 'dev-workflow.sh restart'"
echo "5. Rollback if needed with 'dev-workflow.sh rollback'"
