# Changelog

## V2.2.1 (2026-06-12)
- **Agent 审美内核强化** — 修复智能体审美判断空泛的根本原因
- 新增 `app/agents/design_knowledge.py` 共享设计知识库：意图优先评判 / 字体 / 色彩 / 版式 / 材质 / 高级感与廉价感信号清单，全部为可证伪的具体准则
- 评分校准：1-10 五档锚点（9-10 一线作品集级 … 1-2 传达失败）+ 反通胀规则（从 5-6 档出发凭证据加减、违反原则至少 -1、无亮点不给 8+、短板拖累总分、信息不足保守取低分）
- 证据规则：每条判断必须引用描述中的具体元素并点名所依据原则，禁止空洞措辞和编造细节
- analyzer / critic / iterator / reference_comparator 四个智能体全部注入知识库；分析与评分输出强制中文
- iterator 方向必须基于知识库原则、至少一个方向保留当前商业意图、risk 必须是真实取舍
- critique 改用推理模型（评分是判断最重的任务；延迟由 V2.2 进度 UI + 客户端超时兜底）
- 版本号同步 v2.2.0 → v2.2.1
- 212 tests passed

## V2.2.0 (2026-06-12)
- 工作台体验优化 + 评估图表，不改后端业务逻辑
- AI 调用等待改为分阶段进度卡片（任务专属文案 + 已等待秒数 + 进度条）+「取消」按钮
- DeepSeek 客户端新增 120s 超时（`DEEPSEEK_TIMEOUT_SECONDS` 可配）+ 1 次重试
- 训练面板「标记完成」失败不再静默清空表单，显示错误；成功显示「已保存 ✓」
- 结果就绪自动滚动到可视区；今日训练/案例库/历史记录改为可折叠面板（记住状态）
- 历史详情新增「再练一次」—— 载入当时的作品描述重新自评，对比过去的判断
- Ctrl+Enter 快速提交；描述不足 10 字时在按钮旁说明原因
- iterate 结果统一走「按方向生成提示词」，通用提示词按钮仅 analyze/critique 显示
- 图片上传支持 Ctrl+V 粘贴截图、拖拽上传；Vision 已配置时上传后自动生成描述
- /assessment 新增七维能力雷达图 + 整体/30天/7天判断差距对比图（纯 SVG 无依赖）
- 帮助中心新增「快捷操作」Section
- 版本号同步 v2.1.3 → v2.2.0（main.py / data_io.py / tests）
- 212 tests passed；前端经 `docker compose build frontend` 验证

## V2.1.3 (2026-06-10)
- 本地发布包 / 跨平台部署验证版
- 新增 `docs/LOCAL_DEPLOYMENT.md` — Windows / Mac / Linux 完整部署指南
- 新增 `docs/RELEASE_CHECKLIST.md` — 发布前安全检查清单
- 新增 `.dockerignore` — 排除敏感数据、node_modules、构建产物
- 完善 `.gitignore` — 加固 `backend/data/` 下 .gitkeep 例外规则
- 完善 `backend/data/` 目录结构 — 所有子目录含 .gitkeep
- README 第一屏重写 — 面向普通用户的快速开始
- 版本号同步 v2.1.2 → v2.1.3（main.py / data_io.py / tests）
- 部署文档覆盖：Docker 依赖说明、Win/Mac/Linux 启动步骤、常见问题解答

## V2.1.2 (2026-06-10)
- Windows start.bat 纯 CMD 全重写（`cd /d "%~dp0.."` 双击路径修复）
- 新增 stop.bat / restart.bat 纯 CMD 脚本
- 前端 chunk 缓存自动恢复（ChunkLoadError 全局兜底）
- Help 页面内容刷新（+4 Section + 6 FAQ）
- 212 tests passed

## V2.1.1 (2026-06-09)
- 版本号同步：`/system/preflight` 改用 `app.version` 避免硬编码
- 文档准确性修正（测试数、版本号）
- 升级指南补充 V2.1.0→V2.1.1 步骤
- 210 tests passed

## V2.1.0 (2026-06-09)
- 新增 `/system/preflight` 本地环境诊断端点
- 新增设置页「系统诊断」面板（含 DeepSeek/Vision/Embedding/数据库/目录状态）
- 新增一键启动脚本：`scripts/start.sh`（Docker）、`scripts/start.bat`（Windows）
- 新增停止脚本：`scripts/stop.sh`
- 新增文档：UPGRADE.md、RELEASE_NOTES.md、CHANGELOG.md
- 设置页备份提醒增强（升级前提示、不含 Key 说明）
- 版本号 v2.1.0

## V2.0.1 (2026-06-09)
- 训练评估稳定性校准：统一双评分有效数据阈值
- `selected_direction` 非 dict 格式容错
- 导入版本检查接受 v2.x 前缀
- 关键词精度优化
- 前端报告错误态补齐
- 测试 202 passed

## V2.0.0 (2026-06-09)
- 训练效果评估系统：总览、误判统计、能力维度 7 维评分、周期复盘
- `/assessment` 页面
- 4 个 assessment 端点
- 192 tests passed

## V1.9.1 (2026-06-09)
- 案例库质量管理稳定版
- aesthetic_level 验证统一
- 前端 null 安全加固

## V1.9.0 (2026-06-09)
- 案例完整度评分
- 训练可用状态判定
- 案例库体检接口与页面
- 重复案例检测

## V1.8.1 (2026-06-08)
- 稳定性修复 / 发布前整理
- 版本统一、导出验证、回归测试

## V1.8.0 (2026-06-08)
- 数据导出/导入（zip 备份）
- 案例库语义搜索（OpenAI embeddings）

## V1.7.2 (2026-06-07)
- 迭代方向选择生成提示词
- 结构化迭代字段

## V1.7.1 (2026-06-07)
- 首次使用向导（/setup）
- 帮助中心（/help）
- 配置状态条

## V1.7.0 (2026-06-07)
- 本地设置页 / BYOK 配置
- DeepSeek / Vision 连接测试

## V1.6.0 (2026-06-07)
- Docker 支持
- 配置检查脚本
- 数据目录整理

## V1.5.1 (2026-06-07)
- 案例图片 + 审美标注

## V1.5.0 (2026-06-07)
- 训练工作台
- 每日主题 / 统计 / 每周复盘

## V1.4.x (2026-06-06)
- 参考案例库 CRUD + 对比
- 中文 UI
- OpenAI Vision 支持
- Vision 状态端点

## V1.3.0 (2026-06-06)
- VisionAdapter 可插拔架构
- 自动图片描述

## V1.2.0 (2026-06-06)
- 图片上传 / 手动描述

## V1.1.0 (2026-06-06)
- 用户自评 + 判断差异分析
- Profile 训练反馈

## V1.0.0 (2026-06-06)
- MVP: analyze / critique / iterate
