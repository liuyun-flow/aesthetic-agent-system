# Project Status — V2.3.0

## Current Version
**V2.3.0** — 一键收入案例库（prefill+confirm）+ 描述质量优化（Vision 商业推测 / 完整度进度条 / 引导式补全）

---

## 版本演进总览

| 版本 | 主题 | 关键交付 |
|------|------|----------|
| V1.0 | MVP | analyze / critique / iterate |
| V1.1 | 训练闭环 | 用户自评 + 判断差异 + Profile |
| V1.2 | 图片 | 上传 + 手动描述 |
| V1.3 | Vision | VisionAdapter + 自动描述 |
| V1.4 | 案例库 | 参考案例 CRUD + compare-with-references |
| V1.4.1–V1.4.3 | 打磨 | 中文 UI + 提示词生成 + OpenAI Vision + 状态端点 |
| V1.5 | 训练工作台 | 每日主题 / 统计 / 每周复盘 |
| V1.5.1 | 案例增强 | 案例图片 + 审美标注（premium/cheapness/learn/avoid） |
| V1.6 | 部署 | Docker + 配置检查 + 数据目录整理 |
| V1.7 | 设置 | 本地设置页 / BYOK / 连接测试 / 脱敏 |
| V1.7.1 | 新手引导 | Setup wizard / Help center / 配置状态条 / system/status |
| V1.7.2 | 迭代方向 | 结构化迭代字段 / 选择方向生成提示词 / 历史展示 |
| V1.8 | 数据+搜索 | 导入导出 zip / 语义搜索 / embedding / 数据管理 UI |
| V1.8.1 | 稳定 | 版本统一 / .gitignore / 回归测试 / 文档同步 |
| V1.9.0 | 质量 | 完整度评分 / 训练可用判定 / 案例库体检 / 重复检测 |
| V1.9.1 | 稳定 | aesthetic_level 验证统一 / null 安全加固 / audit issue 字段补全 |
| V2.0.0 | 评估 | 训练效果总览 / 误判统计 / 能力维度 7 维评分 / 周期复盘 |
| V2.0.1 | 校准 | 双评分有效数据阈值 / selected_direction 容错 / 导入 v2 兼容 |
| V2.1.0 | 发布 | 一键启动脚本 / 系统诊断 / 设置页诊断面板 / 文档体系 |
| V2.1.1 | 候选 | 版本同步 / 启动脚本健壮性 / 旧 DB 迁移提示 |
| **V2.1.2** | **热修复** | Windows start.bat 纯 CMD 重写 / chunk 缓存自动恢复 / Help 内容刷新 |
| V2.1.3 | 发布包 | .dockerignore / 部署指南 / 发布清单 / .gitignore 加固 / README 第一屏重写 |
| V2.2.0 | 体验优化+图表 | 分阶段进度+取消 / 再练一次 / 粘贴拖拽上传+自动描述 / 折叠面板 / Ctrl+Enter / 雷达图+差距图 / DeepSeek 超时 |
| V2.2.1 | Agent审美内核 | design_knowledge.py 知识库 / 评分五档锚点+反通胀 / 证据规则 / 四 Agent 注入 / critique→推理模型 / 强制中文 |
| **V2.3.0** | **一键收藏+描述补全** | 一键收入案例库（session→draft+等级推导）/ image_id 链接 / Vision 商业推测字段 / 描述完整度进度条 / 引导式补全 |

---

## V2.0.x 核心交付

### 训练效果评估系统
- 纯规则分析（不依赖 LLM），基于 TrainingRecord 历史数据
- `GET /assessment/overview` — 训练频次、评分均值、差距趋势、中文总结
- `GET /assessment/mistakes` — 10 种关键词规则误判检测，含严重度和训练建议
- `GET /assessment/dimensions` — 7 审美维度 0-100 评分 + 强弱标签 + 趋势
- `GET /assessment/report?days=7` — 周期复盘：进度总结、训练计划、推荐主题
- 前端 `/assessment` 页面 — 总览卡片 + 误判/维度/复盘三 Tab
- 数据不足阈值：有效双评分 ≥5 条

### V2.0.1 稳定性校准
- 统一使用双评分有效记录数作为数据充足判定（修正 total_sessions>=5 的漏洞）
- `selected_direction` 非 dict 格式容错（数组/字符串/非法 JSON 不崩溃）
- 导入版本检查接受 v1.x 和 v2.x 双前缀
- 关键词精度优化（去掉过宽关键词、消除维度间冲突）
- 前端报告错误态补齐

| 类别 | 变更 |
|------|------|
| 训练总览 | 有效评分次数 + 评分均值 + 差距趋势 + 中文总结 |
| 误判检测 | 10 种关键词规则 + 严重度 + 解释 + 训练建议 |
| 能力维度 | 7 维度 0-100 动态评分 + 强弱/趋势 + 证据 + 建议 |
| 周期复盘 | 7/30 天切换 + 进度总结 + 训练计划 + 推荐主题 |
| 评估页面 | `/assessment` — 统计卡片 + 误判/维度/复盘 Tab |
| 版本号 | main.py / health / system/status / export → v2.0.1 |

### 修改的文件（V2.0.0–V2.0.1）
| File | Change |
|------|--------|
| `backend/app/services/assessment.py` | **New** — 规则化评估引擎 |
| `backend/app/services/session_service.py` | +get_all_records(), +get_records_in_range() |
| `backend/app/schemas/responses.py` | +AssessmentOverview, MistakePattern, DimensionAssessment, AssessmentReport |
| `backend/app/main.py` | +4 assessment endpoints, version→v2.0.1 |
| `backend/app/services/data_io.py` | EXPORT_VERSION→v2.0.1, import version v1+v2 |
| `backend/app/tests/test_assessment.py` | **New** — 20 tests |
| `backend/app/tests/test_api.py` | version assertions updated |
| `frontend/src/app/assessment/page.tsx` | **New** — 评估仪表盘 |
| `frontend/src/app/layout.tsx` | +训练评估 nav link |

### V1.9.0 变更（前一个版本）

### 案例完整度评分
- 动态计算 `completeness_score`（0-100），基于 13 个字段加权
- 权重：图片 15 / 描述 15 / 审美等级 10 / 品类 8 / 价格档位 8 / 风格标签 8 / 目标用户 8 / 高级感来源 7 / 廉价感来源 7 / 值得学习 7 / 不能误学 3 / 备注 2 / 评分 2
- 纯动态计算，不写入数据库，兼容所有旧数据
- 缺失字段返回中文标签，无 undefined/null

### 训练可用状态
- 动态判定 `is_training_ready`：完整度 ≥75 + 有图片 + 有审美等级 + 有描述 + 有 learn_from_this 或 premium_sources
- 案例库列表显示训练可用标记（✓）
- 语义搜索结果按训练可用优先排序

### 案例库体检
- 新增 `GET /reference-cases/audit` — 返回完整度统计、缺失分类、疑似重复、建议
- 新增前端 `/audit` 体检页面 — 统计卡片 + 分类问题列表 + 重复检测 + 建议
- 重复检测双层回退：标题 token 重叠相似度（≥70%）+ embedding 余弦相似度（≥90%，如可用）

### 前端增强
- 案例库列表显示完整度分数徽标（绿≥75 / 黄 50-74 / 红 <50）
- 案例详情弹窗新增「案例质量分析」区块
- 语义搜索结果显示训练可用标记和完整度分数
- 导航栏新增「案例库体检」入口

| 类别 | 变更 |
|------|------|
| 完整度评分 | 13 字段加权动态计算，不写 DB |
| 训练可用 | 5 条件判定，列表/搜索/详情均展示 |
| 体检接口 | `GET /reference-cases/audit` |
| 体检页面 | `/audit` — 统计/分类/重复/建议 |
| 重复检测 | 标题相似度 + embedding 相似度（fallback） |
| 前端列表 | 完整度徽标 + 训练可用 ✓ 标记 |
| 前端详情 | 案例质量分析区块（分数/状态/缺失字段） |
| 语义搜索 | 训练可用优先排序 + 完整性字段 |
| 版本号 | main.py / health / system/status / export → v1.9.0 |

### 修改的文件（本次）
| File | Change |
|------|--------|
| `backend/app/services/case_quality.py` | **New** — 完整度评分、训练就绪、体检、重复检测 |
| `backend/app/schemas/responses.py` | +CaseAuditResponse, +AuditIssue, +DuplicateGroup; ReferenceCaseResponse +quality fields |
| `backend/app/main.py` | +audit endpoint, _ref_response +quality, search_semantic +quality sort, version→1.9.0 |
| `backend/app/services/data_io.py` | EXPORT_VERSION→v1.9.0 |
| `backend/app/tests/test_api.py` | +17 tests (TestCaseQuality), 2 version assertion updates |
| `frontend/src/app/audit/page.tsx` | **New** — 案例库体检页面 |
| `frontend/src/components/ReferencePanel.tsx` | +quality badges, +training-ready indicators, +detail quality section |
| `frontend/src/app/layout.tsx` | +audit nav link |
| `README.md` | 版本 + V1.9 说明 |
| `ROADMAP.md` | V1.9 标记 ✅ 已完成 |
| `PROJECT_STATUS.md` | 本文档 |
| `docs/SESSION_HANDOFF.md` | 重写为 V1.9 |
| `CLAUDE.md` | 版本线新增 V1.9 |

---

## V2.3.0 变更（本次）

V2.3.0 来自用户实测反馈：(1) 训练中遇到值得收藏的案例缺乏快捷入口；(2) 用户初始描述常不准确，自动描述也漏掉目标用户/价格带等商业信息。

### 功能 1：一键收入案例库（prefill + confirm）
| 类别 | 变更 |
|------|------|
| 数据模型 | training_records 新增 `image_id`（自动迁移 `_migrate_v2_3`，nullable，旧数据安全） |
| 记录链接 | analyze/critique/iterate 保存时记录所用 image_id |
| 草稿接口 | **New** `GET /sessions/{id}/case-draft` —— 映射会话→案例草稿（不保存）；`build_case_draft()` + `_level_from_score()`（≥75 高/45-74 中/<45 低） |
| 会话详情 | SessionDetailResponse 新增 image_id / image_url |
| 前端 | 训练结果区 + 历史详情弹窗「收入案例库」按钮 → 拉取草稿 → 自动展开案例库并预填表单 → 用户核对后保存；ReferencePanel 接受 prefill；CollapsibleSection 支持 forceOpen |

### 功能 2：描述质量优化（Vision 推测 + 引导式补全 + 完整度）
| 类别 | 变更 |
|------|------|
| Vision 字段 | VisionDescription 新增 design_category / target_audience_guess / price_band_guess / use_case（nullable） |
| Vision 提示词 | OpenAI adapter 推测上述商业字段，信息不足返回 null 不编造；placeholder 同步示例值 |
| 完整度进度条 | TaskForm 显示「描述完整度 X%」+ 缺失项提示（描述详实度 + 4 个商业字段） |
| 引导式补全 | 品类/目标用户/价格带/使用场景输入框；可一键「采用」Vision 推测（标注 AI 推测）；提交时并入作品描述（【补充信息】后缀）供智能体判断 |

### 修改的文件（V2.3.0）
| File | Change |
|------|--------|
| `backend/app/db/models.py` | TrainingRecord +image_id |
| `backend/app/db/database.py` | +_migrate_v2_3 |
| `backend/app/services/session_service.py` | save_record +image_id |
| `backend/app/services/reference_service.py` | +build_case_draft +_level_from_score |
| `backend/app/main.py` | analyze/critique/iterate 传 image_id；session detail +image_url；+/sessions/{id}/case-draft；version 2.3.0 |
| `backend/app/schemas/responses.py` | SessionDetailResponse +image_id/image_url；VisionDescription +4 商业字段 |
| `backend/app/vision/openai_adapter.py` `placeholder_adapter.py` | 商业推测字段 |
| `backend/app/tests/test_api.py` | +TestSessionCaseDraft（4 tests）；version 断言 |
| `frontend/src/components/TaskForm.tsx` | 完整度进度条 + 引导式补全 + Vision 推测采用 |
| `frontend/src/components/ReferencePanel.tsx` | prefill 草稿映射 + CaseDraft 导出 |
| `frontend/src/components/SessionList.tsx` | +onAddToLibrary 按钮 + image 字段 |
| `frontend/src/app/page.tsx` | handleAddToLibrary + casePrefill 接线 + CollapsibleSection forceOpen |
| `frontend/src/i18n/zh.ts` `en.ts` | +addToLibrary +form 补全/完整度 +reference.prefillNotice |

---

## V2.2.1 变更（前一个版本）

V2.2.1 是 Agent 审美内核强化版。诊断：智能体的 prompt 只有"你是专业评论家"的角色设定，没有任何真实设计知识、评分锚点和证据纪律，导致输出空泛、评分集中在 6.5-8 的舒适区。

| 类别 | 变更 |
|------|------|
| 设计知识库 | **New** `app/agents/design_knowledge.py` — 意图优先评判 / 字体 / 色彩 / 版式 / 材质 / 高级感与廉价感信号，全部为可证伪准则 |
| 评分校准 | 五档锚点（9-10 一线作品集 / 7-8 专业 / 5-6 合格平庸 / 3-4 结构性返工 / 1-2 传达失败）+ 反通胀五规则 |
| 证据规则 | 判断必须引用描述中的具体元素 + 点名原则；禁止空话和编造 |
| Agent 注入 | analyzer / critic / iterator / reference_comparator 系统提示词全部携带知识库 |
| 模型分配 | get_critic 改用推理模型（评分最重判断；延迟由进度 UI + 超时兜底） |
| 输出语言 | analyzer / critic 强制中文输出（此前仅 iterator 有此要求） |
| 版本号 | main.py / data_io.py / tests → v2.2.1 |

### 修改的文件（V2.2.1）
| File | Change |
|------|--------|
| `backend/app/agents/design_knowledge.py` | **New** — DESIGN_KNOWLEDGE / SCORING_RUBRIC / EVIDENCE_RULES |
| `backend/app/agents/analyzer.py` | 知识库注入 + 意图优先 + 证据规则 + 中文输出 |
| `backend/app/agents/critic.py` | 知识库 + 评分锚点 + 反通胀 + 中文输出 |
| `backend/app/agents/iterator.py` | 知识库注入 + 原则化方向 + 真实取舍 risk |
| `backend/app/agents/reference_comparator.py` | 知识库 + 证据规则注入 |
| `backend/app/agents/orchestrator.py` `main.py get_critic` | critic → 推理模型 |

---

## V2.2.0 变更（前一个版本）

V2.2.0 是工作台体验优化版：聚焦用户友好度、便捷性和训练有效性，不改后端业务逻辑（仅加 LLM 客户端超时）。

| 类别 | 变更 |
|------|------|
| AI 调用反馈 | 等待时显示任务专属分阶段进度（每 6 秒推进）、已等待秒数、进度条，「取消」按钮（AbortController），取消显示中性提示 |
| DeepSeek 超时 | OpenAI 客户端 timeout=120s（DEEPSEEK_TIMEOUT_SECONDS 可配）+ max_retries=1，挂起连接不再无限等待 |
| 错误可见性 | TrainingPanel 标记完成失败不再清空表单、显示错误；成功显示「已保存 ✓」；周复盘失败显示错误 |
| 工作台结构 | 结果就绪自动滚动到可视区；今日训练/案例库/历史记录折叠面板（localStorage 记住状态，案例库默认收起） |
| 再练一次 | 历史详情弹窗新增「再练一次」：载入当时描述+任务类型回表单，重新自评对比过去判断 |
| 快捷操作 | Ctrl+Enter 提交；描述不足 10 字时按钮旁显示原因提示 |
| 提示词流程 | iterate 结果只保留按方向生成提示词（主路径）；通用生成按钮仅 analyze/critique 显示 |
| 上传体验 | Ctrl+V 粘贴截图、拖拽上传（高亮反馈）、Vision 已配置时上传后自动生成描述、文件类型校验 |
| 评估图表 | /assessment 新增纯 SVG 七维能力雷达图 + 整体/30天/7天判断差距对比条形图 |
| 帮助中心 | 新增「快捷操作」Section（中英双语） |
| i18n | 全部新文案 zh/en 双份同步 |
| 版本号 | main.py / data_io.py / tests → v2.2.0 |

### 修改的文件（V2.2.0）
| File | Change |
|------|--------|
| `backend/app/llm/deepseek_client.py` | +timeout/_get_timeout()/max_retries |
| `backend/app/main.py` | version→2.2.0 |
| `backend/app/services/data_io.py` | EXPORT_VERSION→v2.2.0 |
| `backend/app/tests/test_api.py` `test_preflight.py` | 版本断言→v2.2.0 |
| `frontend/src/app/page.tsx` | AgentProgress / 取消 / 自动滚动 / CollapsibleSection / 再练一次接线 / 提示词按钮条件化 |
| `frontend/src/components/TaskForm.tsx` | prefill / Ctrl+Enter / 不足提示 / 粘贴+拖拽上传 / 自动描述 |
| `frontend/src/components/TrainingPanel.tsx` | 错误/成功反馈，失败不清空表单 |
| `frontend/src/components/SessionList.tsx` | 详情弹窗+再练一次按钮（标题移至折叠栏） |
| `frontend/src/components/ReferencePanel.tsx` | 标题移至折叠栏 |
| `frontend/src/app/assessment/page.tsx` | +RadarChart +GapBars |
| `frontend/src/app/help/page.tsx` | +快捷操作 Section |
| `frontend/src/i18n/zh.ts` `en.ts` | +sections/progress/快捷键/上传/再练一次文案 |

---

## V2.1.3 变更（前一个版本）

V2.1.3 是本地发布包 / 跨平台部署验证版。不做新功能，专注整理发布包结构、部署文档、Codex 审查修复和发布验收。

### 第一轮：发布包结构
| 类别 | 变更 |
|------|------|
| .dockerignore | **New** — 排除 .env、真实数据、node_modules、.next、__pycache__、*.zip 等 |
| .gitignore | 重新整理分类，加固 backend/data/ 下 .gitkeep 例外规则 |
| data/ .gitkeep | database/、uploads/ 子目录新增 .gitkeep |
| LOCAL_DEPLOYMENT.md | **New** — Win/Mac/Linux 完整部署指南，含 FAQ |
| RELEASE_CHECKLIST.md | **New** — 8 大类逐项发布前验收清单 |
| README 第一屏 | 重写为面向普通用户的快速开始 |
| 版本号 | main.py / data_io.py / tests → v2.1.3 |
| 文档同步 | CHANGELOG (+V2.1.2 +V2.1.3) / RELEASE_NOTES / UPGRADE / SESSION_HANDOFF |

### 第二轮：Codex 审查修复
| 类别 | 变更 |
|------|------|
| /health、/system/status 版本 | 改为 `f"v{app.version}"` 动态获取，不再硬编码（之前与 /system/preflight 不一致导致测试失败） |
| start.bat 健康检查 | 添加 30 次 curl /health 等待循环，与 start.sh 对齐 |
| start_all.sh 路径 | 移除硬编码本机路径，改为 PATH 查找 + 环境变量可选覆盖 |
| UPGRADE.md 备份提醒 | 移到 git pull 命令之前（之前顺序不当） |
| ROADMAP.md | 移除 V2.1.1 过期「(当前版本)」标记 |
| PROJECT_STATUS.md 已知问题 | 修正「无 stop.bat（已有）」自相矛盾条目 |
| RELEASE_CHECKLIST.md | 修正 preflight Key 描述（不返回 Key 片段，只返回 configured/hint） |
| README 路径一致性 | 面向用户区域统一使用 `backend/data/config/`（加注容器内路径） |
| test_api.py | 新增 /health 版本断言，总断言数 3+1 |
| AGENTS.md | 测试数 210→212 |

### 第三轮：编码修复
| 类别 | 变更 |
|------|------|
| .bat 文件编码 | start.bat / stop.bat / restart.bat 从 UTF-8 转为 GBK，解决中文 Windows CMD 乱码和命令解析错误 |

### GitHub Release
- Tag: `v2.1.3` → commit `04b0ca6`
- Release URL: https://github.com/liuyun-flow/aesthetic-agent-system/releases/tag/v2.1.3
- 源码包仅含 .env.example（安全占位符），无敏感数据

## V2.1.2 变更（前一个版本）

V2.1.2 是本地发布体验热修复，修复三个实际使用中发现的阻塞问题。

| 类别 | 变更 |
|------|------|
| start.bat | 全重写为纯 Windows CMD，`cd /d "%~dp0.."` 解决双击路径错误，动态 compose 检测，中文提示 + pause |
| stop.bat | 新增纯 CMD 停止脚本 |
| restart.bat | 新增纯 CMD 重启脚本 |
| chunk 缓存恢复 | layout.tsx 全局 unhandledrejection 兜底，ChunkLoadError 自动刷新一次，二次显示 Ctrl+F5 指引 |
| Help 刷新 | 新增语义搜索/Embedding/训练评估/系统诊断/导入导出 Section + 6 FAQ（白屏/start.bat/Docker） |
| 版本号 | main.py / data_io.py / tests → v2.1.2 |

## 测试结果（V2.2.0）

- **212 passed**（analyze / critique / iterate / profile / sessions / upload / vision / reference / compare / prompt / training / health / settings / export / import / embeddings / semantic search / completeness / audit / duplicates / assessment / preflight / old-data compat / import version / DATABASE_URL detection）
- 全部使用 mocked agents + adapters，无需 API key
- Frontend build: ✅ 7 routes（经 `docker compose build frontend` 内 next build 验证）
- Docker compose config: ✅ 无警告
- GitHub Release 源码包清洁度: ✅ 仅 .env.example，无 .env / .db / app_config.json / 真实图片

---

## 已知问题

1. GitHub push 需代理（127.0.0.1:7891），代理未运行时 push 失败
2. Git Bash 下 curl 无法连接 127.0.0.1（用浏览器或 Python + ProxyHandler({}) 替代）
3. HTTP_PROXY 环境变量可能导致 Python urllib 本地连接失败
4. POST /settings/test-vision 只做文本 chat smoke test，不做真实 image input 测试
5. 前端 `NEXT_PUBLIC_API_BASE_URL` 是 build-time env，Docker 自定义部署需 rebuild
6. 语义搜索为暴力余弦相似度，案例量 <1000 时够用，未来可优化
7. 导出不含 embeddings（导入后需手动重建索引）
8. 导入仅合并模式，不做覆盖/去重
9. 误判检测基于关键词规则（非 LLM），精度受关键词覆盖影响
10. 维度评分使用间接关键词频率推断，非直接语义评估
11. 评估接口各自独立读取 DB（本地 SQLite 3000 条内可接受）
12. preflight 返回本地绝对路径可能暴露用户名
13. Apple Silicon Mac 通过 Docker 理论上支持，未经真实 Mac 完整测试
14. 缺少 `scripts/package-release` 自动生成干净发布包的脚本

---

## 尚未构建

- 多人 SaaS / 登录 / 云存储（远期）
- 训练差距随时间折线图（需新增按时间序列的评估端点；雷达图与差距对比图已在 V2.2.0 完成）
- 设置页「配置来源」展示
- 行业训练模板（V2.2）
- 自动发布包脚本（`scripts/package-release`）
- .bat 静态检查测试

## 下一步建议
V2.3 — 行业训练模板 / 案例库推荐 / 差距时间序列折线图
