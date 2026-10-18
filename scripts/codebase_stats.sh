#!/bin/bash
# scripts/codebase_stats.sh
# Generates current stats for the codebase to keep documentation in sync.

cd "$(dirname "$0")/.." || exit 1

echo "=========================================="
echo "📊 CODEBASE STATS - FUZZZY LAW 📊"
echo "=========================================="
echo ""

echo "--- 🟢 BACKEND ---"
python_files=$(find backend/app -name "*.py" | wc -l | tr -d ' ')
lines_of_code=$(find backend/app -name "*.py" | xargs wc -l | tail -1 | awk '{print $1}')
echo "Python files:  $python_files"
echo "Lines of code: ~$lines_of_code"

endpoints=$(grep -r "@router\." backend/app/routes/ --include="*.py" | wc -l | tr -d ' ')
routers=$(find backend/app/routes -name "*.py" ! -name "__init__.py" | wc -l | tr -d ' ')
echo "Endpoints:     $endpoints (across $routers routers)"

services=$(find backend/app/services -name "*.py" ! -name "__init__.py" | wc -l | tr -d ' ')
echo "Services:      $services"

repos=$(find backend/app/repositories -name "*.py" ! -name "__init__.py" | wc -l | tr -d ' ')
echo "Repositories:  $repos"

models=$(find backend/app/models -name "*.py" ! -name "__init__.py" | wc -l | tr -d ' ')
echo "Models:        $models"

schemas=$(find backend/app/schemas -name "*.py" ! -name "__init__.py" | wc -l | tr -d ' ')
echo "Schemas:       $schemas"

test_files=$(find backend/tests -name "test_*.py" -o -name "*_test.py" | wc -l | tr -d ' ')
test_functions=$(find backend/tests -name "test_*.py" -o -name "*_test.py" | xargs grep -c "def test_\|async def test_" 2>/dev/null | awk -F: '{sum+=$2} END {print sum}')
echo "Test files:    $test_files"
echo "Test functions:$test_functions"

echo ""
echo "--- 🔵 FRONTEND (FLUTTER) ---"
if [ -d "frontend/lib/src/features" ]; then
  flutter_features=$(find frontend/lib/src/features -maxdepth 1 -mindepth 1 -type d | sed 's|frontend/lib/src/features/||' | sort | paste -sd "," - | sed 's/,/, /g')
  feature_count=$(find frontend/lib/src/features -maxdepth 1 -mindepth 1 -type d | wc -l | tr -d ' ')
  echo "Feature Count: $feature_count"
  echo "Features:      $flutter_features"
else
  echo "Features:      Not found"
fi

echo ""
echo "=========================================="
echo "📝 NEXT STEPS:"
echo "1. Compare these numbers with backend.md and project_status.md"
echo "2. If there's a mismatch, update the documentation files"
echo "3. Update the 'Last verified' date in the docs"
echo "=========================================="
