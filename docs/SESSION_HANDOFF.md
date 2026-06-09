# Session Handoff — 2026-06-09

## Last Completed
- **V2.1.0: Local release edition — one-click startup, system diagnostics, installation UX**

---

## V2.1.0 变更

| 类别 | 变更 |
|------|------|
| 启动脚本 | `scripts/start.sh`（Docker 一键启动）、`scripts/stop.sh`（停止）、`scripts/start.bat`（Windows） |
| 系统预检 | `GET /system/preflight` — 数据库/配置/上传/DeepSeek/Vision/Embedding 综合诊断 |
| 设置页 | 新增「系统诊断」面板，调用 preflight，显示状态 + 中文建议 |
| 文档 | 新增 CHANGELOG.md、UPGRADE.md、RELEASE_NOTES.md |
| 版本 | v2.1.0 |

## Test Results
- **210 passed**, 1 warning
- Frontend build: ✅ 7 routes
- Docker compose config: ✅

## Next: V2.1.1 stability review
