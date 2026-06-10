# Session Handoff — 2026-06-10

## Last Completed
- **V2.1.3: Released — GitHub Release created, 212 tests passed, all review fixes applied**

---

## V2.1.3 完整交付

V2.1.3 是本地发布包 / 跨平台部署验证版，经历三轮迭代后正式发布。

### 第一轮：发布包结构（初始实现）

- 新增 `.dockerignore` — 排除 `.env`、真实数据、`node_modules`、`.next`、`__pycache__`、`.pytest_cache`、`*.zip`
- 完善 `.gitignore` — 重新整理分类，加固 `backend/data/` 下 `.gitkeep` 例外规则
- 新增 `backend/data/database/.gitkeep`、`backend/data/uploads/.gitkeep`
- 新增 `docs/LOCAL_DEPLOYMENT.md` — Win/Mac/Linux 完整部署指南
- 新增 `docs/RELEASE_CHECKLIST.md` — 8 大类发布前检查清单
- README 第一屏重写 — 面向普通用户
- 版本号同步 v2.1.2 → v2.1.3（main.py / data_io.py / tests）
- 文档同步（CHANGELOG / RELEASE_NOTES / UPGRADE / ROADMAP / CLAUDE.md / AGENTS.md）

### 第二轮：Codex 审查修复（阻塞问题清零）

审查发现 2 个阻塞问题 + 8 个建议问题，全部修复：

**阻塞修复：**
- `/health` 和 `/system/status` 改用 `f"v{app.version}"`，不再硬编码（之前与 `/system/preflight` 不一致导致 2 test failures）
- V2.1.3 关键文件纳入 Git 跟踪（.dockerignore、.gitkeep ×2、LOCAL_DEPLOYMENT.md、RELEASE_CHECKLIST.md）

**建议修复：**
- start.bat 添加 30 次 curl /health 等待循环 + `setlocal enabledelayedexpansion`
- UPGRADE.md 备份提醒移到 git pull 之前
- PROJECT_STATUS.md 修正「无 stop.bat（已有）」自相矛盾条目
- RELEASE_CHECKLIST.md 修正 preflight Key 描述
- start_all.sh 移除硬编码 `C:/Users/Dream/...` 路径，改为 PATH 查找
- README 路径统一使用宿主机路径 `backend/data/...`（加注容器内路径）
- ROADMAP.md 移除 V2.1.1 过期「(当前版本)」标记
- test_api.py 新增 /health 版本断言

### 第三轮：编码修复（终端乱码）

- start.bat / stop.bat / restart.bat 从 UTF-8 转为 GBK 编码
- 原因：中国 Windows CMD 默认代码页为 GBK/CP936，UTF-8 文件会导致中文显示乱码且命令解析错误
- 去掉 `chcp 65001`（GBK 文件 + UTF-8 代码页 = 二次乱码）

### 发布

- Tag: `v2.1.3` → commit `04b0ca6`
- GitHub Release: https://github.com/liuyun-flow/aesthetic-agent-system/releases/tag/v2.1.3
- 源码包清洁度：184 files，仅 `.env.example` ×3（安全占位符），无 `.env`/`.db`/`app_config.json`/真实图片

---

## 修改的文件

| 文件 | 变更 |
|------|------|
| `.gitignore` | 重新整理，加固 data/ 下 .gitkeep 规则 |
| `.dockerignore` | **New** |
| `AGENTS.md` | 测试数 210→212 |
| `CLAUDE.md` | 版本线 +V2.1.2 +V2.1.3 |
| `PROJECT_STATUS.md` | 版本号 + 三轮变更详情 + 已知问题更新 |
| `README.md` | 第一屏重写 + 路径一致性 + 功能表补全 |
| `ROADMAP.md` | +V2.1.2 +V2.1.3 + 移除过期标记 |
| `backend/app/main.py` | version → v2.1.3; /health、/system/status → `f"v{app.version}"` |
| `backend/app/services/data_io.py` | EXPORT_VERSION → v2.1.3 |
| `backend/app/tests/test_api.py` | 4 处版本断言 + /health 新增 |
| `backend/app/tests/test_preflight.py` | 1 处版本断言 |
| `backend/data/database/.gitkeep` | **New** |
| `backend/data/uploads/.gitkeep` | **New** |
| `docs/CHANGELOG.md` | +V2.1.2 +V2.1.3 |
| `docs/LOCAL_DEPLOYMENT.md` | **New** — Win/Mac/Linux 完整部署指南 |
| `docs/RELEASE_CHECKLIST.md` | **New** — 8 大类发布前检查清单 |
| `docs/RELEASE_NOTES.md` | 重写为 V2.1.3 |
| `docs/SESSION_HANDOFF.md` | 本文档 |
| `docs/UPGRADE.md` | 补全升级路径 + 备份提醒提前 |
| `frontend/src/app/layout.tsx` | 注释微调 |
| `scripts/start.bat` | +健康检查等待 + GBK 编码 |
| `scripts/stop.bat` | GBK 编码 |
| `scripts/restart.bat` | GBK 编码 |
| `scripts/start_all.sh` | 移除硬编码本机路径 |

共 **26 files**，+900/-210 lines

---

## Test Results
- **212 passed**，1 warning（httpx deprecation）
- Docker compose config: ✅
- Bash 脚本语法: ✅
- GitHub Release 源码包敏感文件: ✅ 零命中

---

## 已知问题（V2.1.3 发布时）

1. GitHub push 需代理（127.0.0.1:7891），代理未运行时 push 失败
2. POST /settings/test-vision 只做文本 chat smoke test
3. 语义搜索为暴力余弦相似度，案例量 <1000 时够用
4. 导出不含 embeddings（导入后需重建索引）
5. 导入仅合并模式，不做覆盖/去重
6. 误判检测基于关键词规则（非 LLM）
7. preflight 返回本地绝对路径可能暴露用户名
8. Apple Silicon Mac 未经真实机器测试
9. 缺少 `scripts/package-release` 自动打包脚本

## Next Session
1. V2.2: 行业训练模板 / 图表可视化（折线图、雷达图）/ 案例库推荐
2. 或：补充 `scripts/package-release` 自动化发布脚本
3. 或：在真实 Mac 上做一次部署验收
