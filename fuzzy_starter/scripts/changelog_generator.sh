#!/usr/bin/env bash
#
# scripts/changelog_generator.sh
# -----------------------------------------------------------------------------
# Generate changelogs with git‑cliff.
#
# Supported modes:
#   1. Range mode  – between two tags/refs
#        ./scripts/changelog_generator.sh <old_tag> <new_tag>
#        → scripts/changelog_outputs/CHANGELOG_<old>_to_<new>.md
#   2. Full‑history mode – entire repository
#        ./scripts/changelog_generator.sh --full
#        → scripts/changelog_outputs/CHANGELOG.md
# -----------------------------------------------------------------------------
set -euo pipefail

###############################################################################
# Usage & argument parsing                                                    #
###############################################################################

usage() {
  cat >&2 <<EOF
Usage:
  $0 <old_tag> <new_tag>   # changelog between versions
  $0 --full                # full changelog (HEAD..initial commit)
EOF
  exit 1
}

[[ $# -eq 1 && $1 == "--full" ]] || [[ $# -eq 2 ]] || usage

MODE="range"
OLD_TAG=""
NEW_TAG=""
if [[ $1 == "--full" ]]; then
  MODE="full"
else
  OLD_TAG="$1"
  NEW_TAG="$2"
fi

###############################################################################
# Preconditions                                                               #
###############################################################################

command -v git-cliff >/dev/null 2>&1 || {
  echo "Error: git-cliff is not installed. See https://github.com/orhun/git-cliff" >&2
  exit 1
}

git rev-parse --git-dir >/dev/null 2>&1 || {
  echo "Error: not inside a git repository." >&2
  exit 1
}

###############################################################################
# Paths                                                                       #
###############################################################################

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_PATH="$SCRIPT_DIR/git-cliff.toml"
OUT_DIR="$SCRIPT_DIR/changelog_outputs"
mkdir -p "$OUT_DIR"

if [[ $MODE == "range" ]]; then
  OUT_FILE="$OUT_DIR/CHANGELOG_${OLD_TAG}_to_${NEW_TAG}.md"
else
  OUT_FILE="$OUT_DIR/CHANGELOG.md"
fi

###############################################################################
# Generation                                                                  #
###############################################################################

TMP="$(mktemp)"
if [[ $MODE == "range" ]]; then
  # Generate changelog for specified tag range.
  git cliff --config "$CONFIG_PATH" \
            "$OLD_TAG..$NEW_TAG" \
            > "$TMP"
else
  # Full history (no range argument).
  git cliff --config "$CONFIG_PATH" > "$TMP"
fi

# Strip git‑cliff banner and prepend custom header.
{
  if [[ $MODE == "range" ]]; then
    printf "# Changelog from %s to %s\n\n" "$OLD_TAG" "$NEW_TAG"
  else
    printf "# Changelog\n\n"   # simple header for full history
  fi
  sed -n '/^## /,$p' "$TMP"
} > "$OUT_FILE"

rm -f "$TMP"

printf "Changelog written to %s\n" "$OUT_FILE"
