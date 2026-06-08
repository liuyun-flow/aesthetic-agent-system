# Project Status — V1.8.1

## Current Version
**V1.8.1** — 稳定性修复 / 回归测试 / 发布前整理

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
| **V1.8.1** | **稳定** | 版本统一 / .gitignore / 回归测试 / 文档同步 |

---

## V1.8 核心交付（前一个版本）

### 数据导出/导入
- `GET /export` — 生成 zip，含 manifest + cases + sessions + 图片元数据 + uploads/*
- `POST /import` — 合并导入，zip slip 防护，ID 重映射
- 导出包含 config_summary.json（provider / model 名称），**不含 API Key**
- 前端设置页 → 数据管理区（导出下载 + 导入上传 + 结果统计）

### 语义搜索
- `ReferenceCaseEmbedding` 模型（case_id + provider + model + embedding_json + source_text_hash）
- `POST /reference-cases/reindex-embeddings` — 批量生成/更新 embeddings
- `POST /reference-cases/search-semantic` — 余弦相似度搜索，支持 category/aesthetic_level/price_band 过滤
- `GET /embedding/status` — 配置状态，未配置时返回中文提示
- OpenAI text-embedding-3-small，复用 OPENAI_API_KEY
- 前端参考案例面板：搜索框 + 重建索引 + 相似度展示 + 中文提示
- compare-with-references 语义 fallback（无 case_ids 时用 semantic_query 匹配）

---

## V1.8.1 变更（本次）

| 类别 | 变更 |
|------|------|
| 版本号 | main.py / export manifest / health / system/status 统一为 v1.8.1 |
| .gitignore | 新增 `*.zip`（防止导出备份包被提交） |
| 测试 | 全量回归 158 passed |
| Docker | compose config 通过，挂载点验证（data/config, database, uploads） |
| 导出验证 | zip 结构完整，无 API Key 泄露，23 图片正确打包 |
| 前端 | build 通过（5 routes） |
| 文档 | README / PROJECT_STATUS / ROADMAP / SESSION_HANDOFF 全部同步 |

### 修改的文件（本次）
| File | Change |
|------|--------|
| `.gitignore` | +`*.zip` |
| `backend/app/main.py` | version→1.8.1 ×3 |
| `backend/app/services/data_io.py` | EXPORT_VERSION→v1.8.1 |
| `backend/app/tests/test_api.py` | 2 tests 版本断言更新 |
| `README.md` | 版本 + V1.8/V1.8.1 说明 |
| `ROADMAP.md` | 完整重写，标注已完成版本 |
| `PROJECT_STATUS.md` | 本文档 |
| `docs/SESSION_HANDOFF.md` | 更新 |

---

## 测试结果

- **158 passed**（覆盖 analyze / critique / iterate / profile / sessions / upload / vision / reference / compare / prompt / training / health / settings / export / import / embeddings / semantic search）
- 全部使用 mocked agents + adapters，无需 API key
- Frontend build: ✅ 5 routes (/, /settings, /help, /setup, /_not-found)
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

---

## 尚未构建

- 多人 SaaS / 登录 / 云存储（V2.0）
- 案例库质量管理（V1.9 — 重复检测、字段完整性校验、等级分布统计）
- 设置页「配置来源」展示（减少 .env 与设置页混用困惑）

## 下一步建议
V1.9 — 案例库质量管理 + 当前已知问题的修复
