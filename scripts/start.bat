@echo off
REM start.bat — Windows one-click start (Docker)
REM Double-click to run from project root, or run from scripts\ directory

cd /d "%~dp0.."

echo ============================================
echo  Aesthetic Training Agent System - 启动
echo ============================================
echo.

REM 1. Check Docker
where docker >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Docker，请先安装 Docker Desktop。
    echo   https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)
echo [ OK ] Docker 已安装

REM detect compose command
set COMPOSE_CMD=
docker compose version >nul 2>&1
if %errorlevel% equ 0 (
    set COMPOSE_CMD=docker compose
) else (
    docker-compose version >nul 2>&1
    if %errorlevel% equ 0 (
        set COMPOSE_CMD=docker-compose
    ) else (
        echo [错误] 未检测到 docker compose，请更新 Docker Desktop。
        pause
        exit /b 1
    )
)
echo [ OK ] %COMPOSE_CMD% 可用

REM 2. Check .env
if not exist "backend\.env" (
    echo.
    echo [!] 未找到 backend\.env 配置文件。
    echo     正在从 backend\.env.example 复制模板...
    copy /y backend\.env.example backend\.env >nul
    echo [ OK ] 已创建 backend\.env
    echo.
    echo     *** 请编辑 backend\.env，至少设置 DEEPSEEK_API_KEY ***
    echo     编辑完成后重新运行 scripts\start.bat
    echo.
    pause
    exit /b 0
)
echo [ OK ] backend\.env 已存在

REM Check for old DATABASE_URL
findstr /c:"sqlite:///./aesthetic.db" backend\.env >nul 2>&1
if %errorlevel% equ 0 (
    echo.
    echo [!] 检测到旧版 DATABASE_URL=sqlite:///./aesthetic.db
    echo     在 Docker 下此路径不受 volume 保护，docker compose down 后数据可能丢失。
    echo     建议改为 DATABASE_URL=sqlite:///./data/database/aesthetic.db
    echo     详见 docs\UPGRADE.md
    echo.
)

REM 3. Create data directories
if not exist "backend\data\config"  mkdir backend\data\config
if not exist "backend\data\database" mkdir backend\data\database
if not exist "backend\data\uploads"  mkdir backend\data\uploads
echo [ OK ] 数据目录已就绪

REM 4. Start services
echo.
echo 正在启动服务（首次启动需要构建镜像，请稍候）...
call %COMPOSE_CMD% up --build -d
if %errorlevel% neq 0 (
    echo [错误] 启动失败，请检查 Docker 是否正在运行。
    pause
    exit /b 1
)

echo.
echo ============================================
echo   启动完成！
echo.
echo   前端: http://127.0.0.1:3000
echo   后端: http://127.0.0.1:8000
echo.
echo   首次使用请打开 http://127.0.0.1:3000/setup
echo ============================================
echo.
echo 查看日志: %COMPOSE_CMD% logs -f
echo 停止服务: scripts\stop.bat
pause
