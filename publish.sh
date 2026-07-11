#!/usr/bin/env bash
# Update and start official Mealie production stack

echo "============================================="
echo "        Mealie - Production Updater          "
echo "============================================="

# 1. Verify Docker Daemon is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Error: Docker daemon is not running. Please start Docker first."
    exit 1
fi

# 2. Pull latest images
echo "Pulling latest images from GHCR..."
docker compose -f docker/docker-compose.yml pull

# 3. Start stack
echo "Starting Mealie production stack..."
docker compose -f docker/docker-compose.yml up -d

echo "============================================="
echo "🚀 Mealie Production is UP!"
echo "Web app URL: https://192.168.50.107:9925"
echo "To view logs: docker compose -f docker/docker-compose.yml logs -f"
echo "To stop app:  docker compose -f docker/docker-compose.yml stop"
echo "============================================="
