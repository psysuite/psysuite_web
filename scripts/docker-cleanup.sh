#!/bin/bash

# Complete Docker cleanup script - removes everything related to the project

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

echo "🧹 Complete Docker Cleanup for PsySuite Web Manager"
echo "⚠️  This will remove ALL Docker containers, images, volumes, and networks related to this project"
echo ""

read -p "Are you sure you want to proceed? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cleanup cancelled."
    exit 0
fi

print_status "Starting complete Docker cleanup..."

# Stop and remove all containers for this project
print_status "Stopping and removing containers..."
docker-compose down --remove-orphans 2>/dev/null || true

# Remove all containers with web_app prefix
CONTAINERS=$(docker ps -a --filter "name=web_app" --format "{{.ID}}" 2>/dev/null)
if [ ! -z "$CONTAINERS" ]; then
    print_status "Removing project containers..."
    echo "$CONTAINERS" | xargs docker rm -f 2>/dev/null || true
fi

# Remove all volumes with web_app prefix
print_status "Removing project volumes..."
VOLUMES=$(docker volume ls --filter "name=web_app" --format "{{.Name}}" 2>/dev/null)
if [ ! -z "$VOLUMES" ]; then
    echo "$VOLUMES" | xargs docker volume rm -f 2>/dev/null || true
fi

# Remove all networks with web_app prefix
print_status "Removing project networks..."
NETWORKS=$(docker network ls --filter "name=web_app" --format "{{.ID}}" 2>/dev/null)
if [ ! -z "$NETWORKS" ]; then
    echo "$NETWORKS" | xargs docker network rm 2>/dev/null || true
fi

# Remove built images
print_status "Removing built images..."
IMAGES=$(docker images --filter "reference=web_app*" --format "{{.ID}}" 2>/dev/null)
if [ ! -z "$IMAGES" ]; then
    echo "$IMAGES" | xargs docker rmi -f 2>/dev/null || true
fi

# Clean up dangling images and build cache
print_status "Cleaning up dangling images and build cache..."
docker image prune -f 2>/dev/null || true
docker builder prune -f 2>/dev/null || true

# Remove any remaining anonymous volumes
print_status "Cleaning up anonymous volumes..."
docker volume prune -f 2>/dev/null || true

print_status "✅ Complete Docker cleanup finished!"
echo ""
print_status "🔍 Verification - checking for remaining resources:"

# Verify cleanup
REMAINING_CONTAINERS=$(docker ps -a --filter "name=web_app" --format "{{.Names}}" 2>/dev/null)
REMAINING_VOLUMES=$(docker volume ls --filter "name=web_app" --format "{{.Name}}" 2>/dev/null)
REMAINING_NETWORKS=$(docker network ls --filter "name=web_app" --format "{{.Name}}" 2>/dev/null)
REMAINING_IMAGES=$(docker images --filter "reference=web_app*" --format "{{.Repository}}:{{.Tag}}" 2>/dev/null)

if [ -z "$REMAINING_CONTAINERS" ] && [ -z "$REMAINING_VOLUMES" ] && [ -z "$REMAINING_NETWORKS" ] && [ -z "$REMAINING_IMAGES" ]; then
    print_status "✅ All project resources successfully removed"
else
    print_warning "Some resources may still exist:"
    [ ! -z "$REMAINING_CONTAINERS" ] && echo "  Containers: $REMAINING_CONTAINERS"
    [ ! -z "$REMAINING_VOLUMES" ] && echo "  Volumes: $REMAINING_VOLUMES"
    [ ! -z "$REMAINING_NETWORKS" ] && echo "  Networks: $REMAINING_NETWORKS"
    [ ! -z "$REMAINING_IMAGES" ] && echo "  Images: $REMAINING_IMAGES"
fi

echo ""
print_status "🚀 Ready for fresh deployment:"
print_status "   ./deploy.sh docker"