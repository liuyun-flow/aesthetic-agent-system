#!/usr/bin/env bash
# stop.sh — Stop the aesthetic-agent-system services
# Usage: bash scripts/stop.sh

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

echo "============================================"
echo " Aesthetic Training Agent System — 停止服务"
echo "============================================"

COMPOSE_CMD=""
if docker compose version &> /dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
elif docker-compose version &> /dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
fi

if [ -n "$COMPOSE_CMD" ]; then
    echo "正在停止 Docker 服务..."
    $COMPOSE_CMD down
    echo "[✓] 服务已停止"
    echo ""
    echo "你的数据保留在 backend/data/ 目录中，不会丢失。"
    echo "重新启动: bash scripts/start.sh"
else
    echo "[提示] 未检测到 Docker。如果正在使用本地开发模式，请手动停止进程。"
fi
