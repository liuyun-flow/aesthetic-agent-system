# Project Status — V1.7.2

## Current Version
**V1.7.2** — 迭代方向选择 / 基于方向生成提示词 / 结构化迭代字段

## Completed Capabilities (V1.7.2 additions)

### Structured Iteration Directions
- 每个 IterationDirection 包含：id, title, description, expected_impact, goal, visual_changes, color_changes, typography_changes, layout_changes, commercial_rationale, risk
- IteratorAgent 提示词更新，要求所有字段用中文输出
- 向后兼容：LLM 未提供 id 时自动分配 dir-1, dir-2…

### Direction-Based Prompt Generation
- `/generate-prompt` 接收 `selected_direction`（JSON 字符串或对象）与可选 `session_id`
- PromptGeneratorAgent focus block：有选择方向时强烈聚焦该方向
- 生成结果保存到匹配的 iterate session 的 `selected_direction` + `prompt_result`
- 未传 `session_id` 的旧客户端仅回退保存到最新 iterate 记录，不会写入 analyze/critique 记录
- 无选择方向时完全兼容旧流程

### Frontend: Iteration Direction Cards
- 每个迭代方向显示为可交互卡片
- 展开/收起详情（目标、视觉/色彩/字体/布局变化、商业理由、风险）
- 选择方向按钮 + 高亮已选择方向
- 基于该方向生成提示词按钮 + 加载状态
- 提示词结果卡片展示（可逐项复制）

### History Detail Enhancement
- 训练详情弹窗展示当时所有迭代方向，并高亮用户选择的方向
- 展示选中方向对应的生成提示词：中文提示词 / 英文提示词 / 反向提示词 / 设计师执行说明 / 文案优化提示 / 使用建议
- 提示词可逐项复制
- 旧历史记录缺少 `selected_direction` / `prompt_result` 时不会崩溃或显示 undefined/null/[object Object]

## Test Results
- **148 passed**（V1.7.1 原 137 + V1.7.2 新增 11 个）
- 新增测试覆盖：TestGeneratePromptWithDirection × 8, TestIterationDirectionSchema × 3
- 全部使用 mocked agents，无需 API key

## Build Results
- Frontend build: ✅ 通过
- Backend pytest: ✅ 148 passed
- Docker compose config: ✅ 有效
- Docker compose up --build smoke test: ✅ 后端 `/health` 返回 v1.7.2，前端首页返回 200

## Next Step
V1.8 — 语义搜索 / 向量检索（前置条件：案例库 ≥50 个）

## Completed Capabilities (V1.7.1 additions)

### Setup Wizard (`/setup`)
- 5 步首次使用向导：欢迎 → 配置模型 → 测试连接 → 第一次训练 → 完成
- 全部中文界面，可跳过，可从帮助页重新打开
- 完成状态保存到后端 `app_config.json`（`setup.completed`）
- 不保存 API Key 到前端 localStorage
- 测试连接按钮复用 `/settings/test-deepseek` 和 `/settings/test-vision`

### Help Center (`/help`)
- 快速开始 / 配置 API Key / 完成一次训练 / 参考案例库 / 迭代与提示词 / 历史记录 / 备份数据
- FAQ 8 项：图片描述不准、API Key 未配置、DeepSeek vs Vision 职责、placeholder 含义、数据存储位置、API Key 安全、为何先自评、如何判断训练有效
- 全部中文，可折叠 FAQ

### Config Status Bar
- 首页顶部显示系统状态条：DeepSeek / Vision / 数据库 / 上传目录
- 绿灯（已配置/正常）/ 红灯（未配置/异常）
- 未配置时显示「去设置」「查看帮助」快捷按钮
- 数据来源：`GET /system/status`

### Backend: `/system/status` Endpoint
- 合并 health + model + vision + database + uploads + setup 状态
- 数据库连通性检查（`SELECT 1`）
- 上传目录可写性检查
- 不暴露任何 API Key，仅返回 boolean configured 标志

### Backend: `/setup/status` + `/setup/complete`
- GET `/setup/status` — 返回 `{setup_completed: bool}`
- POST `/setup/complete` — 标记向导完成，幂等
- 状态保存在 `app_config.json` 的 `setup.completed` 字段

### Navigation
- 新增「帮助」导航标签（/help）
- Setup 页面可通过链接访问，不在主导航中（减少新用户困惑）

## Test Results
- **137 passed**（V1.7 原 121 + V1.7.1 新增 16 个）
- 新增测试覆盖：/system/status × 11, /setup/status × 1, /setup/complete × 3, /health × 1
- 全部使用 mocked agents + adapters，无需 API key

## Build Results
- Frontend `npm run build`: ✅ 通过（5 routes: /, /settings, /help, /setup, /_not-found）
- Docker compose config: ✅ 有效
- Backend pytest: ✅ 137 passed

## Completed Capabilities
- 图片上传（jpg/png/webp，UUID 命名，10MB 上限）
- 自动生成中文图片描述（OpenAI GPT-4o-mini，可切换 placeholder）
- 作品描述输入 + 用户自评（评分/优缺点/目标用户/价格带）
- AI 多维度美学分析（色彩/构图/字体/材质/情绪/品牌感）
- AI 结构化评分（1-10 分 + 6 维度 + 问题 + 修复建议）
- AI 设计迭代方向（3-5 个改版方向）
- 用户 vs AI 判断差异分析（Comparator Agent）
- Profile 训练画像（偏好/误区/下周重点）
- 训练工作台（每日主题轮换/统计数据/每周复盘）
- 参考案例库（high/medium/low，图片+审美标注+详情弹窗）
- 高低审美对比（compare-with-references）
- 可复制提示词生成（中文/英文/反向/设计说明）
- 历史详情弹窗（点击查看完整训练记录）
- 中英文界面切换（默认中文）
- **Docker 支持**（backend/Dockerfile + frontend/Dockerfile + docker-compose.yml + healthcheck）
- **环境配置检查**（scripts/check-env.py — 同时读取 .env 和设置页 config）
- **数据目录整理**（data/config/ + data/database/ + data/uploads/）
- **健康检查端点**（/health /model/status /vision/status）
- **跨平台工程规范**（AI_CONTEXT.md + kill_port.sh + start_all.sh）
- **项目文档完整**（CLAUDE.md, AGENTS.md, ROADMAP.md, SESSION_HANDOFF.md）
- **Docker build context 安全**（backend/.dockerignore + frontend/.dockerignore）
- **Placeholder key 统一检测**（PLACEHOLDER_CONFIG_VALUES 集中定义）
- **Vision 错误分层返回**（_vision_http_exception 按异常类型映射安全中文提示）
- **Vision smoke test 修复**（运行时生成 64x64 有效 RGB PNG，不再用 1x1 硬编码 hex）
- **前端 i18n 全覆盖**（错误 fallback 全部走 i18n 键）
- **测试全面离线**（Mock 覆盖全部 Agent + Vision Adapter）
- **本地设置页**（前端 /settings + GET/POST /settings + 测试连接 + 清除密钥）
- **BYOK 配置存储**（data/config/app_config.json，优先级：config > .env > 默认值）
- **.env fallback 不被默认 JSON 遮蔽**（DEFAULT_CONFIG 全部空字符串，真实默认值在 get_value() / or 回退中）
- **clear-key 真清除**（_CLEARED_SENTINEL 机制，清 key 后不再 fallback 到 .env）
- **脱敏 API Key 展示**（sk-a***3f8b 格式，check-env.py 同样脱敏）
- **DeepSeek / OpenAI Vision 连接测试**（POST /settings/test-deepseek, /settings/test-vision）
- **配置原子写入**（temp file + rename，invalidate cache before I/O 防止竞态）
- **测试全覆盖**（121 passed，含新增 10 个测试）

## Post-V1.7 Codex Review Fixes (commit: f290ac7)

### 发布阻断修复（8 项）
| # | 问题 | 修复 |
|---|------|------|
| 1 | `backend/data/config/app_config.json` 被 Git 跟踪 | `.gitignore` 添加规则，`git rm --cached`，仅保留 `.gitkeep` |
| 2 | DEFAULT_CONFIG 非空值遮蔽 .env fallback | 全部改为空字符串，默认值移至 `get_value()` 的 `default` 参数和调用方 `or` 回退 |
| 3 | clear-key 后 .env fallback 仍生效 | 引入 `_CLEARED_SENTINEL`，`get_value()` 识别后返回 `""` 跳过 env |
| 4 | 测试连接返回原始异常文本 | 改为固定中文错误消息 |
| 5 | 版本号仍是 V1.6（main.py 两处） | `1.6.0` → `1.7.0` |
| 6 | 前端清除 Key 不检查响应状态 | `handleClearKey` 增加 `res.ok` 检查 |
| 7 | 前端加载失败无错误态 | 新增 `fetchError` state + 重试按钮 |
| 8 | check-env.py 泄露 key 前缀且不识别设置页配置 | 完整重写，同时读取 .env 和 app_config.json，key 全部 masked |

### 建议修复（4 项）
| # | 问题 | 修复 |
|---|------|------|
| 1 | GET /settings 不反映 .env fallback | `get_masked_status()` 改用 `get_value()` 走完整优先级链 |
| 2 | `write_config` 存在竞态窗口 | `_invalidate_cache()` 移到 I/O 之前 |
| 3 | `OpenAIVisionAdapter` 空字符串 key 处理 | `if api_key is not None` → `if api_key:` 允许 fallback |
| 4 | README 测试命令只跑旧测试 | 改为 `pytest app/tests/ -v` |

### 代码重构
- `PLACEHOLDER_CONFIG_VALUES` in config_store: 集中定义占位符值
- `is_configured_value()`: 从 `get_masked_status` 内部提取为公共函数
- `get_vision_provider()` / `get_vision_missing_keys()` / `is_vision_configured()`: 抽取 vision 状态查询
- `_vision_http_exception()` in main.py: 异常分类 → HTTP 状态码 + 安全中文消息
- `start_all.sh`: 去掉了嵌套 subprocess.Popen，backend 直接 `pythonw -m uvicorn`，frontend 直接 `node node_modules/next/dist/bin/next dev`

## Post-V1.7 Vision Fix (commit: 4ac7ee8)

### 修复内容
| # | 问题 | 修复 |
|---|------|------|
| 1 | /settings/test-vision 误报失败（1×1 PNG 被 OpenAI 拒绝） | 运行时生成 64×64 有效 RGB PNG，`_make_vision_test_png()` + `_png_chunk()` |
| 2 | 工作台图片描述错误提示过于笼统 | `_vision_http_exception()` 按 AuthenticationError / APIConnectionError / BadRequestError / APIStatusError 429 / json.JSONDecodeError 等分层返回 |
| 3 | 缺回归测试 | test_settings: `test_vision_test_image_is_valid_png`；test_api: JSON parse error 安全消息 + 通用异常不泄露原始异常 |

## Known Issues
1. GitHub push 需代理（127.0.0.1:7891），代理未运行时 `git push` 失败
2. Git Bash 下 curl 无法连接 127.0.0.1（用浏览器或用 Python urllib + ProxyHandler({}) 替代）
3. HTTP_PROXY 环境变量可能导致 Python urllib 本地连接失败（绕过：ProxyHandler({})）
4. `backend/.env` 里 `DATABASE_URL=sqlite:///./aesthetic.db` 与 V1.7 预期 `data/database/aesthetic.db` 不一致（历史遗留，不要贸然改，否则丢失历史数据）
5. POST /settings/test-vision 对 OpenAI 只做文本 chat smoke test，不做真实 image input 测试（连通性测试，够用）
6. 前端 `NEXT_PUBLIC_API_BASE_URL` 是 build-time env，Docker 运行时不变（本地默认可用，自定义部署需注意）

## Not Yet Built
- 语义搜索 / 向量检索（V1.8，前置条件：案例库 ≥50 个）
- 多人 SaaS / 登录 / 云存储（V2.0）
- 设置页 "配置来源" 展示（减少 .env 与设置页混用困惑）

## Next Step
V1.8 — 语义搜索 / 向量检索（前置条件：案例库 ≥50 个）

## Files Modified/Created in V1.7.1

### Backend
| File | Changes |
|------|---------|
| `backend/app/main.py` | +`/system/status`, +`/setup/status`, +`/setup/complete`; version→1.7.1; health→v1.7.1; +`is_vision_configured`, `get_config` imports |
| `backend/app/settings/config_store.py` | DEFAULT_CONFIG +`setup` section |
| `backend/app/tests/test_api.py` | +TestSystemStatus (11 tests) +TestSetupEndpoints (4 tests) |

### Frontend
| File | Changes |
|------|---------|
| `frontend/src/app/setup/page.tsx` | **New** — 5-step setup wizard |
| `frontend/src/app/help/page.tsx` | **New** — Help center with FAQ |
| `frontend/src/app/layout.tsx` | +「帮助」nav tab |
| `frontend/src/app/page.tsx` | +ConfigStatusBar component; +useEffect for /system/status |
| `frontend/src/i18n/zh.ts` | +status, setup, help i18n keys |
| `frontend/src/i18n/en.ts` | +status, setup, help i18n keys |
| `README.md` | +V1.7.1 features, +new endpoints, +first-time users section, +config verification |


## Files Modified Post-V1.7 Hardening (f290ac7 + 4ac7ee8)

### Backend Core
| File | Changes |
|------|---------|
| `backend/app/main.py` | _vision_http_exception() 异常分类映射；describe 端点接入；version→1.7.0；health→v1.7；OpenAI 异常分类 imports |
| `backend/app/settings/config_store.py` | DEFAULT_CONFIG 清空；_CLEARED_SENTINEL + clear_key 改写；get_value 识别 sentinel；get_masked_status 走 get_value()；PLACEHOLDER_CONFIG_VALUES 集中；is_configured_value / get_vision_provider / get_vision_missing_keys / is_vision_configured 提取；write_config 在 I/O 前 invalidate |
| `backend/app/settings/routes.py` | _make_vision_test_png() 运行时 64×64 PNG；_png_chunk() helper；test-vision 直接测试 adapter 而非 HTTP chat；固定异常消息 |
| `backend/app/vision/openai_adapter.py` | `if api_key is not None` → `if api_key:` 空字符串 fallback |
| `backend/app/llm/deepseek_client.py` | get_value() fallback chain（之前已完成） |

### Tests
| File | Changes |
|------|---------|
| `backend/app/tests/test_settings.py` | 4 个测试适配 env 隔离；test_vision_test_image_is_valid_png（新增） |
| `backend/app/tests/test_api.py` | 2 个 ClearKey 测试适配 sentinel；test_describe_json_parse_error_returns_safe_message（新增）；test_describe_generic_error_does_not_expose_raw_exception（新增） |

### Scripts & Config
| File | Changes |
|------|---------|
| `scripts/check-env.py` | 完整重写：同时读 .env 和 app_config.json；key 全部 masked；source 标注 |
| `scripts/start_all.sh` | 去掉 pythonw subprocess.Popen 嵌套；frontend 直接 node 启动 |
| `.gitignore` | backend/data/config/* / backend/data/uploads/* / backend/data/database/*.db |
| `backend/.env.example` | 路径同步到 data/ 布局 |
| `README.md` | 测试命令改为 `pytest app/tests/ -v` |

### Frontend
| File | Changes |
|------|---------|
| `frontend/src/app/settings/page.tsx` | fetchStatus 失败错误态 + 重试按钮；handleClearKey 检查 res.ok；已配置时 password 框绿色 placeholder |
| `frontend/src/i18n/zh.ts` | loadError / retry / clearKeyHint 键 |
| `frontend/src/i18n/en.ts` | 同上英文 |

## Local Run
```bash
# 一键启动
bash scripts/start_all.sh --open-browser

# 检查配置
python scripts/check-env.py

# 运行测试（当前 148 passed）
cd backend && pytest app/tests/ -v

# 前端 build 检查
cd frontend && npx next build

# Docker 启动
docker compose up --build
```

## Test Results
- **121 passed**（V1.7 原始 111 + hardening 阶段 8 个 + vision fix 阶段 2 个）
- 全部使用 mocked agents + adapters，无需 API key
- 覆盖：Settings CRUD / clear-key sentinel / test-connection / vision describe 异常分层 / PNG 结构验证 / 原始异常不泄露
