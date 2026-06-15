# Aesthetic Training Agent System

AI 辅助审美判断力训练工具。训练你的眼力，不是生成好看输出。

## Tech Stack
- Backend: FastAPI + SQLite + SQLAlchemy + Pydantic v2
- Frontend: Next.js 14 + TypeScript + Tailwind CSS
- LLM: DeepSeek（主推理引擎：分析/批评/迭代/Profile/提示词）
- Vision: OpenAI GPT-4o-mini（仅图片描述），可插拔 VisionAdapter
- Env: `VISION_PROVIDER=placeholder|openai|claude|gemini`

## Architecture
DeepSeek = 审美推理。Vision Provider = 图片→文字描述。两者职责分离。

## Versions
V1.0 analyze/critique/iterate · V1.1 用户自评+判断差异 · V1.2 图片上传+手动描述
V1.3 VisionAdapter+自动描述 · V1.4 参考案例库+对比 · V1.4.1 中文UI+提示词+历史详情
V1.4.2 OpenAI Vision · V1.4.3 Vision状态端点 · V1.5 训练工作台 · V1.5.1 案例库图片+标注
V1.6 部署 · V1.7 BYOK设置 · V1.7.1 新手引导 · V1.7.2 迭代方向 · V1.8 数据导入导出+语义搜索
V1.8.1 稳定修复 · V1.9 案例库质量管理 · V1.9.1 稳定版 · V2.0 训练评估 · V2.0.1 稳定校准 · V2.1 本地发布版 · V2.1.1 稳定候选 · V2.1.2 热修复 · V2.1.3 发布包 · V2.2 体验优化+评估图表 · V2.2.1 Agent审美内核 · V2.3 一键收藏+描述补全 · V2.4 信任度量（评测台+维度分聚合+Vision直评）· V2.4.1 复审收尾（诚实表述+评测台自测+质量趋势）· V2.5 信心（CI+缓存+遥测+前端测试/E2E+on-release评测）· V2.6 UI高级化改版（Editorial Atelier 设计系统）

## Core Flow
上传图片 → 自动生成中文描述 → 用户自评 → AI分析/批评/迭代 → 参考案例对比 → 判断差异 → 训练工作台 → 历史复盘

## Critical Rules
1. 禁止 placeholder 冒充真实视觉识别
2. API key 不入前端、不入代码、不入日志
3. 全站用户可见文案必须中文
4. 历史详情弹窗不能坏（click→modal）
5. V1.1 judgment gap / comparator 不能坏
6. 不提交 .env；.env.example 用安全占位符
7. 使用 `bash scripts/kill_port.sh <port>` 杀进程，禁止 `taskkill //IM`

## Quick Commands
```bash
# 一键启动（Docker 推荐）
bash scripts/start.sh

# 后端
cd backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# 测试（本机裸 python 缺 fastapi，依赖装在 Python311 里）
cd backend && C:/Users/Dream/AppData/Local/Programs/Python/Python311/python.exe -m pytest app/tests/ -q

# 前端（本机已装 Node v24）：组件测试 + 构建
cd frontend && npm run test && npm run build

# CI：push/PR 自动跑后端 pytest + 前端 Vitest + build（.github/workflows/ci.yml），保持绿
```

## Dev Constraints
- 小步修改，改完就测
- 不重构除非明确要求
- 不做 SaaS 登录/部署/Supabase/向量DB 除非明确要求
- Windows 宿主机 + Git Bash：用 127.0.0.1 不用 localhost；用 pythonw 启动子进程
