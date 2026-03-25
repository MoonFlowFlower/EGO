#!/bin/bash
# EgoCore startup script with proper environment for Windows/Git Bash

# Get script directory (Windows format)
SCRIPT_DIR="D:/Project/AIProject/MyProject/Ego/EgoCore"
OPENEMOTION_DIR="D:/Project/AIProject/MyProject/Ego/OpenEmotion"

# Set Python path to include OpenEmotion (Windows format with semicolon)
export PYTHONPATH="${OPENEMOTION_DIR};${PYTHONPATH}"

echo "Starting EgoCore with Proto-Self support..."
echo "PYTHONPATH: ${PYTHONPATH}"

# Clean up any stale lock (Windows TEMP)
rm -f "${TEMP}/egocore-telegram-poller.lock" 2>/dev/null
rm -f "/c/Users/LEO/AppData/Local/Temp/egocore-telegram-poller.lock" 2>/dev/null

# Start EgoCore
cd "${SCRIPT_DIR}"
python -m app.main --telegram "$@"
