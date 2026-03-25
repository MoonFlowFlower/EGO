#!/bin/bash
# EgoCore Production Stop Script
# Usage: ./scripts/stop_egocore.sh [--force]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
EGOCORE_DIR="$PROJECT_ROOT"
PID_FILE="$EGOCORE_DIR/logs/egocore.pid"
LOCK_FILE="${TEMP:-/tmp}/egocore-telegram-poller.lock"
FORCE=false

if [ "$1" = "--force" ]; then
    FORCE=true
fi

echo "========================================"
echo "EgoCore Stop"
echo "========================================"
echo "Time: $(date)"
echo ""

# Find PID
PID=""
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE" 2>/dev/null || echo "")
fi

# Also check for python processes
PYTHON_PIDS=$(ps aux | grep "python.*app.main" | grep -v grep | awk '{print $1}' || echo "")

echo "[1/3] Checking for running processes..."

if [ -n "$PID" ]; then
    echo "  Found PID file: $PID"
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "  Process $PID is running"
    else
        echo "  Process $PID not running (stale PID file)"
        PID=""
        rm -f "$PID_FILE"
    fi
fi

if [ -n "$PYTHON_PIDS" ]; then
    echo "  Found Python processes: $PYTHON_PIDS"
fi

# Stop processes
if [ -n "$PID" ] || [ -n "$PYTHON_PIDS" ]; then
    echo ""
    echo "[2/3] Stopping EgoCore..."

    # Try graceful stop first
    if [ -n "$PID" ]; then
        echo "  Sending SIGTERM to $PID..."
        kill "$PID" 2>/dev/null || true
    fi

    for py_pid in $PYTHON_PIDS; do
        if [ "$py_pid" != "$PID" ]; then
            echo "  Sending SIGTERM to $py_pid..."
            kill "$py_pid" 2>/dev/null || true
        fi
    done

    # Wait for graceful shutdown
    sleep 2

    # Check if still running
    STILL_RUNNING=""
    if [ -n "$PID" ] && ps -p "$PID" > /dev/null 2>&1; then
        STILL_RUNNING="$PID"
    fi

    for py_pid in $PYTHON_PIDS; do
        if ps -p "$py_pid" > /dev/null 2>&1; then
            STILL_RUNNING="$STILL_RUNNING $py_pid"
        fi
    done

    # Force kill if needed
    if [ -n "$STILL_RUNNING" ]; then
        if [ "$FORCE" = true ]; then
            echo "  Force killing: $STILL_RUNNING"
            for p in $STILL_RUNNING; do
                kill -9 "$p" 2>/dev/null || true
            done
            sleep 1
        else
            echo "  WARNING: Processes still running: $STILL_RUNNING"
            echo "  Use --force to force kill:"
            echo "    ./scripts/stop_egocore.sh --force"
        fi
    fi

    echo "  ✓ Stop signal sent"
else
    echo "  No running EgoCore processes found"
fi

# Clean up lock file
echo ""
echo "[3/3] Cleaning up lock file..."
if [ -f "$LOCK_FILE" ]; then
    rm -f "$LOCK_FILE"
    echo "  ✓ Lock file removed"
else
    echo "  No lock file found"
fi

# Remove PID file
rm -f "$PID_FILE"

echo ""
echo "========================================"
echo "✓ EgoCore stopped"
echo "========================================"
