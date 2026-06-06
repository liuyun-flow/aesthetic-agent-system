@echo off
title Frontend :3000
cd /d E:\aesthetic-agent-system\frontend
set "PATH=C:\Users\Dream\AppData\Local\nodejs\node-v24.12.0-win-x64;%PATH%"
echo Starting Next.js dev server...
call npx next dev -p 3000
pause
