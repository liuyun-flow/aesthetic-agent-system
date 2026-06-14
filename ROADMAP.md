# Roadmap

## 🔜 计划中 — V2.5 → V2.7（方向已与用户确认）

> 选定路线主轴：**先让度量可信，再做大**。Stage 1（V2.4）已完成；Stage 2（V2.5）已批准、待启动。
> 评测/校准台（V2.4 已建）是骨干：V2.5 grounding 的前置、V2.6 进 CI。

- **V2.5 闭环（curriculum + grounding）**
  - 首次运行预置案例库（注意版权/来源；考虑纯文本种子）；种子须过 V1.9 完整度门槛
  - top-N 案例注入 analyze/critique grounding（V2.2.1 起规划的 Phase 2）——**会改变评分，必须在评测台就位后做**
  - 结构化课程替代静态主题；assessment 推荐结构化并连向下一练习
- **V2.6 质量**：前端测试 + Playwright E2E + agent 输出评测进 CI（付费/非确定性评测走 nightly，不 gate PR）；真实 vision 集成测试；缓存（视觉描述可缓存、评分不缓存）；成本/延迟遥测
- **V2.7 触达**：运行时可配 API base URL（Next.js rewrite，解决 known issue #5）；桌面打包（Tauri/Electron，Python 后端打包是最大工程量）或托管 demo；**真正的门槛是 API key 而非打包**

备选方向（未选，见会话记录）：集成优先（Figma/浏览器扩展）、社区网络、垂直深耕、移动端、引擎 API 化。

## ✅ V2.4.1 — 信任度量复审收尾
- 诚实表述：`/assessment` 维度评分标注为「作品质量」而非「判断力」
- 评测台单测（19）：Spearman/分级排名/Pearson/成对预测/金标准校验
- 作品质量趋势折线（读取 ai_overall_score）
- 评测可复现（temperature=0 + --repeat 求均值）
- 误判 Tab 标注启发式 + AGENTS 代理文档
- 239 tests passed
- 复审遗留（需 key/Node/运行时）：M-1 真实校准基线 · R-1 前端测试 · R-4 Vision 直评校准 · R-6 运行时 API URL · R-7 遥测

## ✅ V2.4.0 — 信任度量（evaluation integrity）
- 评测/校准台 `backend/evals/`（dev-only）：金标准（成对 + 分档，合成脚手架待替换）+ 成对判对率 / Spearman / 分档单调性 + PROMPT_VERSION 钉死 + `--dry-run`
- 存储真实维度分：training_records +ai_dimension_scores/ai_overall_score/eval_prompt_version（_migrate_v2_4）；critique 保存 critic 8 维分，无额外 LLM
- 维度评估聚合 8 维（critic 6 + 价格感/商业适配），无分时回落关键词法
- critic 输出扩展到 8 维（新增 2 个可选商业维度）
- 可选 Vision 直评（SCORING_VISION_DIRECT，默认关、失败回落）
- 220 tests passed

## ✅ V2.3.0 — 一键收入案例库 + 描述质量优化
- 一键收入案例库（prefill + confirm）：训练结果/历史详情 → 自动填充案例表单 → 核对保存
- training_records 新增 image_id；`GET /sessions/{id}/case-draft` + 按分数推导审美等级
- Vision 自动描述新增商业推测字段（品类/目标用户/价格带/使用场景，标注 AI 推测）
- 描述完整度进度条 + 引导式补全字段（提交时并入作品描述）
- 216 tests passed

## ✅ V2.2.1 — Agent 审美内核强化
- 共享设计知识库 `design_knowledge.py`（意图优先 / 字体 / 色彩 / 版式 / 材质 / 高级感与廉价感信号）
- 评分五档锚点 + 反通胀规则（解决评分集中 6.5-8 舒适区）
- 证据规则（引用具体元素 + 点名原则，禁止空话）
- 四个审美 Agent 全部注入知识库；analyzer/critic 强制中文
- critique 改用推理模型
- 212 tests passed

## ✅ V2.2.0 — 工作台体验优化 + 评估图表
- AI 调用分阶段进度反馈 + 已等待秒数 + 取消按钮
- DeepSeek 客户端超时（120s 可配）+ 重试
- TrainingPanel 错误可见（保存失败不清空表单）
- 结果自动滚动 + 工作台折叠面板（状态持久化）
- 历史记录「再练一次」（载入描述重新自评）
- Ctrl+Enter 提交 + 描述不足提示
- 提示词流程合并（iterate 走按方向生成）
- Ctrl+V 粘贴 / 拖拽上传 / Vision 配置后自动描述
- /assessment 七维雷达图 + 判断差距对比图（纯 SVG）
- 帮助中心「快捷操作」Section
- 212 tests passed / Docker build 验证

## ✅ V1.5.2–V1.7 (已完成)
- 案例库数据导入/导出（JSON）
- Dockerfile / docker-compose
- .env 配置检查脚本
- 本地设置页 / BYOK 配置（`data/config/app_config.json`）
- DeepSeek / OpenAI Vision 连接测试
- 设置页只返回脱敏后的 key，不把 API Key 存到浏览器 localStorage

## ✅ V1.7.1 — 首次使用向导 / Help
- 首次使用向导（`/setup`）
- 帮助中心（`/help`）
- 工作台配置状态条
- `GET /system/status` 综合状态端点

## ✅ V1.7.2 — 迭代方向选择与提示词
- 结构化迭代方向（11 字段）
- 选择迭代方向后生成对应提示词
- 生成结果保存到对应 iterate 历史记录
- 历史详情展示所有方向、选中方向和对应提示词

## ✅ V1.8 — 数据导入/导出 + 语义搜索
- 数据导出 zip（manifest + cases + sessions + images，不含 API Key）
- 数据导入（zip slip 防护、ID 重映射、合并导入）
- 案例库语义搜索（OpenAI text-embedding-3-small）
- ReferenceCaseEmbedding 模型 + reindex
- 语义搜索 fallback 到普通筛选（不崩溃）
- 前端数据管理 UI + 语义搜索 UI

## ✅ V1.8.1 — 稳定性修复 / 发布前整理
- 版本号统一
- .gitignore 补充 `*.zip`
- 全量回归测试 158 passed
- Docker 路径验证
- 导出包结构验证
- 文档同步

## ✅ V2.1.2 — 本地发布体验热修复
- Windows start.bat 纯 CMD 重写（`cd /d "%~dp0.."`）
- stop.bat / restart.bat 新增
- 前端 chunk 缓存自动恢复（ChunkLoadError 全局兜底）
- Help 页面内容刷新（+4 Section + 6 FAQ）
- 212 tests passed

## ✅ V2.1.3 — 本地发布包 / 跨平台部署验证版
- 新增 `.dockerignore` — 排除敏感数据和构建产物
- 新增 `docs/LOCAL_DEPLOYMENT.md` — Win/Mac/Linux 完整部署指南
- 新增 `docs/RELEASE_CHECKLIST.md` — 发布前 8 大类检查清单
- 完善 `.gitignore` — 加固 data/ 目录 .gitkeep 规则
- README 第一屏重写 — 面向普通用户
- 版本号同步 v2.1.2 → v2.1.3

## ✅ V2.1.1 — 本地正式发布版稳定性修复 / 发布候选
- 版本号同步（preflight 使用 app.version）
- 文档准确性修正
- 210 tests passed

## ✅ V2.1.0 — 本地正式发布版 / 安装体验优化
- 一键启动脚本（start.sh / start.bat）
- 停止脚本（stop.sh）
- /system/preflight 系统预检端点
- 设置页系统诊断面板
- CHANGELOG / UPGRADE / RELEASE_NOTES 文档
- 一键启动 + 启动后诊断 + 备份提醒
- 210 tests passed

## ✅ V2.0.1 — 训练评估稳定性与数据校准
- 趋势判断阈值文档化（±3 gap, ±5pp rate）
- 关键词精度优化（去歧义、去冲突）
- 旧数据兼容增强
- 199 tests passed

## ✅ V2.0.0 — 训练效果评估系统
- 训练效果总览（频率、评分、差距趋势）
- 常见误判类型统计（10 种规则化检测）
- 审美能力维度评估（7 维度 0-100 评分）
- 周期复盘报告（7/30 天切换）
- 评估页面（/assessment）含总览卡片 + 误判/维度/复盘 Tab
- 192 测试 passed

## ✅ V1.9.1 — 案例库质量管理稳定版
- aesthetic_level 验证统一（_is_present 替换内联检查）
- _is_present 增强（支持 list/dict 非空判断）
- _tokenize_title None 防护
- audit issue 字段补全（is_training_ready + reason）
- 嵌入重复检测全量匹配（移除 break）
- missing_learning_notes 逻辑修复（AND → OR）
- 前端 null 安全加固（全面 ?? 守卫）
- 前端空状态页面
- 181 测试 passed

## ✅ V1.9.0 — 案例库质量管理
- 案例完整度评分（0-100，13 字段加权动态计算）
- 训练可用状态判定（is_training_ready）
- 案例库体检接口（GET /reference-cases/audit）
- 案例库体检页面（/audit）
- 重复案例检测（标题相似度 + embedding 相似度双层回退）
- 案例列表增强（完整度分数、训练可用标记、缺失字段提示）
- 语义搜索结合训练可用状态排序

## V2.0 — 多人化（远期）
- 用户登录/注册
- 多用户隔离
- 云存储（图片/CDN）
- 付费/订阅
- 部署到云服务

## Future Ideas
- 浏览器扩展（右键分析任意网页设计）
- Figma 插件（直接在 Figma 里分析设计稿）
- 训练课程模板（新手→进阶 30 天训练计划）
- 社区案例分享
