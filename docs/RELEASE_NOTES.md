# V2.4.1 发布说明

## 关于本版本

V2.4 系列的主题是**信任度量（evaluation integrity）**：让"系统能测量你的审美判断力进步"这个核心承诺真正可信。V2.4.0 建立机制，V2.4.1 是其后的全面复审收尾。

完整逐项变更见 [CHANGELOG](CHANGELOG.md)；本文件只讲重点。

## V2.4 系列做了什么

### 评测 / 校准台（dev-only）
- 新增 `backend/evals/`（不进运行时镜像）：金标准集 + `run_eval.py` 计算成对判对率 + Spearman 排序相关性 + 分档单调性，`PROMPT_VERSION` 钉死便于发现回归
- `--dry-run` 无需 key 即可校验金标准；`--repeat N` 求均值降噪，评分以 temperature=0 复现
- 19 个确定性单测保障评测台的度量数学（`app/tests/test_evals.py`）
- 当前金标准为合成脚手架（纯文字，规避版权），待替换为真实"公认强/弱"样本

### 存储真实维度分 + 维度评估
- `training_records` 新增 `ai_dimension_scores` / `ai_overall_score` / `eval_prompt_version`（启动自动迁移 `_migrate_v2_4`，旧数据安全）
- 每次评分（critique）保存 critic 的 8 维得分（critic 6 维 + 价格感 / 商业适配，归一化 0-100），不额外调用 LLM
- `/assessment/dimensions` 有存储分时聚合 8 维，无分时回落到原关键词法
- **诚实表述**：维度评分明确标注为"作品质量评分"而非"判断力分数"
- 作品质量趋势折线（读取 `ai_overall_score`）

### Vision 直评（可选，实验性）
- `SCORING_VISION_DIRECT=1` + OpenAI vision key 时，评分直接观察图片（多模态），绕过"图→文"瓶颈
- 默认关闭；任何失败自动回落文本评分路径

## 发布形态

与既往一致，**本地部署版（Local Release）**：

- ✅ 用户下载 zip → 解压 → Docker Desktop 启动 → 配置 API Key → 使用
- ❌ 不是 SaaS / 不做登录 / 不做云端存储

## 系统要求

- Docker Desktop（必须）
- DeepSeek API Key（必须）
- OpenAI API Key（可选，用于 Vision 自动描述、语义搜索、可选的 Vision 直评）

> 说明：本地使用无需任何代理。开发者向 GitHub 推送代码时若在受限网络下可能需要代理，但这与最终用户的部署和使用无关。

## 从 V2.3.x 升级

```bash
git pull origin main
docker compose up --build -d
```

`ai_dimension_scores` 等新列通过启动时自动迁移添加，旧数据安全无需手动处理。升级前建议先导出备份（设置页 → 数据管理 → 导出）。详见 [升级指南](UPGRADE.md)。

## 已知限制

- 维度评分衡量的是「作品质量」而非「判断力」；判断力差距见「平均判断差距」（判断力分维度度量是后续工作）
- 评测台金标准目前为合成脚手架，真实校准基线需配置 key 后运行 `python -m evals.run_eval` 并替换为真实样本
- Vision 直评为实验性，默认关闭，启用后需单独校准
- 误判检测基于关键词启发式（非 LLM）
- 语义搜索需要 OpenAI API Key；导出不含 embeddings；导入为合并模式不做去重
- Apple Silicon Mac 通过 Docker 理论上支持，但未经真实 Mac 完整测试

## 下一步

- 用真实样本与 key 跑评测台基线，确认 critic 校准
- V2.5 信心：CI + 前端测试/E2E + 缓存 + 成本/延迟遥测
- ~V3.0 闭环：预置案例库 + top-N grounding + 结构化课程
- 判断力分维度度量（收集用户分维度自评）
