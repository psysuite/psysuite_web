#!/bin/bash

# Complete Development Environment Cleanup Script
# Removes virtual environment and development database

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "🧹 Complete Development Environment Cleanup"
echo "⚠️  This will remove:"
echo "   - Python virtual environment (venv/)"
echo "   - Development database (psysuite_dev)"
echo "   - Development logs and cache files"
echo ""

read -p "Are you sure you want to proceed? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cleanup cancelled."
    exit 0
fi

print_status "Starting development environment cleanup..."

# 1. Remove Python virtual environment
if [ -d venv ]; then
    print_status "Removing Python virtual environment..."
    rm -rf venv
    print_status "✅ Virtual environment removed"
else
    print_status "ℹ️  No virtual environment found in current directory"
fi

# Check for venv in parent directory (if accessible)
if [ -d ../venv ]; then
    print_warning "Found virtual environment in parent directory (../venv)"
    read -p "Remove parent directory venv as well? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf ../venv
        print_status "✅ Parent virtual environment removed"
    fi
fi

# 2. Clean up Python cache files
print_status "Cleaning Python cache files..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "*.pyo" -delete 2>/dev/null || true
print_status "✅ Python cache files cleaned"

# 3. Remove development database (PostgreSQL)
print_status "Cleaning development database..."

# Check if PostgreSQL is available
if command -v psql >/dev/null 2>&1; then
    # Try to connect and drop the development database
    DB_NAME="psysuite_dev"
    DB_USER="psysuite_user"
    
    print_status "Attempting to drop development database: $DB_NAME"
    
    # Try to drop the database (will fail gracefully if doesn't exist)
    if psql -U postgres -c "DROP DATABASE IF EXISTS $DB_NAME;" 2>/dev/null; then
        print_status "✅ Development database '$DB_NAME' dropped successfully"
    elif sudo -u postgres psql -c "DROP DATABASE IF EXISTS $DB_NAME;" 2>/dev/null; then
        print_status "✅ Development database '$DB_NAME' dropped successfully (with sudo)"
    else
        print_warning "Could not drop database '$DB_NAME' - it may not exist or you may lack permissions"
        print_status "You can manually drop it with: sudo -u postgres psql -c \"DROP DATABASE IF EXISTS $DB_NAME;\""
    fi
    
    # Also try to drop the user (optional)
    if psql -U postgres -c "DROP USER IF EXISTS $DB_USER;" 2>/dev/null; then
        print_status "✅ Development database user '$DB_USER' dropped successfully"
    elif sudo -u postgres psql -c "DROP USER IF EXISTS $DB_USER;" 2>/dev/null; then
        print_status "✅ Development database user '$DB_USER' dropped successfully (with sudo)"
    else
        print_warning "Could not drop database user '$DB_USER' - it may not exist or may be in use"
    fi
else
    print_warning "PostgreSQL not found - skipping database cleanup"
    print_status "If you have PostgreSQL installed elsewhere, manually run:"
    print_status "  sudo -u postgres psql -c \"DROP DATABASE IF EXISTS psysuite_dev;\""
fi

# 4. Clean up log files
print_status "Cleaning log files..."
if [ -d logs ]; then
    rm -rf logs/*.log 2>/dev/null || true
    print_status "✅ Log files cleaned"
fi

# 5. Clean up instance directory
print_status "Cleaning instance directory..."
if [ -d instance ]; then
    rm -rf instance/*.db 2>/dev/null || true
    rm -rf instance/*.log 2>/dev/null || true
    print_status "✅ Instance directory cleaned"
fi

# 6. Clean up test artifacts
print_status "Cleaning test artifacts..."
rm -rf .pytest_cache 2>/dev/null || true
rm -rf htmlcov 2>/dev/null || true
rm -f .coverage 2>/dev/null || true
print_status "✅ Test artifacts cleaned"

# 7. Reset environment file
print_status "Resetting environment configuration..."
if [ -f .env ]; then
    print_warning "Found active .env file"
    read -p "Remove active .env file? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm .env
        print_status "✅ Active .env file removed"
    else
        print_status "ℹ️  Keeping active .env file"
    fi
fi

print_status "✅ Development environment cleanup completed!"
echo ""
print_status "🔍 Cleanup summary:"
print_status "   - Virtual environment: Removed"
print_status "   - Python cache files: Cleaned"
print_status "   - Development database: Attempted cleanup"
print_status "   - Log files: Cleaned"
print_status "   - Test artifacts: Cleaned"
echo ""
print_status "🚀 To set up development environment again:"
print_status "   ./deploy.sh traditional"