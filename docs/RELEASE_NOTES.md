# V2.5.0 发布说明

## 关于本版本

V2.5.0 是**信心（质量与可靠性）**版：在扩大受众前先锁住质量，让每次改动都有自动护栏、并能看清成本。无新增训练功能——这是工程与可靠性的一层。

完整逐项变更见 [CHANGELOG](CHANGELOG.md)；本文件只讲重点。

## 本版本做了什么

### 持续集成（CI）
- 新增 GitHub Actions（`.github/workflows/ci.yml`）：每次 push/PR 自动跑**后端 pytest（mocked，无需 key）+ 前端 Vitest 组件测试 + 构建 + Playwright E2E**。免费、确定性，不含付费 LLM。

### 视觉描述缓存（省钱省时）
- 同一张图在 vision provider + model 不变时**复用已存描述**，不再重复调用视觉 API。`POST /images/{id}/describe?refresh=true` 可强制重算。
- **评分不缓存**——评分的细微差异是训练信号，且缓存会破坏「再练一次」对比。

### 成本 / 延迟遥测
- 透明计量每次 LLM 调用的 token 与延迟 → `llm_usage` 表；`GET /system/usage` 聚合；**设置页新增「用量统计」面板**（总调用 / 总 token / 平均延迟 / 分模型）。

### 自动化测试
- 前端组件测试（Vitest + React Testing Library）覆盖关键交互（结果卡片、任务表单）。
- Playwright E2E 冒烟：启动整栈后核心路由渲染正常，**无需 API key**。

### 发布时校准评测
- 新增 `.github/workflows/evals.yml`：仅在**发布**（或手动触发）时跑 V2.4 评测台，需仓库 secret `DEEPSEEK_API_KEY`；`--check` 在成对判对率 <0.75 时让该 job 失败，作为发布门槛。**永不 gate PR**（付费 + 非确定性）。

## 发布形态

与既往一致，**本地部署版（Local Release）**：

- ✅ 用户下载 zip → 解压 → Docker Desktop 启动 → 配置 API Key → 使用
- ❌ 不是 SaaS / 不做登录 / 不做云端存储

## 系统要求

- Docker Desktop（必须）
- DeepSeek API Key（必须）
- OpenAI API Key（可选，用于 Vision 自动描述、语义搜索、可选的 Vision 直评）

## 从 V2.4.x 升级

```bash
git pull origin main
docker compose up --build -d
```

`llm_usage` 表与 `uploaded_images.vision_model` 列通过启动时自动迁移（`_migrate_v2_5`）添加，旧数据安全。升级前建议先导出备份（设置页 → 数据管理 → 导出）。详见 [升级指南](UPGRADE.md)。

## 已知限制

- on-release 评测要有意义，需先给仓库加 `DEEPSEEK_API_KEY` secret，并用真实样本替换 `backend/evals/gold/*.jsonl`（仍为合成脚手架，即 M-1）
- 维度评分衡量的是「作品质量」而非「判断力」（判断力分维度度量是后续工作）
- 误判检测基于关键词启发式（非 LLM）
- 语义搜索需要 OpenAI API Key；导出不含 embeddings；导入为合并模式不做去重
- Apple Silicon Mac 通过 Docker 理论上支持，但未经真实 Mac 完整测试

## 下一步

- M-1 真实校准基线（加 secret + 替换真实金标准）
- V2.7 触达：运行时可配 API base URL + 桌面打包
- ~V3.0 闭环：预置案例库 + top-N grounding + 结构化课程
