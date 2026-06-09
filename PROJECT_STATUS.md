# Project Status — V2.1.2

## Current Version
**V2.1.2** — 本地发布体验热修复 / Windows 启动脚本 / chunk 缓存恢复 / Help 刷新

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

## V2.1.2 变更（本次）

V2.1.2 是本地发布体验热修复，修复三个实际使用中发现的阻塞问题。

| 类别 | 变更 |
|------|------|
| start.bat | 全重写为纯 Windows CMD，`cd /d "%~dp0.."` 解决双击路径错误，动态 compose 检测，中文提示 + pause |
| stop.bat | 新增纯 CMD 停止脚本 |
| restart.bat | 新增纯 CMD 重启脚本 |
| chunk 缓存恢复 | layout.tsx 全局 unhandledrejection 兜底，ChunkLoadError 自动刷新一次，二次显示 Ctrl+F5 指引 |
| Help 刷新 | 新增语义搜索/Embedding/训练评估/系统诊断/导入导出 Section + 6 FAQ（白屏/start.bat/Docker） |
| 版本号 | main.py / data_io.py / tests → v2.1.2 |

## 测试结果

- **212 passed**（analyze / critique / iterate / profile / sessions / upload / vision / reference / compare / prompt / training / health / settings / export / import / embeddings / semantic search / completeness / audit / duplicates / assessment / preflight / old-data compat / import version / DATABASE_URL detection）
- 全部使用 mocked agents + adapters，无需 API key
- Frontend build: ✅ 7 routes (/, /settings, /help, /setup, /audit, /assessment, /_not-found)
- Docker compose config: ✅ 无警告

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
12. 无 Windows stop.bat 对应的一键停止（已有 stop.bat）
13. preflight 返回本地绝对路径可能暴露用户名

---

## 尚未构建

- 多人 SaaS / 登录 / 云存储（远期）
- 训练效果图表（折线图、雷达图）
- 设置页「配置来源」展示
- 行业训练模板（V2.2）

## 下一步建议
V2.2 — 行业训练模板 / 案例库推荐 / 图表可视化
