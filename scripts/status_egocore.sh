#!/bin/bash
# EgoCore Status Check Script
# Usage: ./scripts/status_egocore.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
EGOCORE_DIR="$PROJECT_ROOT"
PID_FILE="$EGOCORE_DIR/logs/egocore.pid"
LOCK_FILE="${TEMP:-/tmp}/egocore-telegram-poller.lock"

echo "========================================"
echo "EgoCore Status"
echo "========================================"
echo "Time: $(date)"
echo ""

# Check PID file
PID=""
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE" 2>/dev/null || echo "")
fi

# Check if process is running
RUNNING=false
if [ -n "$PID" ]; then
    if ps -p "$PID" > /dev/null 2>&1; then
        RUNNING=true
    fi
fi

# Check lock file
LOCK_EXISTS=false
if [ -f "$LOCK_FILE" ]; then
    LOCK_EXISTS=true
fi

echo "[Process Status]"
if [ "$RUNNING" = true ]; then
    echo "  Status: RUNNING"
    echo "  PID: $PID"
    echo "  Uptime: $(ps -p $PID -o etime= 2>/dev/null || echo 'N/A')"
    echo "  CPU: $(ps -p $PID -o %cpu= 2>/dev/null || echo 'N/A')%"
    echo "  Memory: $(ps -p $PID -o %mem= 2>/dev/null || echo 'N/A')%"
else
    echo "  Status: STOPPED"
    if [ -n "$PID" ]; then
        echo "  PID File: $PID (stale)"
    fi
fi

echo ""
echo "[Lock Status]"
if [ "$LOCK_EXISTS" = true ]; then
    echo "  Lock File: EXISTS"
    echo "  Path: $LOCK_FILE"
    if [ -f "$LOCK_FILE" ]; then
        LOCK_CONTENT=$(cat "$LOCK_FILE" 2>/dev/null || echo "")
        echo "  Content: $LOCK_CONTENT"
    fi
else
    echo "  Lock File: NOT FOUND"
fi

echo ""
echo "[Log Files]"
LATEST_LOG=$(ls -t "$EGOCORE_DIR/logs/egocore_"*.log 2>/dev/null | head -1 || echo "")
if [ -n "$LATEST_LOG" ]; then
    echo "  Latest Log: $LATEST_LOG"
    echo "  Size: $(stat -c%s "$LATEST_LOG" 2>/dev/null || stat -f%z "$LATEST_LOG" 2>/dev/null || echo 'N/A') bytes"
    echo "  Modified: $(stat -c%y "$LATEST_LOG" 2>/dev/null || stat -f%Sm "$LATEST_LOG" 2>/dev/null || echo 'N/A')"
else
    echo "  No log files found"
fi

# Check Proto-Self trace
if [ -f "$EGOCORE_DIR/logs/proto_self_trace.jsonl" ]; then
    TRACE_ENTRIES=$(wc -l < "$EGOCORE_DIR/logs/proto_self_trace.jsonl")
    TRACE_SIZE=$(stat -c%s "$EGOCORE_DIR/logs/proto_self_trace.jsonl" 2>/dev/null || stat -f%z "$EGOCORE_DIR/logs/proto_self_trace.jsonl" 2>/dev/null || echo 'N/A')
    echo ""
    echo "[Proto-Self Trace]"
    echo "  File: logs/proto_self_trace.jsonl"
    echo "  Entries: $TRACE_ENTRIES"
    echo "  Size: $TRACE_SIZE bytes"
    echo "  Latest: $(tail -1 "$EGOCORE_DIR/logs/proto_self_trace.jsonl" 2>/dev/null | head -c 100)..."
fi

# Check State Mirror
if [ -f "$EGOCORE_DIR/artifacts/proto_self_mirror/state.json" ]; then
    STATE_SIZE=$(stat -c%s "$EGOCORE_DIR/artifacts/proto_self_mirror/state.json" 2>/dev/null || stat -f%z "$EGOCORE_DIR/artifacts/proto_self_mirror/state.json" 2>/dev/null || echo 'N/A')
    echo ""
    echo "[Proto-Self State]"
    echo "  File: artifacts/proto_self_mirror/state.json"
    echo "  Size: $STATE_SIZE bytes"
fi

echo ""
echo "========================================"

if [ "$RUNNING" = true ]; then
    echo "✓ EgoCore is running"
else
    echo "✗ EgoCore is stopped"
fi

echo ""
echo "Actions:"
echo "  Start:  ./scripts/start_egocore.sh"
echo "  Stop:   ./scripts/stop_egocore.sh"
echo "  Restart: ./scripts/stop_egocore.sh && ./scripts/start_egocore.sh"
