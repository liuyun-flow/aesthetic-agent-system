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
- **本地设置页**（前端 /settings + GET/POST /settings + 测试连接 + 清除密钥）
- **BYOK 配置**（data/config/app_config.json，优先级：config > .env > 默认值）
- **测试全覆盖**（111 passed，含新增 test_settings.py 23 个测试）

## Known Issues
1. GitHub push 需代理（127.0.0.1:7891），代理未运行时 `git push` 失败
2. Git Bash 下 curl 无法连接 localhost（用 127.0.0.1 替代，浏览器正常）
3. Docker 配置文件已创建但未在当前环境测试
4. HTTP_PROXY 环境变量可能导致 Python urllib 本地连接失败（需绕过代理）

## Not Yet Built
- 语义搜索 / 向量检索（V1.8，需案例库 ≥50 个）
- Docker 本地测试（docker compose up --build）
- 多人 SaaS / 登录 / 云存储（V2.0）

## Next Step
V1.8 — 语义搜索 / 向量检索（前置条件：案例库 ≥50 个）

## Local Run
```bash
# 一键启动
bash scripts/start_all.sh --open-browser

# 检查配置
python scripts/check-env.py

# Docker 启动
docker compose up --build
```
