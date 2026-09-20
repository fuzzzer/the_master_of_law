#!/bin/bash

PROJECT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_PATH" || { echo "Path not found: $PROJECT_PATH"; exit 1; }

STATE_FILE=".last_deployed_version"
CURRENT_VERSION=$(grep -oE 'version="([0-9]+)\.([0-9]+)\.([0-9]+)"' app/main.py | cut -d'"' -f2)

if [[ -z "$CURRENT_VERSION" ]]; then
    echo "Error: Could not find version in app/main.py"
    exit 1
fi

LAST_VERSION="0.0.0"
if [[ -f "$STATE_FILE" ]]; then
    LAST_VERSION=$(cat "$STATE_FILE")
fi

echo "Current Backend: $CURRENT_VERSION | Last Deployed: $LAST_VERSION"

if [[ "$CURRENT_VERSION" == "$LAST_VERSION" ]]; then
    echo "⚡ Version has not changed. Run ./bump.sh first if you want to deploy."
    exit 0
fi

echo "⚠️ Make sure you have pushed your changes to GitHub before deploying!"
echo "🖥️ Deploying Backend to Hetzner VPS..."

# Load deploy config (not tracked in git)
DEPLOY_ENV="$PROJECT_PATH/.deploy.env"
if [[ ! -f "$DEPLOY_ENV" ]]; then
    echo "❌ Missing .deploy.env — create it with VPS_HOST=<your-server-ip>"
    exit 1
fi
source "$DEPLOY_ENV"

VPS_USER="${VPS_USER:-fuzzzer}"
VPS_DIR="${VPS_DIR:-/var/www/fuzzzy_law}"

ssh -o StrictHostKeyChecking=no ${VPS_USER}@${VPS_HOST} "cd ${VPS_DIR} && git pull origin main && cd backend && docker compose build && docker compose up -d"

if [[ $? -eq 0 ]]; then
    echo "$CURRENT_VERSION" > "$STATE_FILE"
    echo "✅ Backend deployed successfully! Updated state to $CURRENT_VERSION."
else
    echo "❌ Deployment failed."
    exit 1
fi
