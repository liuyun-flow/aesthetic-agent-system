# V2.1.3 发布说明

## 关于本版本

V2.1.3 是**本地发布包 / 跨平台部署验证版**。专注把项目整理成别人可以下载、安装、启动、配置和试用的本地发布包。

这不是新功能版。没有新增训练功能。

## 本版本做了什么

### 发布包结构

- 新增 `.dockerignore` — 确保 Docker 构建镜像时不包含 `.env`、真实数据、`node_modules`、`__pycache__` 等
- 完善 `.gitignore` — 加固 `backend/data/` 下 `.gitkeep` 例外规则，确保目录结构可被 Git 追踪
- 完善 `backend/data/` 目录结构 — `config/`、`database/`、`uploads/` 三个子目录各有 `.gitkeep`
- 发布包 = 项目根目录去掉了 `.env`、真实数据库、真实上传图片、真实配置、`node_modules`、`.next`、`__pycache__` 的干净副本

### 部署文档

- 新增 `docs/LOCAL_DEPLOYMENT.md` — 完整部署指南，覆盖：
  - Windows 部署（Docker Desktop + 双击 start.bat）
  - Mac 部署（Docker Desktop for Mac + ./start.sh）
  - Linux 部署
  - API Key 配置说明（两种方式）
  - 数据目录说明
  - 常见问题（Docker、端口、白屏、备份、升级、卸载）
  - 端口说明
- README 第一屏重写 — 面向普通用户，一眼看懂这是什么、怎么用

### 发布验收

- 新增 `docs/RELEASE_CHECKLIST.md` — 发布前逐项确认清单，覆盖：
  - 安全检查（12 项）
  - 启动检查（9 项）
  - 停止与重启检查（4 项）
  - 功能检查（15 项）
  - 文档检查（13 项）
  - 后端测试 + 前端构建验证

### 版本同步

- `v2.1.2` → `v2.1.3`：main.py / data_io.py / test_api.py / test_preflight.py
- README / CHANGELOG / UPGRADE / PROJECT_STATUS / ROADMAP / SESSION_HANDOFF / CLAUDE.md / AGENTS.md

## 发布形态

V2.1.3 是 **Local Release**（本地部署版）。

- ✅ 用户下载 zip → 解压 → Docker Desktop 启动 → 配置 API Key → 使用
- ❌ 不是 SaaS
- ❌ 不做登录
- ❌ 不做云端存储

## 系统要求

- Docker Desktop（必须）
- DeepSeek API Key（必须）
- OpenAI API Key（可选，用于 Vision 和语义搜索）

## 从 V2.1.2 升级

```bash
git pull origin main
docker compose up --build -d
```

升级前务必先导出备份（设置页 → 数据管理 → 导出）。

详见 [升级指南](UPGRADE.md)。

## 已知限制

与 V2.1.2 相同：
- 误判检测基于关键词规则（非 LLM）
- 语义搜索需要 OpenAI API Key
- 导出不含 embeddings（导入后需重建索引）
- 导入为合并模式，不做去重
- Apple Silicon Mac 通过 Docker 理论上支持，但未经真实 Mac 完整测试

## 下一步

- V2.2：行业训练模板 / 图表可视化 / 案例库推荐
