@echo off
REM restart.bat - Stop and restart the services

cd /d "%~dp0.."

call scripts\stop.bat
echo.
call scripts\start.bat
