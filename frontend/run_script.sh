SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)/scripts"

if [ ! -d "$SCRIPT_DIR" ]; then
    echo "Error: scripts directory not found at $SCRIPT_DIR"
    exit 1
fi

source ./scripts/runner.sh "$SCRIPT_DIR/$@"