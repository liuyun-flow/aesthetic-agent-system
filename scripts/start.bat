@echo off
REM start.bat — Windows 一键启动脚本（Docker 方式）
REM 双击运行，或在终端中执行 scripts\start.bat

echo ============================================
echo  Aesthetic Training Agent System - 启动脚本
echo ============================================
echo.

REM 1. Check Docker
where docker >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Docker。请先安装 Docker Desktop：
    echo   https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)
echo [OK] Docker 已安装

docker compose version >nul 2>&1
if %errorlevel% neq 0 (
    docker-compose version >nul 2>&1
    if %errorlevel% neq 0 (
        echo [错误] 未检测到 docker compose。
        pause
        exit /b 1
    )
)
echo [OK] docker compose 可用

REM 2. Check .env
if not exist "backend\.env" (
    echo.
    echo [!] 未找到 backend\.env 配置文件。
    echo     正在从 backend\.env.example 复制模板...
    copy backend\.env.example backend\.env >nul
    echo [OK] 已创建 backend\.env
    echo.
    echo     ! 请编辑 backend\.env，至少设置 DEEPSEEK_API_KEY
    echo     编辑完成后双击 scripts\start.bat 重新启动
    echo.
    pause
    exit /b 0
)
echo [OK] backend\.env 已存在

REM 3. Create data directories
if not exist "backend\data\config" mkdir backend\data\config
if not exist "backend\data\database" mkdir backend\data\database
if not exist "backend\data\uploads" mkdir backend\data\uploads
echo [OK] 数据目录已就绪

REM 4. Start
echo.
echo 正在启动服务（首次启动需要构建镜像，请稍候）...
docker compose up --build -d
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
echo 查看日志: docker compose logs -f
echo 停止服务: docker compose down
pause
