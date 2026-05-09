#!/bin/bash

PROJECT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_PATH" || { echo "Path not found: $PROJECT_PATH"; exit 1; }

STATE_FILE=".last_deployed_version"
CURRENT_VERSION=$(grep -E '^version:' pubspec.yaml | awk '{print $2}')

if [[ -z "$CURRENT_VERSION" ]]; then
    echo "Error: Could not find version in pubspec.yaml"
    exit 1
fi

LAST_VERSION="0.0.0"
if [[ -f "$STATE_FILE" ]]; then
    LAST_VERSION=$(cat "$STATE_FILE")
fi

echo "Current Frontend: $CURRENT_VERSION | Last Deployed: $LAST_VERSION"

if [[ "$CURRENT_VERSION" == "$LAST_VERSION" ]]; then
    echo "⚡ Version has not changed. Run ./bump.sh first if you want to deploy."
    exit 0
fi

echo "🌐 Deploying Frontend to Firebase..."
flutter build web --release || { echo "❌ Build failed"; exit 1; }
firebase deploy --only hosting || { echo "❌ Firebase deploy failed"; exit 1; }

echo "$CURRENT_VERSION" > "$STATE_FILE"
echo "✅ Frontend deployed successfully! Updated state to $CURRENT_VERSION."
