# Aesthetic Training Agent System / 审美训练智能体系统

AI-assisted aesthetic judgment training.  
Train your eye, not just generate pretty output.  
AI 辅助审美判断力训练。训练你的眼力，而不只是生成好看的输出。

**当前版本：V1.5.1** | 测试：85+ passed | [项目状态](PROJECT_STATUS.md) | [路线图](ROADMAP.md) | [开发规范](AI_CONTEXT.md)

---

## English

### What is this?

An AI-powered training system that helps you improve your aesthetic judgment.  
You describe visual work, the AI analyzes it, you self-assess, and the system  
shows you what you missed, what you misjudged, and what to practice next.

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

### Quick Start

#### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # edit .env — set DEEPSEEK_API_KEY
uvicorn app.main:app --reload    # http://127.0.0.1:8000
```

API docs: http://127.0.0.1:8000/docs

#### Frontend

```bash
cd frontend
cp .env.example .env             # NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
npm install                      # if registry is slow: --registry https://registry.npmmirror.com
npm run dev                      # http://localhost:3000
```

### Features by Version

| Version | Feature |
|---------|---------|
| V1.0 | `/analyze` `/critique` `/iterate` — 9-dimension aesthetic decomposition, scored critique, design iteration |
| V1.1 | User self-assessment → AI scoring → judgment gap analysis → Profile training feedback |
| V1.2 | Image upload (jpg/png/webp, 10MB), manual image description, `/uploads` static files |
| V1.3 | Pluggable VisionAdapter, `POST /images/{id}/describe`, auto-generate image descriptions |
| V1.4 | Reference case library (high/medium/low), `POST /compare-with-references`, aesthetic comparison training |

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

### Training Workflow

1. **Describe a visual work** — paste a design description or upload an image
2. **Choose task type** — Analyze / Critique / Iterate
3. **(Optional) Self-assess** — score your work, list strengths/weaknesses/audience/price band
4. **AI responds** — structured analysis, scored critique, or design alternatives
5. **View the gap** — see what you got right, what you missed, commercial/aesthetic blind spots
6. **Check your profile** — the system tracks your patterns and suggests next-week focus
7. **Compare with references** — see how your work stacks up against curated high/medium/low examples

### Environment Variables

| Variable | Default | Required |
|----------|---------|----------|
| `DEEPSEEK_API_KEY` | — | **Yes** (for LLM calls) |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com` | No |
| `DEEPSEEK_DEFAULT_MODEL` | `deepseek-v4-flash` | No |
| `DEEPSEEK_REASONING_MODEL` | `deepseek-v4-pro` | No |
| `DATABASE_URL` | `sqlite:///./aesthetic.db` | No |
| `VISION_PROVIDER` | `placeholder` | No |
| `NEXT_PUBLIC_API_BASE_URL` | `http://127.0.0.1:8000` | No |

### Vision Provider

Set `VISION_PROVIDER` in your `.env`:

- `placeholder` (default) — returns mock structured descriptions, no API key needed
- `manual` — V1.2 mode: user must type the image description
- `openai` — (future) OpenAI Vision
- `claude` — (future) Claude Vision

### Running Tests

```bash
cd backend
pytest app/tests/test_api.py -v    # 73 tests, no API key needed (mocked agents)
```

### Rebuilding the SQLite Database

If you upgrade and the table schema is incompatible, delete the database file and restart:

```bash
rm backend/aesthetic.db              # Linux/macOS
del backend\aesthetic.db             # Windows
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

#### 后端

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # 编辑 .env，设置 DEEPSEEK_API_KEY
uvicorn app.main:app --reload    # http://127.0.0.1:8000
```

API 文档：http://127.0.0.1:8000/docs

#### 前端

```bash
cd frontend
cp .env.example .env             # NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
npm install                      # 如果下载慢：--registry https://registry.npmmirror.com
npm run dev                      # http://localhost:3000
```

### 各版本功能

| 版本 | 功能 |
|------|------|
| V1.0 | `/analyze` `/critique` `/iterate` — 9 维美学分解、打分、设计迭代 |
| V1.1 | 用户自评 → AI 评分 → 判断差异分析 → Profile 训练反馈 |
| V1.2 | 图片上传（jpg/png/webp，10MB），手动图片描述，`/uploads` 静态文件 |
| V1.3 | 可插拔 VisionAdapter，`POST /images/{id}/describe`，自动生成图片描述 |
| V1.4 | 参考案例库（high/medium/low），`POST /compare-with-references`，高低审美对比训练 |

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
| `GET` | `/health` | 健康检查 |

### 训练流程

1. **描述一个视觉作品** — 粘贴设计描述或上传图片
2. **选择任务类型** — 分析 / 评分 / 迭代
3. **（可选）自我评估** — 打分，列出优缺点、目标用户、价格带
4. **AI 返回结果** — 结构化分析、打分评论、或设计改版方向
5. **查看差异** — 看你对在哪、漏了什么、商业/美学盲点
6. **查看画像** — 系统跟踪你的模式，给出下周训练重点
7. **与参考案例对比** — 看看你的作品和高/中/低审美案例的差距

### 环境变量

| 变量 | 默认值 | 是否必需 |
|------|--------|----------|
| `DEEPSEEK_API_KEY` | — | **是**（LLM 调用需要） |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com` | 否 |
| `DEEPSEEK_DEFAULT_MODEL` | `deepseek-v4-flash` | 否 |
| `DEEPSEEK_REASONING_MODEL` | `deepseek-v4-pro` | 否 |
| `DATABASE_URL` | `sqlite:///./aesthetic.db` | 否 |
| `VISION_PROVIDER` | `placeholder` | 否 |
| `NEXT_PUBLIC_API_BASE_URL` | `http://127.0.0.1:8000` | 否 |

### 视觉提供者

在 `.env` 中设置 `VISION_PROVIDER`：

- `placeholder`（默认）— 返回 mock 结构化描述，无需 API key
- `manual` — V1.2 模式：用户必须手动输入图片描述
- `openai` — （未来）OpenAI Vision
- `claude` — （未来）Claude Vision

### 运行测试

```bash
cd backend
pytest app/tests/test_api.py -v    # 73 个测试，无需 API key（使用 mock agents）
```

### 重建 SQLite 数据库

如果升级后表结构不兼容，删除数据库文件后重启即可：

```bash
rm backend/aesthetic.db              # Linux/macOS
del backend\aesthetic.db             # Windows
# 重启后端 — 启动时会自动建表
```

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
