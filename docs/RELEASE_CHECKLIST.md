# 发布前检查清单 / Release Checklist

通用清单 — 每次发布前逐项确认（不绑定具体版本号）。

---

## 一、安全检查（Security）

发布包不得包含任何真实用户数据或密钥。

- [ ] **不包含 `.env`** — 发布包中只有 `.env.example`，没有 `backend/.env`
- [ ] **不包含真实 API Key** — 全文搜索 `sk-`、`sk-or-` 等密钥前缀，确保零命中
- [ ] **不包含真实数据库** — `backend/data/database/` 只有 `.gitkeep`，没有 `*.db` 文件
- [ ] **不包含真实上传图片** — `backend/data/uploads/` 只有 `.gitkeep`，没有真实图片
- [ ] **不包含真实配置文件** — `backend/data/config/` 只有 `.gitkeep`，没有 `app_config.json`
- [ ] **不包含导出备份包** — 项目根目录和各级子目录没有 `*.zip`
- [ ] **不包含 node_modules** — `frontend/node_modules/` 不在发布包中
- [ ] **不包含 .next** — `frontend/.next/` 不在发布包中
- [ ] **不包含 __pycache__** — 所有 Python 缓存目录均被排除
- [ ] **不包含 .pytest_cache** — 测试缓存目录被排除
- [ ] **README / 文档不含真实 API Key** — 所有示例 Key 使用 `replace-me` 或 `sk-your-key-here`
- [ ] **/system/preflight 不暴露完整 API Key** — 端点只返回 configured/hint 状态，不返回 Key 内容
- [ ] **/settings 返回脱敏 Key** — 确认返回格式为 `sk-a***3f8b`

---

## 二、启动检查（Startup）

- [ ] **Windows start.bat 可运行** — 双击启动，无错误退出
- [ ] **Mac/Linux start.sh 可运行** — 终端运行，无错误退出
- [ ] **docker compose config 通过** — `docker compose config`（或 `docker-compose config`）无警告
- [ ] **.env 不存在时自动复制** — 删除 `.env` 后运行启动脚本，确认自动从 `.env.example` 创建
- [ ] **数据目录自动创建** — 删除 `backend/data/config`、`database`、`uploads` 后启动，确认自动重建
- [ ] **启动后能访问 http://localhost:3000** — 浏览器打开无白屏、无网络错误
- [ ] **启动后能访问 http://localhost:8000/health** — 健康检查返回 200
- [ ] **start.sh 语法无错误** — `bash -n scripts/start.sh` 通过
- [ ] **start.sh 不删除 data/** — 确认脚本中无 `rm -rf data/` 之类命令
- [ ] **start.bat 不删除 data/** — 确认脚本中无 `rmdir /s /q data\` 之类命令

---

## 三、停止与重启检查（Stop & Restart）

- [ ] **stop.sh 可停止服务** — 运行后 `docker compose ps` 无运行中的容器
- [ ] **stop.bat 可停止服务** — 双击运行，服务停止
- [ ] **停止后数据保留** — `docker compose down` 后 `backend/data/` 中的文件完好
- [ ] **restart.bat 可重启服务** — 停止后再启动，服务恢复正常
- [ ] **docker compose down && docker compose up** — 重建后数据不丢失

---

## 四、功能检查（Functional）

在启动并配置 API Key 后验证：

- [ ] **设置页可打开** — http://localhost:3000/settings
- [ ] **系统诊断可用** — 设置页「系统诊断」面板显示各项状态
- [ ] **Help 可打开** — http://localhost:3000/help 内容完整
- [ ] **Setup 向导可打开** — http://localhost:3000/setup
- [ ] **图片上传可用** — 上传一张测试图片，返回成功
- [ ] **分析/批评/迭代可用** — 三个核心任务正常返回结果
- [ ] **案例库可用** — 参考案例列表可打开、可新增
- [ ] **案例库体检可用** — http://localhost:3000/audit
- [ ] **训练评估可用** — http://localhost:3000/assessment
- [ ] **导入导出可用** — 设置页导出 zip → 导入 zip 成功
- [ ] **语义搜索可用** — 案例搜索正常返回结果（如配置了 Embedding）
- [ ] **API 文档可打开** — http://localhost:8000/docs
- [ ] **历史记录详情弹窗正常** — 点击历史记录可打开详情弹窗
- [ ] **判断差异（V1.1 judgment gap）正常** — 自评后差异分析显示正确
- [ ] **middleware 正常** — preflight 诊断端点返回完整 JSON

---

## 五、文档检查（Documentation）

- [ ] **README 第一屏能看懂** — 不熟悉项目的人看第一屏就能理解这是什么、怎么用
- [ ] **README 命令准确** — 所有 bash 命令和路径在 Windows/Mac 上可执行
- [ ] **LOCAL_DEPLOYMENT.md 命令准确** — Windows/Mac/Linux 部署步骤可复现
- [ ] **LOCAL_DEPLOYMENT.md 覆盖率** — 包含 Win/Mac/Linux 三种部署方式
- [ ] **UPGRADE.md 说明升级前备份** — 升级步骤第一项为「导出数据备份」
- [ ] **UPGRADE.md 默认不删除 data/** — 升级步骤不包含删除数据目录的操作
- [ ] **CHANGELOG.md 当前版本正确** — 本次发布版本条目完整
- [ ] **RELEASE_NOTES.md 当前版本正确** — 版本号和日期准确
- [ ] **RELEASE_CHECKLIST.md 当前版本正确** — 即本文档
- [ ] **ROADMAP.md 已更新** — 本次发布版本标记完成
- [ ] **SESSION_HANDOFF.md 已更新** — 反映当前会话状态
- [ ] **CLAUDE.md 版本号正确** — 版本线包含本次发布版本
- [ ] **AGENTS.md 版本号正确** — 项目版本信息一致

---

## 六、后端测试

- [ ] **全部测试通过** — `cd backend && pytest app/tests/ -v`
- [ ] **测试数与文档一致** — 实际 pass 数与 README/AGENTS 中的数字匹配
- [ ] **健康检查版本正确** — `/health` 和 `/system/status` 返回本次发布版本（形如 `vX.Y.Z`）
- [ ] **预检版本正确** — `/system/preflight` 返回本次发布版本
- [ ] **导出包版本正确** — 导出包中 version 字段为本次发布版本
- [ ] **评测台校准** — 发布后 `evals.yml` 自动跑（需仓库 secret `DEEPSEEK_API_KEY`；`--check` 在成对判对率 <0.75 时让该 job 失败）。本地手动：`cd backend && python -m evals.run_eval --repeat 3 --check`。改过 prompt/知识库后必跑；金标准仍为合成脚手架时需先替换真实样本（M-1）

---

## 七、前端检查

- [ ] **CI 绿** — 最新 push 的 GitHub Actions（后端 pytest + 前端 Vitest + build）全部通过
- [ ] **npm run test 通过** — 前端 Vitest 组件测试
- [ ] **npm run build 通过** — 无 TypeScript 错误，无构建警告
- [ ] **所有路由可访问** — /, /settings, /help, /setup, /audit, /assessment 无 404
- [ ] **ChunkLoadError 恢复** — 前端全局 unhandledrejection 监听存在且正常
- [ ] **中文 UI 未损坏** — 全站文案为中文

---

## 八、发布前最终确认

- [ ] `git status` 干净（无未提交的 `.env`、`.db`、real images）
- [ ] `git log --oneline -1` 是本次发布版本的最新提交
- [ ] GitHub Release zip 下载后，按 LOCAL_DEPLOYMENT.md 步骤可以成功部署
