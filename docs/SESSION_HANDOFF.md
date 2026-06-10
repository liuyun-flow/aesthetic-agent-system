# Session Handoff — 2026-06-10

## Last Completed
- **V2.1.3: Local Release Packaging — .dockerignore, deployment guide, release checklist, data dir hardening**

---

## V2.1.3 变更详情

V2.1.3 是本地发布包 / 跨平台部署验证版。不做新功能，专注于发布包结构、部署文档和安全检查。

### 1. 发布包结构加固
- 新增 `.dockerignore` — 排除 `.env`、真实数据、`node_modules`、`.next`、`__pycache__`、`.pytest_cache`、`*.zip` 等
- 完善 `.gitignore` — 重新整理为分类清晰的结构，加固 `backend/data/` 下 `.gitkeep` 例外规则
- 新增 `backend/data/database/.gitkeep`、`backend/data/uploads/.gitkeep` — 确保目录结构可被 Git 追踪

### 2. 部署文档
- 新增 `docs/LOCAL_DEPLOYMENT.md` — Windows / Mac / Linux 完整部署指南，含常见问题、端口说明、备份/升级/卸载说明
- README 第一屏重写 — 面向普通用户，包含：是什么、适合谁、2 分钟快速开始（Win/Mac）、关键信息速查表

### 3. 发布验收
- 新增 `docs/RELEASE_CHECKLIST.md` — 8 大类逐项确认清单（安全/启动/停止/功能/文档/测试/前端/最终确认）

### 4. 版本同步
- backend: main.py (v2.1.2→v2.1.3), data_io.py (EXPORT_VERSION), test_api.py (3 assertions + 1 new /health assertion), test_preflight.py (1 assertion)
- docs: CHANGELOG (+V2.1.2 +V2.1.3), RELEASE_NOTES (重写), UPGRADE (+V2.1.2→V2.1.3), SESSION_HANDOFF (本文档)
- root: README (第一屏 + 版本号), PROJECT_STATUS (版本号), ROADMAP (+V2.1.3), CLAUDE.md (版本线)

### 修改的文件

| 文件 | 变更 |
|------|------|
| `.gitignore` | 重新整理，加固 data/ 下 .gitkeep 规则 |
| `.dockerignore` | **New** |
| `backend/data/database/.gitkeep` | **New** |
| `backend/data/uploads/.gitkeep` | **New** |
| `backend/app/main.py` | version → v2.1.3 |
| `backend/app/services/data_io.py` | EXPORT_VERSION → v2.1.3 |
| `backend/app/tests/test_api.py` | 2 version assertions → v2.1.3 |
| `backend/app/tests/test_preflight.py` | 1 version assertion → v2.1.3 |
| `README.md` | 第一屏重写 + 版本号 + 功能表补全 |
| `docs/LOCAL_DEPLOYMENT.md` | **New** |
| `docs/RELEASE_CHECKLIST.md` | **New** |
| `docs/CHANGELOG.md` | +V2.1.2 +V2.1.3 |
| `docs/RELEASE_NOTES.md` | 重写为 V2.1.3 |
| `docs/UPGRADE.md` | +V2.1.1→V2.1.2 +V2.1.2→V2.1.3 |
| `docs/SESSION_HANDOFF.md` | 重写为 V2.1.3 |
| `PROJECT_STATUS.md` | 更新版本号 |
| `ROADMAP.md` | +V2.1.3 标记完成 |
| `CLAUDE.md` | +V2.1.3 |
| `AGENTS.md` | 版本号 + 测试数更新 |

## Test Results
- **待运行**（版本号变更后需重新跑测试）

## Next Session
1. 运行后端测试确认版本断言通过
2. 运行前端 build
3. docker compose config 验证
4. 按 RELEASE_CHECKLIST.md 逐项验收
5. Commit + push
6. V2.2: Industry training templates, chart visualization, case library recommendations
