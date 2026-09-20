#!/bin/bash
set -e

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running."
    echo "👉 Please start Docker Desktop manually and then run this script again."
    exit 1
fi

echo "🚀 Starting backend development environment..."
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
