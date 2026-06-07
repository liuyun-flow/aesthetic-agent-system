# Project Status — V1.7

## Current Version
**V1.7** — 本地设置页 / BYOK 配置

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
- **环境配置检查**（scripts/check-env.py）
- **数据目录整理**（data/config/ + data/database/ + data/uploads/）
- **健康检查端点**（/health /model/status /vision/status）
- **跨平台工程规范**（AI_CONTEXT.md + kill_port.sh + start_all.sh）
- **项目文档完整**（CLAUDE.md, AGENTS.md, ROADMAP.md, SESSION_HANDOFF.md）
- **Docker build context 安全**（backend/.dockerignore + frontend/.dockerignore）
- **Placeholder key 统一检测**（replace-me / your_*_api_key_here / replace-with-your-key 共用）
- **Vision 错误不泄露原始异常**（固定中文错误消息）
- **前端 i18n 全覆盖**（错误 fallback 全部走 i18n 键）
- **测试全面离线**（MockReferenceComparatorAgent / MockPromptGeneratorAgent / MockWeeklyReviewAgent）
- **本地设置页**（前端 /settings + GET/POST /settings + 测试连接 + 清除密钥）
- **BYOK 配置存储**（data/config/app_config.json，优先级：config > .env > 默认值）
- **脱敏 API Key 展示**（sk-a***3f8b 格式）
- **DeepSeek / OpenAI Vision 连接测试**（POST /settings/test-deepseek, /settings/test-vision）
- **配置原子写入**（temp file + rename，Windows fallback 直接写）
- **测试全覆盖**（111 passed，含新增 test_settings.py 23 个测试）

## Known Issues
1. GitHub push 需代理（127.0.0.1:7891），代理未运行时 `git push` 失败
2. Git Bash 下 curl 无法连接 127.0.0.1（用浏览器或用 Python urllib + ProxyHandler({}) 替代）
3. Docker 配置文件已创建但未在当前环境测试（Docker 不在 PATH）
4. HTTP_PROXY 环境变量可能导致 Python urllib 本地连接失败（绕过：ProxyHandler({})）
5. test_api.py 中 2 个 env fallback 测试依赖 monkeypatch（与 load_dotenv 交互不稳定）；核心功能被 TestDeepSeekClient 覆盖
6. 前端 `npm run build` 未在本次验证（需要完整 Node PATH）
7. `set_config` 故意跳过空字符串防止误清 key — 如需清值需用 `write_config`

## Not Yet Built
- 语义搜索 / 向量检索（V1.8，前置条件：案例库 ≥50 个）
- Docker 本地实测（docker compose up --build）
- 前端 build 验证（npm run build）
- 多人 SaaS / 登录 / 云存储（V2.0）

## Next Step
V1.8 — 语义搜索 / 向量检索（前置条件：案例库 ≥50 个）

## Files Modified This Version (V1.7)

### New Files (10)
| File | Purpose |
|------|---------|
| `backend/app/settings/__init__.py` | Settings 包初始化 |
| `backend/app/settings/config_store.py` | 配置持久化核心（读写/缓存/脱敏/优先级） |
| `backend/app/settings/schemas.py` | Settings API Pydantic 模型 |
| `backend/app/settings/routes.py` | 5 个设置 API 端点 |
| `backend/app/tests/test_settings.py` | 23 个设置模块测试 |
| `backend/data/config/.gitkeep` | 配置目录占位 |
| `backend/.dockerignore` | Docker build context 安全 |
| `frontend/.dockerignore` | Docker build context 安全 |
| `frontend/src/app/settings/page.tsx` | 前端设置页 |

### Modified Files (20)
| File | Change |
|------|--------|
| `.env.example` | DATABASE_URL + UPLOAD_DIR 同步到 data/ 布局 |
| `.gitignore` | data/config/* + .dockerignore 规则 |
| `README.md` | V1.7 — 版本号、功能表、API 表、BYOK 说明（中英文） |
| `PROJECT_STATUS.md` | 版本号 + known issues + 文件清单 |
| `ROADMAP.md` | （未修改） |
| `docker-compose.yml` | config volume + healthcheck + depends_on condition |
| `docs/SESSION_HANDOFF.md` | 会话交接记录 |
| `backend/app/main.py` | include_router + get_value wiring + version 1.6.0 |
| `backend/app/llm/deepseek_client.py` | os.getenv → get_value config fallback |
| `backend/app/vision/openai_adapter.py` | placeholder_keys 扩展 |
| `backend/app/tests/test_api.py` | 3 个 Mock agent + 3 个 config_store 兼容修复 |
| `scripts/check-env.py` | placeholder_keys 扩展 |
| `scripts/start_all.sh` | PYTHON_HOME / NODE_HOME 可配置化 |
| `frontend/Dockerfile` | CMD dev → start（生产模式） |
| `frontend/src/i18n/zh.ts` | settings namespace（25+ 键） |
| `frontend/src/i18n/en.ts` | settings namespace（25+ 键） |
| `frontend/src/app/layout.tsx` | Header 导航（工作台 / 设置） |
| `frontend/src/app/page.tsx` | English fallback → i18n |
| `frontend/src/components/TaskForm.tsx` | English fallback → i18n |
| `frontend/src/components/SessionList.tsx` | English fallback → i18n |
| `frontend/src/components/ReferencePanel.tsx` | English fallback → i18n |

## Local Run
```bash
# 一键启动
bash scripts/start_all.sh --open-browser

# 检查配置
python scripts/check-env.py

# Docker 启动
docker compose up --build
```
