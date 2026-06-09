# Session Handoff — 2026-06-10

## Last Completed
- **V2.1.2: Hotfix — Windows start.bat rewrite, chunk error recovery, Help refresh**

---

## V2.1.2 变更详情

V2.1.2 是本地发布体验热修复，修复三个实际使用中发现的阻塞问题。

### 1. Windows start.bat 纯 CMD 重写
- 全重写为纯 Windows CMD（无 bash 语法），双击 `scripts\start.bat` 即可执行
- `cd /d "%~dp0.."` 确保从项目根目录启动，与双击位置无关
- 动态检测 `docker compose` vs `docker-compose`
- .env 不存在时自动从 .env.example 复制并提示编辑 API Key
- 旧 DATABASE_URL 检测并提示迁移
- 错误时 pause，不会窗口一闪而过
- 新增 `scripts/stop.bat`、`scripts/restart.bat`

### 2. 前端 chunk 缓存自动恢复
- `frontend/src/app/layout.tsx` 添加全局 `unhandledrejection` 监听
- 捕获 `ChunkLoadError` / `Loading chunk failed` / `Failed to fetch dynamically imported module`
- 首次失败自动 `window.location.reload()`（sessionStorage 防无限循环）
- 二次失败替换页面为中文恢复指引（Ctrl+F5 / 清除缓存 / Docker 重启）

### 3. Help 页面内容刷新
- 新增 4 个 Section：语义搜索与 Embedding、训练效果评估、系统诊断、数据导入/导出
- 新增 6 个 FAQ：Embedding 是什么、语义搜索 vs 普通筛选、白屏崩溃、start.bat 打不开、Docker 没安装、API Key 安全

### 修改的文件

| 文件 | 变更 |
|------|------|
| `scripts/start.bat` | 纯 CMD 重写 |
| `scripts/stop.bat` | **New** |
| `scripts/restart.bat` | **New** |
| `frontend/src/app/layout.tsx` | +ChunkLoadError 全局兜底 |
| `frontend/src/app/help/page.tsx` | +4 Section + 6 FAQ |
| `backend/app/main.py` | version → v2.1.2 |
| `backend/app/services/data_io.py` | EXPORT_VERSION → v2.1.2 |
| `backend/app/tests/test_api.py` | 版本断言 |
| `backend/app/tests/test_preflight.py` | 版本断言 |
| `README.md` | 版本号 |

## Test Results
- **212 passed**, 1 warning
- Frontend build: ✅ 7 routes
- Docker compose config: ✅

## Local Services
- Backend: V2.1.1 (previous session, not restarted)
- Frontend: running on port 3000

## Known Remaining Issues
- start_all.sh is dev-only with hardcoded paths — not for end users
- WebSocket errors on settings page (cosmetic, not blocking)
- No charts in assessment (text-only progress bars)

## Next Session
1. Commit remaining doc updates (SESSION_HANDOFF, PROJECT_STATUS)
2. V2.2: Industry training templates, chart visualization for assessment
