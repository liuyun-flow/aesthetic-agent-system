#!/usr/bin/env bash
# start_all.sh — [DEV ONLY] Start both backend and frontend locally (pythonw detached)
# Usage: bash scripts/start_all.sh [--open-browser]
#
# NOTE: This is a developer convenience script with hardcoded paths.
# For end users, use scripts/start.sh (Docker one-click) instead.
#
# NOTE: Uses pythonw.exe to detach processes from the terminal.
# If your Python is installed elsewhere, set PYTHON_HOME and NODE_HOME
# environment variables before running, e.g.:
#   PYTHON_HOME=C:/Python311 NODE_HOME=C:/nodejs bash scripts/start_all.sh

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Configurable paths — override via env vars for portability
PYTHON_HOME="${PYTHON_HOME:-C:/Users/Dream/AppData/Local/Programs/Python/Python311}"
NODE_HOME="${NODE_HOME:-C:/Users/Dream/AppData/Local/nodejs/node-v24.12.0-win-x64}"

PYTHON="${PYTHON_HOME}/python.exe"
PYTHONW="${PYTHON_HOME}/pythonw.exe"
NODE="${NODE_HOME}/node.exe"

# Fallback: try PATH if configured executables don't exist
if [ ! -f "$PYTHONW" ]; then
	PYTHONW="pythonw"
fi
if [ ! -f "$PYTHON" ]; then
	PYTHON="python"
fi
if [ ! -f "$NODE" ]; then
	NODE="node"
fi

# Kill existing processes on target ports
echo "=== Cleaning up existing processes ==="
"$PYTHON" -c "
import subprocess, sys
result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
killed = False
for port in ['8000', '3000']:
	for line in result.stdout.splitlines():
		if f':{port}' in line and 'LISTENING' in line:
			pid = line.strip().split()[-1]
			subprocess.run(['taskkill', '/PID', pid, '/F'], capture_output=True)
			print(f'Killed PID {pid} on port {port}', file=sys.stderr)
			killed = True
			break
if not killed:
	print('No existing processes to kill', file=sys.stderr)
"

# Start backend (pythonw detaches from terminal, no console window)
echo ""
echo "=== Starting backend on 127.0.0.1:8000 ==="
cd "$PROJECT_DIR/backend"
"$PYTHONW" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 > /dev/null 2>&1 &
sleep 3

# Start frontend (node directly — npx.cmd can't resolve node from Git Bash PATH)
echo "=== Starting frontend on 127.0.0.1:3000 ==="
cd "$PROJECT_DIR/frontend"
"$NODE" node_modules/next/dist/bin/next dev -p 3000 > /dev/null 2>&1 &
sleep 8

# Verify
echo ""
echo "=== Status ==="
netstat -ano 2>/dev/null | grep -E ":(8000|3000).*LISTENING" && echo "Both servers running!" || echo "Check ports manually"

if [ "${1:-}" = "--open-browser" ]; then
  MSYS_NO_PATHCONV=1 cmd.exe //c "start http://127.0.0.1:3000"
  echo "Browser opened."
fi
