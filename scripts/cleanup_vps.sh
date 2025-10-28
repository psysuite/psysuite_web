#!/bin/bash
# VPS Cleanup Script - Remove unnecessary files for production deployment

echo "🧹 Cleaning up VPS deployment..."

# Remove development environment
echo "Removing Python virtual environment..."
rm -rf ../venv/

# Remove IDE files
echo "Removing IDE files..."
rm -rf ../.idea/
rm -rf ../.vscode/

# Remove Python cache files
echo "Removing Python cache files..."
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null
find . -name "*.pyo" -delete 2>/dev/null

# Remove test files
echo "Removing test files..."
rm -rf ../tests/
rm -rf ../scripts/tests/
rm -rf ./tests/htmlcov/
rm -rf ../.pytest_cache/
rm -rf ./tests/.coverage
rm -f ../coverage.xml

# Remove documentation and design files
echo "Removing documentation files..."
rm -rf ../OT/
rm -rf ../docs/

# Remove development scripts
echo "Removing development scripts..."
rm -f ./debug.py
#rm -f ./db/clear_db.py
#rm -f ./db/recreate_db.py

# Remove development environment files
echo "Removing development environment files..."
rm -f ../.env.development

# Remove git repository
echo "Removing git repository..."
rm -rf ../.git/
rm -f ../.gitignore

# Remove build artifacts
echo "Removing build artifacts..."
rm -rf ../build/
rm -rf ../dist/
rm -rf ../*.egg-info/

# Remove this cleanup script itself
echo "Removing cleanup script..."
rm -f cleanup_vps.sh

echo "✅ VPS cleanup complete!"
echo ""
echo "📁 Remaining essential files:"
echo "   - Docker files (Dockerfile, docker-compose.yml, nginx.conf)"
echo "   - Application code (app/, run.py, config.py)"
echo "   - Production environment (.env)"
echo "   - Database initialization (init_db.py, scripts/db/init_db.py)"
echo "   - Requirements (requirements.txt)"
echo "   - Deployment script (deploy.sh)"
echo ""
echo "🚀 Ready for production deployment!"