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

# The SDK is pinned by fvm (.fvm/fvm_config.json → 3.32.0) and there is no
# `flutter` on PATH on the machine this is run from, so a bare `flutter`
# here failed before it built anything. Prefer fvm, fall back to a global
# install for anyone who has one.
if command -v fvm >/dev/null 2>&1; then
    FLUTTER="fvm flutter"
elif command -v flutter >/dev/null 2>&1; then
    FLUTTER="flutter"
else
    echo "❌ No Flutter SDK found (looked for fvm, then flutter)"; exit 1
fi

$FLUTTER build web --release \
    --target lib/main_production.dart \
    || { echo "❌ Build failed"; exit 1; }

# Which project this lands in is decided by .firebaserc (currently
# `fuzzzylaws`). Named explicitly so a stale `firebase use` in the shell
# cannot redirect a release to another project.
firebase deploy --only hosting --project "$(python3 -c 'import json;print(json.load(open(".firebaserc"))["projects"]["default"])')" \
    || { echo "❌ Firebase deploy failed"; exit 1; }

echo "$CURRENT_VERSION" > "$STATE_FILE"
echo "✅ Frontend deployed successfully! Updated state to $CURRENT_VERSION."
