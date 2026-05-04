set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# if no env is found then run setup
if [[ ! -f "$SCRIPT_DIR/.venv/bin/activate" ]]; then
  echo "[runner.sh] No virtual environment found – running setup.sh first..."
  "$SCRIPT_DIR/setup.sh"
fi

source "$SCRIPT_DIR/.venv/bin/activate"
python3 "$@"