#!/usr/bin/env bash
# start.sh — One-click start for aesthetic-agent-system (Docker)
# Usage: bash scripts/start.sh

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

echo "============================================"
echo " Aesthetic Training Agent System — 启动脚本"
echo "============================================"
echo ""

# ── 0. Detect compose command (docker compose vs docker-compose) ───────
COMPOSE_CMD=""
if docker compose version &> /dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
elif docker-compose version &> /dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
fi

# ── 1. Check Docker ────────────────────────────────────────────────────
if ! command -v docker &> /dev/null; then
    echo "[错误] 未检测到 Docker。请先安装 Docker Desktop："
    echo "  https://www.docker.com/products/docker-desktop/"
    exit 1
fi
echo "[✓] Docker 已安装"

if [ -z "$COMPOSE_CMD" ]; then
    echo "[错误] 未检测到 docker compose。请更新 Docker Desktop 到最新版本。"
    exit 1
fi
echo "[✓] $COMPOSE_CMD 可用"

# ── 2. Check .env ──────────────────────────────────────────────────────
if [ ! -f "backend/.env" ]; then
    echo ""
    echo "[!] 未找到 backend/.env 配置文件。"
    echo "    正在从 backend/.env.example 复制模板..."
    cp backend/.env.example backend/.env
    echo "[✓] 已创建 backend/.env"
    echo ""
    echo "    ⚠️  请编辑 backend/.env，至少设置 DEEPSEEK_API_KEY："
    echo "    nano backend/.env"
    echo "    或"
    echo "    notepad backend\\\\.env"
    echo ""
    echo "    编辑完成后重新运行 bash scripts/start.sh"
    exit 0
fi
echo "[✓] backend/.env 已存在"

# ── 2b. Check for old DATABASE_URL ─────────────────────────────────────
if grep -q "sqlite:///\./aesthetic\.db" backend/.env 2>/dev/null; then
    echo ""
    echo "[!] 检测到旧版 DATABASE_URL=sqlite:///./aesthetic.db"
    echo "    旧路径在 Docker 下可能导致数据丢失。"
    echo "    建议改为：DATABASE_URL=sqlite:///./data/database/aesthetic.db"
    echo "    详见 docs/UPGRADE.md"
    echo ""
fi

# ── 3. Create data directories ─────────────────────────────────────────
mkdir -p backend/data/config
mkdir -p backend/data/database
mkdir -p backend/data/uploads
echo "[✓] 数据目录已就绪"

# ── 4. Start services ──────────────────────────────────────────────────
echo ""
echo "正在启动服务（首次启动需要构建镜像，请稍候）..."
$COMPOSE_CMD up --build -d

# ── 5. Wait for health ─────────────────────────────────────────────────
echo ""
echo "等待后端就绪..."
HEALTHY=0
for i in $(seq 1 30); do
    if curl -sf http://127.0.0.1:8000/health > /dev/null 2>&1; then
        echo "[✓] 后端就绪"
        HEALTHY=1
        break
    fi
    sleep 2
done

if [ "$HEALTHY" = "0" ]; then
    echo ""
    echo "[错误] 后端健康检查超时，请检查日志："
    echo "  $COMPOSE_CMD logs backend"
    exit 1
fi

echo ""
echo "============================================"
echo "  启动完成！"
echo ""
echo "  前端: http://127.0.0.1:3000"
echo "  后端: http://127.0.0.1:8000"
echo "  API 文档: http://127.0.0.1:8000/docs"
echo ""
echo "  首次使用请打开 http://127.0.0.1:3000/setup"
echo "============================================"
echo ""
echo "查看日志: $COMPOSE_CMD logs -f"
echo "停止服务: bash scripts/stop.sh"
