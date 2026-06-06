#!/usr/bin/env bash
# start_all.sh — Start both backend and frontend using pythonw (detached from Git Bash)
# Usage: bash scripts/start_all.sh [--open-browser]

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PYTHON="C:/Users/Dream/AppData/Local/Programs/Python/Python311/pythonw.exe"
NODE="C:/Users/Dream/AppData/Local/nodejs/node-v24.12.0-win-x64"

echo "=== Starting backend on 127.0.0.1:8000 ==="
"$PYTHON" -c "
import subprocess, os
os.chdir(r'$PROJECT_DIR/backend')
subprocess.Popen([
    r'C:/Users/Dream/AppData/Local/Programs/Python/Python311/python.exe',
    '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000'
], creationflags=subprocess.CREATE_NEW_CONSOLE)
" &
sleep 3

echo "=== Starting frontend on 127.0.0.1:3000 ==="
"$PYTHON" -c "
import subprocess, os
os.chdir(r'$PROJECT_DIR/frontend')
env = os.environ.copy()
env['PATH'] = r'$NODE;' + env.get('PATH', '')
subprocess.Popen([
    r'$NODE/npx.cmd', 'next', 'dev', '-p', '3000'
], env=env, creationflags=subprocess.CREATE_NEW_CONSOLE)
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
