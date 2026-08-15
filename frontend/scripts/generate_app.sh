#!/bin/bash
# Generate directory structure for Fuzzzy Law
# Run from frontend/ directory

set -e

BASE="lib/src/features"

# Cases feature directories
mkdir -p "$BASE/cases/models"
mkdir -p "$BASE/cases/data/data_sources"
mkdir -p "$BASE/cases/data/repositories"
mkdir -p "$BASE/cases/bloc"
mkdir -p "$BASE/cases/view/pages"
mkdir -p "$BASE/cases/view/components"

# Consultation feature directories
mkdir -p "$BASE/consultation/models"
mkdir -p "$BASE/consultation/data/data_sources"
mkdir -p "$BASE/consultation/data/repositories"
mkdir -p "$BASE/consultation/bloc"
mkdir -p "$BASE/consultation/view/pages"
mkdir -p "$BASE/consultation/view/components"

# Laws feature directories
mkdir -p "$BASE/laws/models"
mkdir -p "$BASE/laws/data/data_sources"
mkdir -p "$BASE/laws/data/repositories"
mkdir -p "$BASE/laws/bloc"
mkdir -p "$BASE/laws/view/pages"
mkdir -p "$BASE/laws/view/components"

# Profile feature directories
mkdir -p "$BASE/profile/view/pages"
mkdir -p "$BASE/profile/view/components"

echo "✅ Directory structure created"
