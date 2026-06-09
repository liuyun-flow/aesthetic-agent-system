# Project Status — V1.9.1

## Current Version
**V1.9.1** — 案例库质量管理稳定版 / 安全加固 / 回归测试

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
| **V1.9.1** | **稳定** | aesthetic_level 验证统一 / null 安全加固 / audit issue 字段补全 / 前端防御 guard |

---

## V1.9.0 变更（本次）

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

## V1.9.1 变更（本次）

V1.9.1 是 V1.9 的稳定性修复版，不新增业务功能。

| 类别 | 变更 |
|------|------|
| aesthetic_level 验证 | 统一使用 `_is_present()` 替换四处内联检查，同时拒绝 "unknown"/"n/a"/"none"/"暂无" 等占位值 |
| _is_present 增强 | 新增 list/dict/tuple/set 非空判断 |
| _tokenize_title | 新增 None 防护，避免空 title 导致审计端点崩溃 |
| audit issue 字段补全 | `_case_summary` 新增 `is_training_ready`、`reason`；AuditIssue schema 同步新增 |
| 重复检测 | 移除 embedding 匹配的 `break`，报告所有高相似度匹配 |
| missing_learning_notes | AND 改为 OR，缺任一字段即标记 |
| 前端 null 安全 | 所有数组访问添加 `??` 守卫；StatCard 防 NaN/负数 |
| 前端空状态 | 案例库为空时显示专用空状态提示 |
| 前端完整度颜色 | completenessColor/Bg 新增 null/NaN 灰度处理 |
| 版本号 | main.py / data_io.py / tests → v1.9.1 |

## 测试结果

- **181 passed**（analyze / critique / iterate / profile / sessions / upload / vision / reference / compare / prompt / training / health / settings / export / import / embeddings / semantic search / completeness / audit / duplicates / stability）
- 全部使用 mocked agents + adapters，无需 API key
- Frontend build: ✅ 6 routes (/, /settings, /help, /setup, /audit, /_not-found)
- Docker compose config: ✅ 无警告

---

## 已知问题

1. GitHub push 需代理（127.0.0.1:7891），代理未运行时 push 失败
2. Git Bash 下 curl 无法连接 127.0.0.1（用浏览器或 Python + ProxyHandler({}) 替代）
3. HTTP_PROXY 环境变量可能导致 Python urllib 本地连接失败
4. `backend/.env` DATABASE_URL 仍指向 `./aesthetic.db`（历史遗留，**不要贸然改**）
5. POST /settings/test-vision 只做文本 chat smoke test，不做真实 image input 测试
6. 前端 `NEXT_PUBLIC_API_BASE_URL` 是 build-time env，Docker 自定义部署需 rebuild
7. 语义搜索为暴力余弦相似度，案例量 <1000 时够用，未来可优化
8. 导出不含 embeddings（导入后需手动重建索引）
9. 导入仅合并模式，不做覆盖/去重
10. 完整度评分为动态计算（不写 DB），大量案例时需关注性能

---

## 尚未构建

- 多人 SaaS / 登录 / 云存储（V2.0）
- 训练效果评估系统（V2.0 — 训练前后对比、成长曲线、里程碑）
- 设置页「配置来源」展示（减少 .env 与设置页混用困惑）

## 下一步建议
V2.0 — 训练效果评估系统 + 当前已知问题的修复
