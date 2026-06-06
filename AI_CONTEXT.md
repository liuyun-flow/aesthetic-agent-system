# AI Context — 跨平台工程规范

本项目运行在 **Windows 宿主机**，但终端使用 **Git Bash (MSYS2)**。
以下三条规则是硬性底层规范，必须在每次开发和故障排查中严格遵守。

---

## 规则 1：统一网络寻址 — 禁用 localhost

**诊断**：Git Bash 下 `localhost` 常被解析为 IPv6 `::1`，导致向 IPv4 服务（如 `0.0.0.0:8000`）发起请求时出现 `ConnectionRefused`。

**规范**：
- 启动后端服务时使用 `--host 127.0.0.1` 或 `--host 0.0.0.0`
- 所有 curl / requests / fetch 测试请求使用 `127.0.0.1`
- 前端 `.env` 中 `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000`
- CORS 白名单保留 `localhost` 以便浏览器访问

**示例**：
```bash
# ✅ 正确
curl -s http://127.0.0.1:8000/health
uvicorn app.main:app --host 127.0.0.1 --port 8000

# ❌ 错误
curl -s http://localhost:8000/health
```

---

## 规则 2：禁用 MSYS2 隐式路径转换

**诊断**：Git Bash 调用 Windows 原生程序（`cmd.exe`）时会破坏嵌套引号并错误转换 POSIX 路径。

**规范**：
- 每次调用 `cmd.exe` 前必须加上 `MSYS_NO_PATHCONV=1`
- 使用 `cygpath -w` 转换路径时显式处理
- 标准语法：

```bash
# ✅ 正确
MSYS_NO_PATHCONV=1 cmd.exe //c "start \"Title\" /D \"$(cygpath -w "$PWD")\" command"

# ❌ 错误（路径被破坏，引号丢失）
cmd.exe //c "cd E:\project && npm run dev"
```

---

## 规则 3：精确进程管理 — 禁止镜像名批量杀进程

**诊断**：`taskkill //IM python.exe` 会杀死机器上所有 Python 进程，极度危险。

**规范**：
- **严禁** 使用 `taskkill //IM python.exe` 或 `taskkill //IM node.exe`
- 使用项目提供的 `scripts/kill_port.sh` 按端口精确清理
- 交互式 CLI 优先使用 `winpty` 包装启动

**使用方式**：
```bash
# 按端口精确杀进程
bash scripts/kill_port.sh 8000
bash scripts/kill_port.sh 3000

# 交互式启动（如需要）
winpty python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

---

## 标准服务启动流程

```bash
# 1. 清理旧进程（按端口）
bash scripts/kill_port.sh 8000
bash scripts/kill_port.sh 3000

# 2. 启动后端（在 backend 目录下）
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# 3. 启动前端（在新终端窗口中）
MSYS_NO_PATHCONV=1 cmd.exe //c "start \"Frontend\" /D \"$(cygpath -w "$PWD/../frontend")\" cmd.exe /c \"set PATH=%USERPROFILE%\\AppData\\Local\\nodejs\\node-v24.12.0-win-x64;%PATH% && npx next dev -p 3000\""

# 4. 验证
curl -s http://127.0.0.1:8000/health
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3000

# 5. 打开浏览器
MSYS_NO_PATHCONV=1 cmd.exe //c "start http://127.0.0.1:3000"
```

---

## 文件索引

| 文件 | 用途 |
|------|------|
| `scripts/kill_port.sh` | 按端口精确杀进程 |
| `AI_CONTEXT.md` | 本文档 — 跨平台工程规范 |
| `backend/.env` | 后端配置（API keys, DB path） |
| `frontend/.env` | 前端 API 地址（NEXT_PUBLIC_API_BASE_URL） |
