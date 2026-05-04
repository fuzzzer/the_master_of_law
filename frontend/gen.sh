#!/bin/bash

################################################################################
# Mason Generator Shortcut (Run Only From Project Root)
#
# 📄 USAGE:
#   ./g.sh <brick_name> [--initial]

# add --initial flag only if running this for the first time
#
#   EXAMPLES:
#   ./g.sh remote_feature_template_brick
#     Generates new feature into 'lib/feature_name'

#   ./g.sh remote_feature_template_brick --initial
#     Runs 'mason get' in code_generators/
#     then generates new feature into 'lib/feature_name'
#
#
#  HOW IT WORKS:
#   - Always runs 'mason make' from project root
#   - Uses bricks inside 'code_generators'
#   - Bricks must be built with full path like 'lib/...'
################################################################################

# Always CD to code_generators for config
cd "$(dirname "$0")/code_generators"

# Run mason get if requested
if [[ "$2" == "--initial" ]]; then
  echo "🧱 Running mason get..."
  mason get
fi

# Brick name
BRICK=$1

echo "🚀 Generating brick '$BRICK' into project root..."
mason make "$BRICK" --output-dir ../
