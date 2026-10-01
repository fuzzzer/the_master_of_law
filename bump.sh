#!/bin/bash
# One-shot wrapper to bump both frontend and backend versions

PROJECT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "======================================"
echo "🚀 Bumping Frontend..."
echo "======================================"
cd "$PROJECT_PATH/frontend" && ./bump.sh

echo ""
echo "======================================"
echo "🚀 Bumping Backend..."
echo "======================================"
cd "$PROJECT_PATH/backend" && ./bump.sh

echo ""
echo "🎉 All versions bumped."
