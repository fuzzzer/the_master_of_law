#!/bin/bash

PROJECT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_PATH" || { echo "Path not found: $PROJECT_PATH"; exit 1; }

# Extract the current version from app/main.py
CURRENT_VERSION=$(grep -E '^\s*version=' app/main.py | awk -F'"' '{print $2}')

if [[ -z "$CURRENT_VERSION" ]]; then
    # Maybe it's defined inside the FastAPI constructor, let's search for version="X.Y.Z"
    CURRENT_VERSION=$(grep -oE 'version="([0-9]+)\.([0-9]+)\.([0-9]+)"' app/main.py | cut -d'"' -f2)
    if [[ -z "$CURRENT_VERSION" ]]; then
        echo "Error: Could not find version in app/main.py"
        exit 1
    fi
fi

if [[ "$CURRENT_VERSION" =~ ^([0-9]+)\.([0-9]+)\.([0-9]+)$ ]]; then
    MAJOR="${BASH_REMATCH[1]}"
    MINOR="${BASH_REMATCH[2]}"
    PATCH="${BASH_REMATCH[3]}"

    NEW_PATCH=$((PATCH + 1))
    NEW_VERSION="${MAJOR}.${MINOR}.${NEW_PATCH}"
else
    echo "Error: Version format in app/main.py is invalid: $CURRENT_VERSION"
    exit 1
fi

# Update the version in app/main.py
sed -i.bak "s/version=\"${CURRENT_VERSION}\"/version=\"${NEW_VERSION}\"/" app/main.py && rm app/main.py.bak

git fetch

if ! git merge-base --is-ancestor @{u} @; then
  echo "❌ Remote branch is ahead (or has diverged). Pull/rebase first."
  exit 1
fi
echo "✅ Local branch is up to date or ahead. Continuing…"

git add app/main.py
git commit -m "chore: bump backend version to ${NEW_VERSION}"
git tag "backend-v${NEW_VERSION}" -m "Backend version ${NEW_VERSION}"
git push
git push --tags

echo "Version updated to ${NEW_VERSION}, committed, and tagged successfully."
