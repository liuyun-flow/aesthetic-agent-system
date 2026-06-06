#!/usr/bin/env bash
# kill_port.sh — Safely kill the process listening on a specific port.
# Usage: bash scripts/kill_port.sh 8000
#
# This avoids the dangerous "taskkill //IM python.exe" approach which
# kills ALL Python processes on the machine.
#
# Works on Windows (Git Bash/MSYS2) by parsing netstat output.

set -euo pipefail

PORT="${1:-}"
if [ -z "$PORT" ]; then
  echo "Usage: $0 <port>"
  exit 1
fi

echo "Looking for process on port $PORT..."

# netstat -ano: find the PID listening on this port
PID=$(netstat -ano 2>/dev/null | grep ":$PORT " | grep LISTENING | awk '{print $NF}' | head -1)

if [ -z "$PID" ]; then
  echo "No process found listening on port $PORT."
  exit 0
fi

echo "Found PID $PID on port $PORT. Killing..."
MSYS_NO_PATHCONV=1 taskkill //F //PID "$PID" 2>/dev/null

sleep 1
# Verify it's gone
if netstat -ano 2>/dev/null | grep -q ":$PORT .*LISTENING"; then
  echo "WARNING: Port $PORT may still be in use."
  exit 1
else
  echo "Port $PORT is now free."
fi
