#!/bin/bash
# One-shot wrapper to deploy both frontend and backend

PROJECT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "======================================"
echo "🚀 Checking Frontend Deployment..."
echo "======================================"
cd "$PROJECT_PATH/frontend" && ./deploy.sh

echo ""
echo "======================================"
echo "🚀 Checking Backend Deployment..."
echo "======================================"
cd "$PROJECT_PATH/backend" && ./deploy.sh

echo ""
echo "🎉 All deployments finished!"
