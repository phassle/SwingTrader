#!/bin/bash
# SwingTrader daily scan — called by launchd
# Runs --full (scan + review + evaluate) once per day
# Skips if already run today (idempotent)

set -euo pipefail

PROJECT_DIR="/Users/perhassle/source/SwingTrader"
PYTHON="/Library/Frameworks/Python.framework/Versions/3.12/bin/python3"
LOG_DIR="$PROJECT_DIR/scans/logs"
SCANS_DIR="$PROJECT_DIR/scans"

mkdir -p "$LOG_DIR"

TODAY=$(date +%Y-%m-%d)
LOG_FILE="$LOG_DIR/scan_${TODAY}.log"

# Check if we already ran a scan today (look for scan_YYYY-MM-DD_*.json)
if ls "$SCANS_DIR"/scan_${TODAY}_*.json 1>/dev/null 2>&1; then
    echo "$(date): Scan already exists for $TODAY, skipping." >> "$LOG_FILE"
    exit 0
fi

echo "=== SwingTrader daily scan started at $(date) ===" >> "$LOG_FILE"

cd "$PROJECT_DIR"
PYTHONPATH=src "$PYTHON" -m swingtrader --full >> "$LOG_FILE" 2>&1

echo "=== Scan completed at $(date) ===" >> "$LOG_FILE"
