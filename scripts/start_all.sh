#!/usr/bin/env bash
# start_all.sh — Start both backend and frontend using pythonw (detached from Git Bash)
# Usage: bash scripts/start_all.sh [--open-browser]
#
# NOTE: This script uses pythonw.exe to detach processes from the terminal.
# If your Python is installed elsewhere, set PYTHON_HOME and NODE_HOME
# environment variables before running, e.g.:
#   PYTHON_HOME=C:/Python311 NODE_HOME=C:/nodejs bash scripts/start_all.sh

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Configurable paths — override via env vars for portability
PYTHON_HOME="${PYTHON_HOME:-C:/Users/Dream/AppData/Local/Programs/Python/Python311}"
NODE_HOME="${NODE_HOME:-C:/Users/Dream/AppData/Local/nodejs/node-v24.12.0-win-x64}"

PYTHONW="${PYTHON_HOME}/pythonw.exe"
PYTHON="${PYTHON_HOME}/python.exe"
NPX="${NODE_HOME}/npx.cmd"

# Fallback: try PATH if configured executables don't exist
if [ ! -f "$PYTHONW" ]; then
    PYTHONW="pythonw"
fi
if [ ! -f "$PYTHON" ]; then
    PYTHON="python"
fi

# Convert PROJECT_DIR to Windows path (pythonw needs C:\... not /c/...)
WIN_PROJECT_DIR="$(echo "$PROJECT_DIR" | sed 's|^/\([a-zA-Z]\)|\1:|;s|/|\\\\|g')"

echo "=== Starting backend on 127.0.0.1:8000 ==="
"$PYTHONW" -c "
import subprocess, os, sys
os.chdir(r'${WIN_PROJECT_DIR}\\\\backend')
subprocess.Popen([
    r'${PYTHON}',
    '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000'
], creationflags=0x00000008)
" &
sleep 3

echo "=== Starting frontend on 127.0.0.1:3000 ==="
"$PYTHONW" -c "
import subprocess, os
os.chdir(r'${WIN_PROJECT_DIR}\\\\frontend')
env = os.environ.copy()
env['PATH'] = r'${NODE_HOME};' + env.get('PATH', '')
subprocess.Popen([
    r'${NPX}', 'next', 'dev', '-p', '3000'
], env=env, creationflags=0x00000008)
" &
sleep 8

# Verify
echo ""
echo "=== Status ==="
netstat -ano 2>/dev/null | grep -E ":(8000|3000).*LISTENING" && echo "Both servers running!" || echo "Check ports manually"

if [ "${1:-}" = "--open-browser" ]; then
  MSYS_NO_PATHCONV=1 cmd.exe //c "start http://127.0.0.1:3000"
  echo "Browser opened."
fi
