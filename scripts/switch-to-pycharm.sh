#!/bin/bash
# Switch to PyCharm development configuration

echo "🐍 Switching to PyCharm development configuration..."

# Copy development environment file
cp ../.env.development ../.env

echo "✅ Configuration switched to PyCharm development"
echo "📋 Current settings:"
echo "   - Database: PostgreSQL on localhost:5432"
echo "   - Environment: development"
echo "   - Port: 5001 (via scripts/debug.py)"
echo ""
echo "🚀 To start PyCharm development:"
echo "   python scripts/debug.py"
echo "   OR run from PyCharm debugger"
echo ""
echo "🌐 Access your app at:"
echo "   http://localhost:5001"