chcp 65001 >nul
@echo off
REM stop.bat — Stop the services
REM Double-click to run

cd /d "%~dp0.."

echo ============================================
echo  Aesthetic Training Agent System - 停止
echo ============================================

set COMPOSE_CMD=
docker compose version >nul 2>&1
if %errorlevel% equ 0 (
    set COMPOSE_CMD=docker compose
) else (
    docker-compose version >nul 2>&1
    if %errorlevel% equ 0 (
        set COMPOSE_CMD=docker-compose
    )
)

if not "%COMPOSE_CMD%"=="" (
    echo 正在停止 Docker 服务...
    call %COMPOSE_CMD% down
    echo [ OK ] 服务已停止
    echo.
    echo 数据保留在 backend\data\ 目录中，不会丢失。
    echo 重新启动: scripts\start.bat
) else (
    echo [提示] 未检测到 Docker，请手动停止进程。
)

pause
