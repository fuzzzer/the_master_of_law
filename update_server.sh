#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "🚀 Fetching latest changes from git..."
git fetch origin main
git pull origin main

echo "🔄 Rebuilding and restarting backend container..."
# Build the new image and recreate the container in detached mode
# We only target the 'backend' service to prevent downtime for DB, Redis, etc.
cd backend
docker compose up -d --build backend

echo "🧹 Cleaning up old unused images to save disk space..."
docker image prune -f

echo "✅ Server successfully updated and running!"
