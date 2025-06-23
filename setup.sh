#!/bin/bash

# 🚀 Render Setup Script for Swarm Multi-Agent System
# This script verifies the environment and helps debug deployment issues

echo "🔧 Starting Render Setup Script..."

# Print Python environment info
echo "📋 Python Environment Information:"
echo "Python version: $(python --version)"
echo "Python path: $(which python)"
echo "Pip version: $(pip --version)"
echo "Working directory: $(pwd)"

# List directory contents to verify files
echo "📁 Project Structure:"
ls -la

# Check if critical files exist
echo "🔍 Checking Critical Files:"
critical_files=("app.py" "requirements.txt" "backend/main.py" "backend/__init__.py")
for file in "${critical_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file exists"
    else
        echo "❌ $file missing"
    fi
done

# Check Python package structure
echo "🐍 Checking Python Package Structure:"
python_dirs=("backend" "backend/services" "backend/utils")
for dir in "${python_dirs[@]}"; do
    init_file="$dir/__init__.py"
    if [ -f "$init_file" ]; then
        echo "✅ $init_file exists"
    else
        echo "❌ $init_file missing"
    fi
done

# Verify installed packages
echo "📦 Verifying Key Installed Packages:"
key_packages=("flask" "gunicorn" "psycopg2" "requests" "pydantic")
for package in "${key_packages[@]}"; do
    if pip list | grep -i "$package" > /dev/null 2>&1; then
        version=$(pip list | grep -i "$package" | awk '{print $2}')
        echo "✅ $package: $version"
    else
        echo "❌ $package not found"
    fi
done

# Test basic import capabilities
echo "🧪 Testing Basic Imports:"
test_imports=(
    "import flask"
    "import psycopg2"
    "import requests"
    "import pydantic"
    "import gunicorn"
)

for import_cmd in "${test_imports[@]}"; do
    if python -c "$import_cmd" 2>/dev/null; then
        echo "✅ $import_cmd"
    else
        echo "❌ $import_cmd failed"
    fi
done

# Test backend imports
echo "🔧 Testing Backend Imports:"
backend_imports=(
    "from backend.main import create_app"
    "from backend.utils.error_handler import SwarmError"
    "from backend.utils.service_utils import service_registry"
)

for import_cmd in "${backend_imports[@]}"; do
    if python -c "$import_cmd" 2>/dev/null; then
        echo "✅ $import_cmd"
    else
        echo "❌ $import_cmd failed"
        echo "   Attempting to diagnose..."
        python -c "$import_cmd"
    fi
done

# Check environment variables
echo "🌍 Environment Variables Check:"
env_vars=("PORT" "DATABASE_URL" "OPENROUTER_API_KEY" "SUPERMEMORY_API_KEY" "SUPERMEMORY_BASE_URL" "SECRET_KEY")
for var in "${env_vars[@]}"; do
    if [ -n "${!var}" ]; then
        if [ "$var" = "DATABASE_URL" ] || [ "$var" = "OPENROUTER_API_KEY" ] || [ "$var" = "SUPERMEMORY_API_KEY" ] || [ "$var" = "SECRET_KEY" ]; then
            echo "✅ $var: [SET - hidden for security]"
        else
            echo "✅ $var: ${!var}"
        fi
    else
        echo "⚠️ $var: not set"
    fi
done

# Test basic Flask app creation
echo "🧪 Testing Flask App Creation:"
if python -c "
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath('.')))
try:
    from backend.main import create_app
    app = create_app()
    print('✅ Flask app created successfully')
    print(f'App name: {app.name}')
    print(f'App config keys: {list(app.config.keys())}')
except Exception as e:
    print(f'❌ Flask app creation failed: {e}')
    import traceback
    traceback.print_exc()
" 2>/dev/null; then
    echo "✅ Basic Flask app test passed"
else
    echo "❌ Basic Flask app test failed"
    echo "   Running detailed diagnostics..."
    python -c "
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath('.')))
from backend.main import create_app
app = create_app()
"
fi

# Check disk space and memory
echo "💾 System Resources:"
echo "Disk usage: $(df -h . | tail -1 | awk '{print $5}') used"
echo "Available memory: $(free -h 2>/dev/null | grep '^Mem:' | awk '{print $7}' || echo 'N/A')"

# Final summary
echo "🎯 Setup Script Complete!"
echo "If any tests failed above, check the Render build logs for more details."
echo "Common issues:"
echo "  - Missing environment variables (check Render dashboard)"
echo "  - Import errors (check Python path and package structure)"
echo "  - Memory/resource constraints (upgrade Render plan if needed)"
echo ""
echo "🚀 Ready for deployment!"
