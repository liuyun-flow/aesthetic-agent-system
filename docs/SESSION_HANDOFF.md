# Session Handoff — 2026-06-14

## Last Completed
- **V2.4.1: 信任度量复审收尾 — 239 tests passed**（诚实表述 + 评测台 19 单测 + 作品质量趋势 + 评测可复现 + 误判启发式标注）。前端经 Docker build 验证。
- V2.4.0: 信任度量（评测台 + 存储真实维度分 + 维度聚合 8 维 + 可选 Vision 直评）
- V2.3.0: 一键收入案例库 + 描述质量优化（已发布 Release v2.3.0）
- V2.2.1 / V2.2.0：Agent 审美内核 / 工作台体验（已发布）

---

## V2.4.0 交付（信任度量，本次会话）

按计划 [docs/V2.4_PLAN.md](V2.4_PLAN.md) 的 6 个里程碑执行：
- **M1 评测台**：`backend/evals/`（dev-only，.dockerignore 排除）。run_eval.py 算成对判对率 + Spearman + 分档单调性；`PROMPT_VERSION` 钉在 design_knowledge.py；金标准为合成脚手架（gold/*.jsonl），**待用户替换真实样本**。`--dry-run` 无 key 校验。
- **M2 存储维度分**：training_records +3 列（ai_dimension_scores/ai_overall_score/eval_prompt_version），`_migrate_v2_4` 自动加列；critique 经 `_extract_dimension_kwargs` 存 critic 8 维分（0-100），不额外调 LLM。
- **M3 聚合**：assessment.compute_dimension_scores 派发——有存储分→`_aggregate_dimension_scores`（8 维 = critic 6 + 价格感/商业适配）；无分→`_keyword_dimension_scores`（原逻辑，保旧数据/无 key 行为）。旧 assessment 测试因此全绿。
- **M4 校准**：harness 接好、import 验证、dry-run 通过；**实跑基线需真实 key**：`cd backend && python -m evals.run_eval`（用户运行）。
- **M5 Vision 直评（可选实验性）**：`SCORING_VISION_DIRECT=1` + OpenAI vision key 时 critique 走 `VisionCriticAgent` 直接看图打分；默认关、任何失败回落文本 critic。
- **M6 收尾**：版本 v2.4.0、.env.example +2 项、docs 全同步、RELEASE_CHECKLIST +评测项。

关键设计点（备查）：维度评估现在测的是「作品质量分聚合」而非「用户判断准确度」——后者需用户分维度自评输入，是 V2.5+ 的渐进项。

---

## V2.3.0 交付（来自用户实测反馈）

**功能 1 — 一键收入案例库（prefill + confirm）**：训练结果区/历史详情「收入案例库」→ `GET /sessions/{id}/case-draft` 生成草稿（含按 ai_score 推导审美等级）→ 前端自动展开案例库并预填表单 → 用户核对等级/目标用户/价格带后保存。新增 `image_id` 到 training_records（`_migrate_v2_3`），analyze/critique/iterate 记录所用图片。

**功能 2 — 描述质量优化**：VisionDescription +4 商业推测字段（品类/目标用户/价格带/使用场景，标注「AI 推测」，信息不足返回 null）；TaskForm 描述完整度进度条 + 引导式补全字段（可一键采用 Vision 推测，提交时并入作品描述）。

**未做（用户当时选择不做）**：描述增强 Agent（2b-agent）—— DeepSeek 改写粗描述为完整描述。如需可作为下一阶段。

**相关下一步**：把案例库 top-N 注入 analyze/critique grounding（V2.2.1 起就规划的 Phase 2）；现在案例库收集更顺畅，这一步收益更高。

---

---

## V2.2.1 交付（Agent 审美内核）

**诊断**：四个审美 Agent 的 prompt 只有角色设定（"你是专业评论家"），没有真实设计知识、评分锚点、证据纪律 → 输出空泛、评分挤在 6.5-8。

**交付**：
1. `app/agents/design_knowledge.py` — 共享知识库（意图优先评判 / 字体 / 色彩 / 版式 / 材质 / 高级感与廉价感信号清单）+ 评分五档锚点 + 反通胀五规则 + 证据规则
2. analyzer / critic / iterator / reference_comparator 系统提示词全部注入知识库；analyzer/critic 强制中文输出
3. `main.py get_critic`（和 orchestrator）改用推理模型
4. 版本 v2.2.1，212 tests passed

**下一步（已与用户讨论的 Phase 2）**：把案例库接入 analyze/critique（取 top N training-ready 案例的 premium/cheapness/learn_from_this 注入 prompt），需同步更新 test mock 签名。

---

## V2.2.0 完整交付

V2.2.0 是体验优化版，聚焦用户友好度、便捷性和训练有效性。后端业务逻辑不变（仅加 LLM 客户端超时）。

### 按优先级交付的 9 项改进

1. **DeepSeek 客户端超时** — `deepseek_client.py` 加 `timeout=120s`（`DEEPSEEK_TIMEOUT_SECONDS` 或 config store `deepseek.timeout_seconds` 可配）+ `max_retries=1`
2. **分阶段进度 + 取消** — analyze/critique/iterate 等待时显示任务专属阶段文案（每 6 秒推进，纯节奏展示非真实进度）、已等待秒数、进度条；「取消」按钮用 AbortController 中断；取消显示中性灰色提示
3. **TrainingPanel 错误可见** — 标记完成失败不再清空表单且显示错误（之前 `catch {}` 静默吞掉、表单照清）；成功显示「已保存 ✓」；周复盘失败同样显示
4. **工作台结构** — 结果就绪自动 `scrollIntoView`；今日训练/参考案例库/最近训练记录改为 `CollapsibleSection`（localStorage 按面板记住开合，案例库默认收起）；子组件内重复标题已移除
5. **再练一次** — 历史详情弹窗新增主按钮：载入该记录的作品描述+任务类型回表单（`prefill` prop，key 用时间戳保证同记录可重复载入），滚动到顶部并显示蓝色提示条
6. **Ctrl+Enter + 禁用原因** — 描述框内 Ctrl/Cmd+Enter 提交；不足 10 字时按钮旁琥珀色提示
7. **提示词流程合并** — iterate 只走「按方向生成提示词」；通用「生成可复制提示词」仅 analyze/critique 显示
8. **上传体验** — 全页 Ctrl+V 粘贴截图；拖拽上传（拖入高亮）；Vision 已配置且非占位时上传后自动调用 describe；类型校验（JPG/PNG/WebP）
9. **评估图表** — `/assessment` 新增纯 SVG `RadarChart`（七维 0-100）+ `GapBars`（整体/30天/7天差距对比，越小越好）；不造假时间序列（API 无逐次数据）

另：帮助中心新增「快捷操作」Section（中英双语）；所有新文案 zh.ts/en.ts 同步。

## 修改的文件

| 文件 | 变更 |
|------|------|
| `backend/app/llm/deepseek_client.py` | +DEFAULT_TIMEOUT_SECONDS/_get_timeout()/max_retries |
| `backend/app/main.py` | version → 2.2.0 |
| `backend/app/services/data_io.py` | EXPORT_VERSION → v2.2.0 |
| `backend/app/tests/test_api.py` | 3 处版本断言 → v2.2.0 |
| `backend/app/tests/test_preflight.py` | 1 处版本断言 → v2.2.0 |
| `frontend/src/app/page.tsx` | +AgentProgress +CollapsibleSection +abortRef/canceled +resultRef 自动滚动 +prefill/handleRetrain +iterate 提示词按钮条件化 |
| `frontend/src/components/TaskForm.tsx` | +prefill +Ctrl+Enter +tooShortHint +uploadFile/describeImage 重构 +粘贴/拖拽 +自动描述 |
| `frontend/src/components/TrainingPanel.tsx` | +completeError/completeSaved/reviewError，失败不清空表单 |
| `frontend/src/components/SessionList.tsx` | +onRetrain prop +详情弹窗「再练一次」按钮；内部 h2 移除（标题在折叠栏） |
| `frontend/src/components/ReferencePanel.tsx` | 内部 h2 移除（标题在折叠栏），添加按钮右对齐 |
| `frontend/src/app/assessment/page.tsx` | +RadarChart +GapBars（纯 SVG） |
| `frontend/src/app/help/page.tsx` | +「快捷操作」Section |
| `frontend/src/i18n/zh.ts` / `en.ts` | +sections +progress +form 快捷键/上传 +sessions.retrain |
| `CLAUDE.md` | 版本线 +V2.2；Quick Commands 更新为本机实际可用命令 |
| `PROJECT_STATUS.md` / `ROADMAP.md` / `docs/CHANGELOG.md` | V2.2.0 同步 |

## Test Results
- **212 passed**，1 warning（httpx deprecation）
- 前端构建：✅ `docker compose build frontend`（镜像内 next build，7 routes）

## 本机环境注意（本次会话发现）
1. **裸 `python` 指向 `E:\Program Files (x86)\python.exe`，没有 fastapi**；项目依赖装在 `C:\Users\Dream\AppData\Local\Programs\Python\Python311`。跑测试用：
   `cd backend && C:/Users/Dream/AppData/Local/Programs/Python/Python311/python.exe -m pytest app/tests/ -q`
2. **本机已无全局 node/npx**（git-bash 和 PowerShell PATH 均无）；前端 build 验证用 `docker compose build frontend`
3. `.claude/settings.local.json` 的 permissions 在**会话启动时**加载，会话中途修改不生效；allow 规则按命令段匹配（`cd X && cmd | tail` 拆段），规则里不要写 `cd ... &&`
4. 代理：本机 git 曾有 local override 指向失效端口 7891，已 `git config --local --unset http.proxy/https.proxy` 改用全局（当前 7890）；`gh` 受 `HTTP_PROXY` env 影响，env 端口失效时需临时覆盖。**代理纯属开发机网络问题，不写入仓库，最终用户无需代理**

## 已知问题（继承 V2.1.3）
1. 开发者受限网络下 push 需本机代理（端口随代理软件变化，不入仓库）；最终用户部署无需代理
2. POST /settings/test-vision 只做文本 chat smoke test
3. 语义搜索为暴力余弦相似度，案例量 <1000 时够用
4. 导出不含 embeddings（导入后需重建索引）
5. 导入仅合并模式，不做覆盖/去重
6. 误判检测基于关键词规则（非 LLM）
7. preflight 返回本地绝对路径可能暴露用户名
8. Apple Silicon Mac 未经真实机器测试
9. 缺少 `scripts/package-release` 自动打包脚本

## 本会话后续（2026-06-14）
V2.3.0 发布后，本会话主要是**文档同步 + 演进路线规划**，无新增代码：
- 文档同步提交 `39c2fb6`：README 去掉硬编码版本徽标（改为链接 Releases/CHANGELOG）+ 补 V2.2/V2.2.1/V2.3 版本表行；RELEASE_NOTES 重写为 V2.3.0；UPGRADE 补 V2.2.x/V2.3.0 段；AGENTS 测试数 212→216
- 修复本机 git 代理（见已知问题 #1）
- **确认演进路线 V2.4 → V2.7**（详见 [ROADMAP.md](../ROADMAP.md) 顶部「计划中」）

## Next Session — V2.4.x 已完成；版号 2026-06-15 重排
- **重排**：用户优先「信心（质量/可靠性）」→ 提前为 **V2.5**（[docs/V2.5_PLAN.md](V2.5_PLAN.md)，决策已定）；原 V2.5 闭环（种子/grounding/课程）顺延至 **~V3.0**（[docs/V3.0_PLAN.md](V3.0_PLAN.md)）。
- **环境变化**：本机已装 **Node v24.16.0**，`npm run build` 已验证；前端测试不再受阻。
- **V2.5 下一步（已选 N1+N2 切片先做）**：N1 CI 脚手架（GitHub Actions：mocked pytest + 前端 build/lint）→ N2 缓存（只缓存视觉描述）+ 遥测（DB+设置页）→ N3 前端组件测试 → N4 E2E → N5 评测进 on-release CI → N6 收尾 v2.5.0。
- **独立待办（需 key）**：M-1 真实校准基线 `cd backend && python -m evals.run_eval --repeat 3` + 替换 `backend/evals/gold/*.jsonl` 真实样本；R-4 Vision 直评校准。
- **之后**：V2.7 触达（运行时 API URL / 桌面打包；**API key 才是触达真门槛**） · **~V3.0 闭环**（预置案例库 + top-N grounding[改评分须配评测护栏] + 结构化课程；详见 [V3.0_PLAN.md](V3.0_PLAN.md)）。
- 关键坑（已走查）：grounding 会使校准失效需重跑评测台；种子案例版权；Python 桌面打包工程量大。
