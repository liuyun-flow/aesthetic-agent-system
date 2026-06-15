# Aesthetic Training Agent System / 审美训练智能体系统

AI-assisted aesthetic judgment training.  
Train your eye, not just generate pretty output.  
AI 辅助审美判断力训练。训练你的眼力，而不只是生成好看的输出。

最新版本见 [Releases](https://github.com/liuyun-flow/aesthetic-agent-system/releases) 与 [变更日志](docs/CHANGELOG.md)。 | [部署指南](docs/LOCAL_DEPLOYMENT.md) | [升级指南](docs/UPGRADE.md) | [发布说明](docs/RELEASE_NOTES.md) | [路线图](ROADMAP.md)

---

## English

### What is this?

**Aesthetic Training Agent System** is a local AI tool that trains your *eye* for design quality.

Most AI design tools generate pretty output. This one trains **you** — it analyzes your visual work, compares your self-assessment against AI judgment, identifies your blind spots, and tells you exactly what to practice next.

### Who is this for?

Designers, art directors, photographers, and anyone who needs to sharpen their aesthetic judgment. If you can look at a design and feel "something is off" but can't articulate why, this tool helps you build that vocabulary.

### Quick Start (2 minutes)

**You need:**
- **Docker Desktop** (free) — handles all dependencies automatically
- **DeepSeek API Key** (required) — powers the aesthetic analysis. [Get one here](https://platform.deepseek.com/api_keys)
- **OpenAI API Key** (optional but recommended) — enables real image recognition and semantic search

**You don't need** Python, Node.js, or SQLite — Docker handles everything.

#### Windows
1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) and start it
2. Download and unzip the project
3. **Double-click `scripts\start.bat`**
4. Open http://localhost:3000 → Settings → configure your API keys
5. Start your first training session

#### Mac / Linux
```bash
# 1. Download and unzip the project
# 2. Open Terminal in the project directory
chmod +x scripts/start.sh
./scripts/start.sh
# 3. Open http://localhost:3000 → Settings → configure your API keys
```

**To stop:** `bash scripts/stop.sh` (Mac/Linux) or double-click `scripts\stop.bat` (Windows)

### What you need to know

| Question | Answer |
|----------|--------|
| Where is my data stored? | `backend/data/` directory on your computer — never in the cloud |
| Are my API keys safe? | Keys are stored only in your local `backend/data/config/`. Never exported to backups. Never sent to us. |
| What if something breaks? | Visit `/help` in the app, or read the [deployment guide](docs/LOCAL_DEPLOYMENT.md) |
| How do I back up? | Settings → Data Management → Export (saves everything except API keys) |
| Can I use it offline? | No — it needs DeepSeek API for aesthetic reasoning |

### Architecture

```
aesthetic-agent-system/
├── backend/                  # FastAPI + SQLite + DeepSeek API
│   ├── app/
│   │   ├── agents/           # Analyzer, Critic, Iterator, Comparator, Profile, ReferenceComparator
│   │   ├── vision/           # Pluggable VisionAdapter (placeholder/manual/openai/claude)
│   │   ├── db/               # SQLAlchemy models + migrations
│   │   ├── schemas/          # Pydantic request/response models
│   │   └── services/         # Session, image, reference case services
│   └── data/uploads/         # Uploaded images (git-ignored)
└── frontend/                 # Next.js 14 + TypeScript + Tailwind CSS
    └── src/
        ├── app/              # Page + layout
        ├── components/       # TaskForm, ResultCard, SessionList, ReferencePanel
        └── i18n/             # English / Chinese translations
```

### Local Development (without Docker)

##### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # edit .env — set DEEPSEEK_API_KEY
uvicorn app.main:app --reload    # http://127.0.0.1:8000
```

API docs: http://127.0.0.1:8000/docs

##### Frontend

```bash
cd frontend
npm install                      # if registry is slow: --registry https://registry.npmmirror.com
npm run dev                      # http://127.0.0.1:3000
```

> **Note:** The frontend connects to `http://127.0.0.1:8000` by default. Override via `NEXT_PUBLIC_API_BASE_URL`.

### Features by Version

| Version | Feature |
|---------|---------|
| V1.0 | `/analyze` `/critique` `/iterate` — 9-dimension aesthetic decomposition, scored critique, design iteration |
| V1.1 | User self-assessment → AI scoring → judgment gap analysis → Profile training feedback |
| V1.2 | Image upload (jpg/png/webp, 10MB), manual image description, `/uploads` static files |
| V1.3 | Pluggable VisionAdapter, `POST /images/{id}/describe`, auto-generate image descriptions |
| V1.4 | Reference case library (high/medium/low), `POST /compare-with-references`, aesthetic comparison training |
| V1.4.1 | Chinese UI, copyable prompt generation, session detail modal |
| V1.4.2 | OpenAI GPT-4o-mini Vision support |
| V1.4.3 | Vision status endpoint (`GET /vision/status`) |
| V1.5 | Training workbench (daily theme, stats, weekly review) |
| V1.5.1 | Reference case image upload + aesthetic annotations |
| V1.6 | Docker support (`docker compose up`), env config checker, data directory layout |
| V1.7 | Local settings page, BYOK config (`data/config/app_config.json`), test-connection buttons |
| V1.7.1 | Setup wizard (`/setup`), Help center (`/help`), config status bar, system status endpoint |
| V1.7.2 | Iteration direction selection, direction-based prompt generation, structured iteration fields |
| V1.8 | Data export/import (zip backup), semantic search over reference cases (embeddings), data management UI |
| V1.8.1 | Stability fixes, regression tests, pre-release cleanup |
| V1.9 | Case quality management (completeness scoring, training readiness, audit report, duplicate detection) |
| V1.9.1 | Stability fixes: aesthetic_level validation, null safety, audit field completion |
| V2.0 | Training effectiveness assessment (overview, mistake patterns, dimension scoring, period review) |
| V2.0.1 | Stability fixes: data-sufficiency threshold, selected_direction crash, import v2 compat |
| V2.1 | One-click startup scripts, system diagnostics panel, preflight endpoint, upgrade guide |
| V2.1.1 | Stability fixes: version sync (preflight uses app.version), doc accuracy, backup reminders |
| V2.1.2 | Hotfix: Windows start.bat pure CMD rewrite, chunk cache auto-recovery, Help content refresh |
| V2.1.3 | Local release packaging: deployment guide, release checklist, .dockerignore, data dir hardening |
| V2.2 | UX pass: staged AI progress + cancel, collapsible workbench, practice-again, paste/drag upload, assessment charts |
| V2.2.1 | Agent aesthetic core: shared design-knowledge base, calibrated scoring rubric, evidence rules |
| V2.3 | One-click add-to-library (prefill + confirm), description completeness meter + guided fill, vision commercial inference |
| V2.4 | Evaluation integrity: calibration/eval harness, stored AI dimension scores, aggregated 8-dimension assessment, optional vision-direct scoring |
| V2.4.1 | Review follow-ups: honest dimension labeling (work-quality, not ability), eval-metric unit tests, work-quality trend line, deterministic eval runs |
| V2.5 | Confidence: CI (GitHub Actions), vision-description caching, cost/latency telemetry, Vitest component tests, Playwright E2E, on-release calibration evals |

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/analyze` | Multi-dimensional aesthetic analysis |
| `POST` | `/critique` | Scored critique (1-10) with issues and fixes |
| `POST` | `/iterate` | 3-5 alternative design directions |
| `POST` | `/upload` | Upload an image (jpg/png/webp, max 10MB) |
| `POST` | `/images/{id}/describe` | Auto-generate structured image description (V1.3) |
| `GET` | `/profile` | User aesthetic profile from training history |
| `GET` | `/sessions` | Recent training records |
| `POST` | `/reference-cases` | Create a reference case (V1.4) |
| `GET` | `/reference-cases` | List/filter reference cases (V1.4) |
| `POST` | `/compare-with-references` | Compare user work vs reference library (V1.4) |
| `GET` | `/health` | Health check |
| `GET` | `/model/status` | DeepSeek model status |
| `GET` | `/vision/status` | Vision provider status |
| `GET` | `/settings` | Get current config (keys masked) |
| `POST` | `/settings` | Save/update config |
| `POST` | `/settings/clear-key` | Clear a specific config key |
| `POST` | `/settings/test-deepseek` | Test DeepSeek API connection |
| `POST` | `/settings/test-vision` | Test Vision provider connection |
| `GET` | `/system/status` | Consolidated status (backend/model/vision/db/uploads) (V1.7.1) |
| `GET` | `/setup/status` | Check if setup wizard completed (V1.7.1) |
| `POST` | `/setup/complete` | Mark setup wizard as done (V1.7.1) |
| `GET` | `/export` | Export all data as zip backup (V1.8) |
| `POST` | `/import` | Import data from zip backup (V1.8) |
| `POST` | `/reference-cases/reindex-embeddings` | Rebuild semantic search index (V1.8) |
| `POST` | `/reference-cases/search-semantic` | Semantic search over reference cases (V1.8) |
| `GET` | `/embedding/status` | Embedding provider config status (V1.8) |
| `GET` | `/reference-cases/audit` | Case library quality audit report (V1.9) |
| `GET` | `/assessment/overview` | Training effectiveness overview (V2.0) |
| `GET` | `/assessment/mistakes` | Common mistake patterns (V2.0) |
| `GET` | `/assessment/dimensions` | Aesthetic dimension scores (V2.0) |
| `GET` | `/assessment/report` | Period review report (V2.0) |
| `GET` | `/system/preflight` | Comprehensive environment diagnostic (V2.1) |

### One-Click Startup (V2.1)

Run `bash scripts/start.sh` (Mac/Linux) or double-click `scripts\start.bat` (Windows). The script automatically checks Docker, creates data directories, verifies the `.env` file, and starts both services. See [UPGRADE.md](docs/UPGRADE.md) for version upgrade instructions and [CHANGELOG.md](docs/CHANGELOG.md) for full version history.

### System Diagnostics (V2.1)

Open Settings → the "System Diagnostics" panel shows the real-time status of every component: backend, database, config directory, uploads directory, DeepSeek, Vision, and Embedding. Recommendations are displayed in Chinese. Also available programmatically via `GET /system/preflight`.

### Training Effectiveness Assessment (V2.0)

The assessment system evaluates your training progress using rule-based analytics (no LLM calls):

- **Overview (训练总览)** — Total sessions, recent activity, score gap trends, Chinese summary with next steps.
- **Mistake Patterns (常见误判)** — 10 keyword-based mistake types detected from judgment gaps, focus tags, and weaknesses. Each with severity, explanation, and targeted training suggestion.
- **Dimension Scores (能力维度)** — 7 aesthetic judgment dimensions scored 0-100: typography, color, composition, texture/material, price-band, commercial fit, and iteration judgment. Each with trend indicator.
- **Period Review (周期复盘)** — 7/30 day review reports with progress summary, weakest/strongest dimensions, top mistakes, training plan, and recommended themes.
- Visit `/assessment` for the full assessment dashboard with tabbed views.

### Case Quality Management (V1.9)

The case library now includes quality assessment for every reference case:

- **Completeness Score (完整度评分)** — Each case gets a 0-100 score calculated dynamically from 13 weighted fields. No database changes needed — it works with existing data.
- **Training Readiness (训练可用状态)** — A case is "training-ready" when it scores ≥75 and has an image, aesthetic level, description, and learning notes. Training-ready cases are prioritized in semantic search.
- **Audit Report (案例库体检)** — `GET /reference-cases/audit` returns a full quality report: completeness stats, missing-field breakdowns, possible duplicates, and actionable recommendations.
- **Audit Page (体检页面)** — Visit `/audit` for a dashboard showing case quality stats, missing-field categories, duplicate detection, and recommendations.
- **Duplicate Detection** — Two-tier approach: title token overlap (always available) + embedding cosine similarity (if configured). No crashes when embeddings are unavailable.

### First-Time Users (V1.7.1)

If you're new, open **http://127.0.0.1:3000/setup** — a 5-step wizard walks you through:

1. What this tool is (and what it's not)
2. How to get and configure API keys
3. Testing connections
4. How to complete your first training session
5. Ready to go

You can skip the wizard anytime. Find it again at `/setup` or via the `/help` page.

Visit **http://127.0.0.1:3000/help** for the full help center covering quick start, configuration, training workflow, reference library, prompts, backup, and FAQ.

### How to Verify Model Configuration

The config status bar on the workbench homepage shows at a glance:

- **DeepSeek**: Configured / Not configured
- **Vision**: Configured / Not configured / Placeholder mode
- **Database**: OK / Error
- **Uploads**: OK / Error

Or check programmatically: `GET /system/status` returns everything in one JSON response.

### Data Export / Import (V1.8)

Export your training data including reference cases, training sessions, prompts,
and uploaded images as a zip file. Use this for backup or migrating to a new computer.

```bash
# Download backup via browser
# Settings → Data Management → Export
# Or: curl http://127.0.0.1:8000/export -o backup.zip
```

Import merges data — it never overwrites. Image/case IDs are automatically remapped.

**Security:** Export packages contain a config summary (provider, model names) but **never include real API keys**. Imported data never overwrites your local API keys or config.

#### How to Migrate to a New Computer
1. On old machine: Settings → Export → download `aesthetic-backup.zip`
2. Copy the zip to the new machine
3. Start the app on the new machine and configure API keys
4. Settings → Import → upload the zip
5. Optional: go to Reference Cases → click "Rebuild Index" for semantic search

### Semantic Search over Reference Cases (V1.8)

Search your reference case library by describing what you're looking for, not just by category tags. Uses OpenAI `text-embedding-3-small` to compute similarity.

**Setup:**
```bash
# In backend/.env or Settings page:
EMBEDDING_PROVIDER=openai
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
# Also requires OPENAI_API_KEY (reuses Vision key)
```

**Usage:**
1. Go to Reference Cases section on the workbench
2. Type a natural language query (e.g., "高考直播封面，年轻有冲击力但不要廉价")
3. Click "Semantic Search"
4. Results show similarity scores and match reasons

If embeddings aren't configured, the system falls back to normal category/level filters — no crashes.

**Semantic Search vs. Regular Filters:**
- **Regular filters**: exact match on category, aesthetic level, price band
- **Semantic search**: matches by *meaning* — finds cases that feel similar even if their tags don't match

**Why no automatic external case search?** This tool is for training YOUR eye. Finding externally-hosted high-aesthetic examples is part of the learning process. The semantic search only searches cases YOU have curated.

### Training Workflow

1. **Describe a visual work** — paste a design description or upload an image
2. **Choose task type** — Analyze / Critique / Iterate
3. **(Optional) Self-assess** — score your work, list strengths/weaknesses/audience/price band
4. **AI responds** — structured analysis, scored critique, or design alternatives
5. **View the gap** — see what you got right, what you missed, commercial/aesthetic blind spots
6. **Check your profile** — the system tracks your patterns and suggests next-week focus
7. **Compare with references** — see how your work stacks up against curated high/medium/low examples

### Local Settings (BYOK) — V1.7

You can configure API keys through the frontend Settings page (`/settings`) instead of manually editing `.env` files.

**Config Priority:** `backend/data/config/app_config.json` (host) / `data/config/app_config.json` (container) > `.env` environment variables > hardcoded defaults

| Config Key | JSON Path | Env Fallback |
|------------|-----------|-------------|
| DeepSeek API Key | `deepseek.api_key` | `DEEPSEEK_API_KEY` |
| DeepSeek Base URL | `deepseek.base_url` | `DEEPSEEK_BASE_URL` |
| DeepSeek Default Model | `deepseek.default_model` | `DEEPSEEK_DEFAULT_MODEL` |
| DeepSeek Reasoning Model | `deepseek.reasoning_model` | `DEEPSEEK_REASONING_MODEL` |
| Vision Provider | `vision.provider` | `VISION_PROVIDER` |
| OpenAI API Key | `vision.openai_api_key` | `OPENAI_API_KEY` |
| OpenAI Vision Model | `vision.openai_vision_model` | `OPENAI_VISION_MODEL` |

**Security:** Keys are stored only on your server in `backend/data/config/app_config.json`. The Settings API returns masked keys (e.g., `sk-a***3f8b`). Keys are never saved to browser localStorage, never logged, and never exposed to the frontend.

### Environment Variables

| Variable | Default | Required |
|----------|---------|----------|
| `DEEPSEEK_API_KEY` | — | **Yes** (LLM calls) |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com` | No |
| `DEEPSEEK_DEFAULT_MODEL` | `deepseek-v4-flash` | No |
| `DEEPSEEK_REASONING_MODEL` | `deepseek-v4-pro` | No |
| `DATABASE_URL` | `sqlite:///./data/database/aesthetic.db` | No |
| `UPLOAD_DIR` | `./data/uploads` | No |
| `VISION_PROVIDER` | `placeholder` | No |
| `OPENAI_API_KEY` | — | If `VISION_PROVIDER=openai` |
| `OPENAI_VISION_MODEL` | `gpt-4o-mini` | No |
| `NEXT_PUBLIC_API_BASE_URL` | `http://127.0.0.1:8000` | No |

### Vision Provider

Set `VISION_PROVIDER` in your `.env`:

| Value | Description | Requires API Key |
|-------|-------------|-----------------|
| `placeholder` (default) | Mock structured descriptions — no real vision model | No |
| `manual` | V1.2 mode: user types the image description | No |
| `openai` | OpenAI GPT-4o-mini — real image-to-text | `OPENAI_API_KEY` |

> **⚠️ Important:** `placeholder` mode returns fake example descriptions that do NOT match your images. It is for development/demo only. Set `VISION_PROVIDER=openai` with a valid key for real visual recognition.

Check status: `GET /vision/status` shows current provider, whether it's configured, and missing keys if any.

### Running Tests

```bash
cd backend
pytest app/tests/ -v    # All tests use mocked agents — no API key needed
```

### Database & Data Directory

```
backend/data/
├── config/
│   └── app_config.json     # BYOK persistent config (V1.7)
├── database/
│   └── aesthetic.db        # SQLite database (git-ignored)
└── uploads/                # Uploaded images (git-ignored)
```

### Rebuilding the SQLite Database

If you upgrade and the table schema is incompatible, delete the database file and restart:

```bash
rm backend/data/database/aesthetic.db    # Linux/macOS
del backend\data\database\aesthetic.db   # Windows
# Restart the backend — tables are created automatically on startup
```

### Why This Matters

Most AI design tools generate pretty output. This system trains YOU —  
it shows you what you consistently miss, whether you over-focus on surface  
aesthetics and ignore commercial fit, and exactly what to practice next.

---

## 中文

### 这是什么？

一个 AI 驱动的审美训练系统，帮助你提升设计审美判断力。  
你描述视觉作品，AI 分析它，你自评，系统告诉你漏看了什么、误判了什么、下次该练什么。

### 架构

```
aesthetic-agent-system/
├── backend/                  # FastAPI + SQLite + DeepSeek API
│   ├── app/
│   │   ├── agents/           # 分析、评分、迭代、比较、画像、参考对比
│   │   ├── vision/           # 可插拔 VisionAdapter（placeholder/manual/openai/claude）
│   │   ├── db/               # SQLAlchemy 模型 + 自动迁移
│   │   ├── schemas/          # Pydantic 请求/响应模型
│   │   └── services/         # 会话、图片、参考案例服务
│   └── data/uploads/         # 上传的图片（git-ignored）
└── frontend/                 # Next.js 14 + TypeScript + Tailwind CSS
    └── src/
        ├── app/              # 页面 + 布局
        ├── components/       # 任务表单、结果卡片、历史列表、参考案例面板
        └── i18n/             # 中英文翻译
```

### 快速开始

#### Docker（推荐）— 一键启动

**你需要准备：**
- **Docker Desktop**（免费）— 自动处理所有依赖
- **DeepSeek API Key**（必需）— 驱动审美分析。[点击获取](https://platform.deepseek.com/api_keys)
- **OpenAI API Key**（可选但推荐）— 启用真实图片识别和语义搜索

**你不需要**安装 Python、Node.js 或 SQLite — Docker 全部搞定。

#### Windows
1. 安装 [Docker Desktop](https://www.docker.com/products/docker-desktop/) 并启动
2. 下载解压项目
3. **双击 `scripts\start.bat`**
4. 打开 http://localhost:3000 → 设置页 → 配置 API Key
5. 开始第一次训练

#### Mac / Linux
```bash
# 1. 下载解压项目
# 2. 打开终端进入项目目录
chmod +x scripts/start.sh
./scripts/start.sh
# 3. 打开 http://localhost:3000 → 设置页 → 配置 API Key
```

**停止服务：** `bash scripts/stop.sh`（Mac/Linux）或双击 `scripts\stop.bat`（Windows）

### 关键信息速查

| 问题 | 答案 |
|------|------|
| 数据存在哪？ | 你电脑上的 `backend/data/` 目录——绝不上传云端 |
| API Key 安全吗？ | Key 只存在本地 `backend/data/config/`。导出备份不包含密钥，不会发送给我们 |
| 出问题了怎么办？ | 在应用内访问 `/help`，或查看[部署指南](docs/LOCAL_DEPLOYMENT.md) |
| 如何备份？ | 设置 → 数据管理 → 导出（保存除 API Key 外的所有数据） |
| 能离线用吗？ | 不行——需要 DeepSeek API 做审美推理 |

### 各版本功能

| 版本 | 功能 |
|------|------|
| V1.0 | `/analyze` `/critique` `/iterate` — 9 维美学分解、打分、设计迭代 |
| V1.1 | 用户自评 → AI 评分 → 判断差异分析 → Profile 训练反馈 |
| V1.2 | 图片上传（jpg/png/webp，10MB），手动图片描述，`/uploads` 静态文件 |
| V1.3 | 可插拔 VisionAdapter，`POST /images/{id}/describe`，自动生成图片描述 |
| V1.4 | 参考案例库（high/medium/low），`POST /compare-with-references`，高低审美对比训练 |
| V1.4.1 | 中文 UI、可复制提示词生成、历史详情弹窗 |
| V1.4.2 | OpenAI GPT-4o-mini Vision 支持 |
| V1.4.3 | Vision 状态端点（`GET /vision/status`） |
| V1.5 | 训练工作台（每日主题、统计数据、每周复盘） |
| V1.5.1 | 参考案例图片上传 + 审美标注 |
| V1.6 | Docker 支持（`docker compose up`）、环境配置检查、数据目录整理 |
| V1.7 | 本地设置页、BYOK 配置（`data/config/app_config.json`）、测试连接按钮 |
| V1.7.1 | 首次使用向导（`/setup`）、帮助中心（`/help`）、配置状态条、系统状态端点 |
| V1.7.2 | 迭代方向选择、基于选中方向生成提示词、历史详情展示方向与提示词 |
| V1.8 | 数据导出/导入（zip 备份）、案例库语义搜索、数据管理 UI |
| V1.8.1 | 稳定性修复：版本统一、回归测试、导出包验证 |
| V1.9 | 案例库质量管理（完整度评分、训练可用判定、体检报告、重复检测）|
| V1.9.1 | 稳定性修复：aesthetic_level 验证统一、null 安全加固、audit 补全 |
| V2.0 | 训练效果评估系统（总览、误判统计、7 维评分、周期复盘）|
| V2.0.1 | 稳定性校准：双评分阈值、关键词精度、旧数据兼容 |
| V2.1 | 一键启动脚本、系统诊断面板、预检端点、升级指南 |
| V2.1.1 | 稳定性修复：版本同步、文档准确性、备份提醒 |
| V2.1.2 | 热修复：Windows start.bat 纯 CMD 重写、chunk 缓存恢复、Help 刷新 |
| V2.1.3 | 本地发布包：部署指南、发布清单、.dockerignore、数据目录加固 |
| V2.2 | 体验优化：分阶段进度+取消、折叠工作台、再练一次、粘贴/拖拽上传、评估图表 |
| V2.2.1 | Agent 审美内核：共享设计知识库、评分锚点+反通胀、证据规则 |
| V2.3 | 一键收入案例库（预填+确认）、描述完整度进度条+引导式补全、Vision 商业推测 |
| V2.4 | 信任度量：评测/校准台、存储真实维度分、聚合 8 维评估、可选 Vision 直评 |
| V2.4.1 | 复审收尾：诚实表述（作品质量≠判断力）、评测台单测、作品质量趋势、评测可复现 |
| V2.5 | 信心：CI（GitHub Actions）、视觉描述缓存、成本/延迟遥测、Vitest 组件测试、Playwright E2E、on-release 校准评测 |

### API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/analyze` | 多维度美学分析 |
| `POST` | `/critique` | 结构化评分（1-10）+ 问题 + 修复建议 |
| `POST` | `/iterate` | 3-5 个改版方向 |
| `POST` | `/upload` | 上传图片（jpg/png/webp，最大 10MB） |
| `POST` | `/images/{id}/describe` | 自动生成结构化图片描述（V1.3） |
| `GET` | `/profile` | 从训练历史生成的用户审美画像 |
| `GET` | `/sessions` | 最近训练记录 |
| `POST` | `/reference-cases` | 创建参考案例（V1.4） |
| `GET` | `/reference-cases` | 查看/筛选参考案例（V1.4） |
| `POST` | `/compare-with-references` | 用户作品 vs 参考案例库对比（V1.4） |
| `POST` | `/generate-prompt` | 生成可复制提示词；V1.7.2 支持 `selected_direction` + `session_id` |
| `GET` | `/training/today` | 今日训练主题与任务（V1.5） |
| `GET` | `/training/stats` | 训练统计数据（V1.5） |
| `GET` | `/training/weekly-review` | 每周复盘（V1.5） |
| `GET` | `/health` | 健康检查 |
| `GET` | `/model/status` | DeepSeek 模型状态 |
| `GET` | `/vision/status` | Vision 提供者状态 |
| `GET` | `/settings` | 获取当前配置（密钥脱敏） |
| `POST` | `/settings` | 保存/更新配置 |
| `POST` | `/settings/clear-key` | 清除指定密钥 |
| `POST` | `/settings/test-deepseek` | 测试 DeepSeek 连接 |
| `POST` | `/settings/test-vision` | 测试 Vision 连接 |
| `GET` | `/system/status` | 综合状态（后端/模型/Vision/数据库/上传目录）（V1.7.1） |
| `GET` | `/setup/status` | 检查首次向导是否完成（V1.7.1） |
| `POST` | `/setup/complete` | 标记向导完成（V1.7.1） |

### 首次使用（V1.7.1）— 面向新用户

如果你是第一次打开这个工具，访问 **http://127.0.0.1:3000/setup**，5 步向导会带你了解：

1. 这是什么工具（以及不是什么）
2. 如何获取并配置 API Key
3. 测试连接
4. 如何完成第一次审美训练
5. 准备就绪

向导可以随时跳过或重新打开。从 `/help` 页面也能重新启动向导。

访问 **http://127.0.0.1:3000/help** 查看完整的帮助中心，涵盖快速开始、配置 API Key、训练流程、参考案例库、迭代与提示词、历史记录、备份数据和常见问题。

### 如何判断模型配置是否成功

训练工作台顶部的配置状态条一目了然地显示：

- **DeepSeek**：已配置 / 未配置
- **Vision**：已配置 / 未配置 / 占位模式
- **数据库**：正常 / 异常
- **上传目录**：正常 / 异常

也可以通过接口查询：`GET /system/status` 一次性返回所有状态信息。

### 数据导出/导入（V1.8）

导出训练数据（参考案例、训练记录、提示词、上传图片）为 zip 备份包。用于备份或迁移到新电脑。

```bash
# 浏览器中下载
# 设置页 → 数据管理 → 导出
# 或：curl http://127.0.0.1:8000/export -o backup.zip
```

导入为「合并导入」，不会清空当前数据。图片和案例 ID 会自动重映射。

**安全说明：** 导出包包含配置摘要（provider、model 名称），但**永远不包含真实 API Key**。导入时不会覆盖本地 API Key 或配置。

#### 如何迁移到新电脑
1. 旧电脑：设置页 → 导出 → 下载 `aesthetic-backup.zip`
2. 复制 zip 到新电脑
3. 在新电脑启动应用并配置 API Key
4. 设置页 → 导入 → 上传 zip
5. 可选：前往参考案例库点击「重建语义索引」

### 案例库语义搜索（V1.8）

用自然语言搜索你收藏的参考案例，而不是只能按分类标签筛选。使用 OpenAI text-embedding-3-small 计算相似度。

**配置：**
```bash
# backend/.env 或设置页中配置：
EMBEDDING_PROVIDER=openai
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
# 同时需要 OPENAI_API_KEY（复用 Vision Key）
```

**使用：**
1. 在工作台的参考案例区域输入自然语言查询（如「高考直播封面，年轻有冲击力但不要廉价」）
2. 点击「语义搜索」
3. 结果显示相似度百分比和匹配原因

如果未配置 embedding，系统会自动降级为普通分类筛选——不会崩溃。

**语义搜索 vs 普通筛选：**
- **普通筛选**：按分类、审美等级、价格带精确匹配
- **语义搜索**：按*含义*匹配——找到"感觉相似"的案例，即使标签不完全匹配

**为什么不做外部案例自动搜索？** 这个工具的目的是训练你的眼力。自己去发现和收藏高审美案例本身就是训练的一部分。语义搜索只搜索你亲手建立和策展的案例库。

### 训练流程

1. **描述一个视觉作品** — 粘贴设计描述或上传图片
2. **选择任务类型** — 分析 / 评分 / 迭代
3. **（可选）自我评估** — 打分，列出优缺点、目标用户、价格带
4. **AI 返回结果** — 结构化分析、打分评论、或设计改版方向
5. **查看差异** — 看你对在哪、漏了什么、商业/美学盲点
6. **查看画像** — 系统跟踪你的模式，给出下周训练重点
7. **与参考案例对比** — 看看你的作品和高/中/低审美案例的差距

### 迭代方向与提示词（V1.7.2）

当任务类型选择“迭代”时，系统会返回 3-5 个结构化改版方向。每个方向包含目标、视觉改动、色彩改动、字体改动、版式改动、商业理由和风险。

你可以选择其中一个方向，然后点击“基于该方向生成提示词”。前端会把当前训练记录的 `session_id` 和选中的 `selected_direction` 一起发送给后端，后端会围绕该方向生成提示词，并保存回对应的 iterate 历史记录。

历史详情中可以查看当时所有迭代方向、用户选择的方向，以及对应生成的中文提示词、英文提示词、反向提示词、设计师执行说明、文案优化提示和使用建议。旧历史记录没有这些字段时仍可正常打开。

### 环境变量

| 变量 | 默认值 | 是否必需 |
|------|--------|----------|
| `DEEPSEEK_API_KEY` | — | **是**（LLM 调用需要） |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com` | 否 |
| `DEEPSEEK_DEFAULT_MODEL` | `deepseek-v4-flash` | 否 |
| `DEEPSEEK_REASONING_MODEL` | `deepseek-v4-pro` | 否 |
| `DATABASE_URL` | `sqlite:///./data/database/aesthetic.db` | 否 |
| `UPLOAD_DIR` | `./data/uploads` | 否 |
| `VISION_PROVIDER` | `placeholder` | 否 |
| `OPENAI_API_KEY` | — | 若 `VISION_PROVIDER=openai` |
| `OPENAI_VISION_MODEL` | `gpt-4o-mini` | 否 |
| `NEXT_PUBLIC_API_BASE_URL` | `http://127.0.0.1:8000` | 否 |

### 视觉提供者

在 `.env` 中设置 `VISION_PROVIDER`：

| 值 | 说明 | 需要 API Key |
|----|------|-------------|
| `placeholder`（默认） | Mock 结构化描述 — 不调用真实视觉模型 | 否 |
| `manual` | V1.2 模式：用户手动输入图片描述 | 否 |
| `openai` | OpenAI GPT-4o-mini — 真实图片识别 | `OPENAI_API_KEY` |

> **⚠️ 注意：** `placeholder` 模式返回的是固定示例描述，与你的实际图片不匹配。仅供开发/演示使用。如需真实视觉识别，请设置 `VISION_PROVIDER=openai` 并配置有效的 API Key。

检查状态：`GET /vision/status` 显示当前提供者、是否已配置、缺失的 Key。

### 本地设置（BYOK）— V1.7

你可以通过前端设置页（`/settings`）配置 API Key，不必手动编辑 `.env` 文件。

**配置优先级：** `backend/data/config/app_config.json`（宿主机）/ `data/config/app_config.json`（容器内）> `.env` 环境变量 > 硬编码默认值

| 配置项 | JSON 路径 | Env Fallback |
|--------|----------|-------------|
| DeepSeek API Key | `deepseek.api_key` | `DEEPSEEK_API_KEY` |
| DeepSeek Base URL | `deepseek.base_url` | `DEEPSEEK_BASE_URL` |
| DeepSeek 默认模型 | `deepseek.default_model` | `DEEPSEEK_DEFAULT_MODEL` |
| DeepSeek 推理模型 | `deepseek.reasoning_model` | `DEEPSEEK_REASONING_MODEL` |
| Vision 提供者 | `vision.provider` | `VISION_PROVIDER` |
| OpenAI API Key | `vision.openai_api_key` | `OPENAI_API_KEY` |
| OpenAI Vision 模型 | `vision.openai_vision_model` | `OPENAI_VISION_MODEL` |

**安全说明：** Key 保存在服务器本地的 `backend/data/config/app_config.json` 中。设置接口返回脱敏后的 Key（如 `sk-a***3f8b`）。Key 不会保存到浏览器 localStorage、不会打印到日志、不会暴露给前端。

### 运行测试

```bash
cd backend
pytest app/tests/ -v    # 全部测试使用 mock agents — 无需 API key
```

### 数据库与数据目录

```
backend/data/
├── config/
│   └── app_config.json     # BYOK 持久化配置（V1.7）
├── database/
│   └── aesthetic.db        # SQLite 数据库（git-ignored）
└── uploads/                # 上传的图片（git-ignored）
```

### 升级与数据库迁移

升级前务必先导出数据备份（设置页 → 数据管理 → 导出）。详见 [docs/UPGRADE.md](docs/UPGRADE.md)。

如果升级后遇到表结构不兼容：**先导出备份**，再联系升级指南中的迁移步骤。一般情况下向后兼容的自动迁移无需手动操作。

### 为什么这个系统有意义

大多数 AI 设计工具只生成好看的输出。这个系统训练**你**——  
它展示你反复漏掉什么、你是否过度关注表面美感而忽略商业适配、以及你下一步该练什么。

### 如何最大化训练效果

1. **添加参考案例** — 收集 high / medium / low 各 3-5 个案例，建立你的审美参考系
2. **每次提交都自评** — 自评分数 + 优缺点，系统才能对比你的判断和 AI 的判断
3. **使用「与参考案例对比」** — 看出你的作品和高审美案例的具体差距
4. **定期查看 Profile** — 了解你的进步轨迹和持续盲区
5. **上传真实图片** — 用你自己的设计稿训练，效果最好
6. **手动修改 AI 生成的描述** — V1.3 生成的描述你可以编辑，让分析更精准
