#!/bin/bash
# run_app_flows.sh - the five app flows (key entry, saving a key, new case,
# chat, laws browser) against an in-memory fake backend. No key, no server.
#
#   scripts/run_app_flows.sh                 widget flows only (no device)
#   scripts/run_app_flows.sh -d <device-id>  also on a device or emulator
#   scripts/run_app_flows.sh -d chrome       also in Chrome (needs chromedriver)
#   scripts/run_app_flows.sh -d web-server   also headless web (needs chromedriver)
#
# Exits non-zero when any step fails; the last line is a one-line summary.
set -o pipefail

FRONTEND_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$FRONTEND_DIR" || exit 2

DEVICE=""
while [ $# -gt 0 ]; do
    case "$1" in
        -d|--device) DEVICE="$2"; shift 2 ;;
        -h|--help) sed -n '2,10p' "$0"; exit 0 ;;
        *) echo "Unknown argument: $1" >&2; exit 2 ;;
    esac
done

WIDGET_RESULT="not run"
DEVICE_RESULT="not run (no device given)"
FAILED=0

echo "== Widget flows: fvm flutter test test/app_flows"
if fvm flutter test test/app_flows; then
    WIDGET_RESULT="passed"
else
    WIDGET_RESULT="FAILED"
    FAILED=1
fi

run_web_drive() {
    if ! command -v chromedriver >/dev/null 2>&1; then
        DEVICE_RESULT="skipped on $DEVICE: chromedriver not installed"
        FAILED=1
        return
    fi
    chromedriver --port=4444 >/dev/null 2>&1 &
    local driver_pid=$!
    sleep 2
    local browser_args=()
    if [ "$DEVICE" = "web-server" ]; then
        browser_args=(--browser-name=chrome --headless)
    fi
    if fvm flutter drive \
        --driver=test_driver/integration_test.dart \
        --target=integration_test/app_flows_test.dart \
        -d "$DEVICE" "${browser_args[@]}"; then
        DEVICE_RESULT="passed on $DEVICE"
    else
        DEVICE_RESULT="FAILED on $DEVICE"
        FAILED=1
    fi
    kill "$driver_pid" 2>/dev/null
}

if [ -n "$DEVICE" ]; then
    echo "== Integration flows on $DEVICE"
    case "$DEVICE" in
        chrome|web-server) run_web_drive ;;
        *)
            if fvm flutter test integration_test/app_flows_test.dart -d "$DEVICE"; then
                DEVICE_RESULT="passed on $DEVICE"
            else
                DEVICE_RESULT="FAILED on $DEVICE"
                FAILED=1
            fi
            ;;
    esac
fi

if [ "$FAILED" -eq 0 ]; then STATUS="PASS"; else STATUS="FAIL"; fi
echo "APP FLOWS $STATUS: widget flows $WIDGET_RESULT; device flows $DEVICE_RESULT"
exit "$FAILED"
