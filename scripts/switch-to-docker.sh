#!/bin/bash
# Switch to Docker configuration

echo "🐳 Switching to Docker configuration..."

# Copy Docker environment file
cp ../.env.docker ../.env

echo "✅ Configuration switched to Docker"
echo "📋 Current settings:"
echo "   - Database: PostgreSQL in Docker (db:5432)"
echo "   - Environment: production"
echo "   - Port: 5000 (via Docker)"
echo ""
echo "🚀 To start Docker deployment:"
echo "   docker-compose up -d"
echo ""
echo "🌐 Access your app at:"
echo "   http://localhost (via nginx)"
echo "   http://localhost:5000 (direct)"