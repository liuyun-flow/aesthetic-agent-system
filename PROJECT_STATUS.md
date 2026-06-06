# Project Status — V1.6

## Current Version
**V1.6** — 本地部署准备 / Docker / 环境配置检查

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
- **Docker 支持**（backend/Dockerfile + frontend/Dockerfile + docker-compose.yml）
- **环境配置检查**（scripts/check-env.py）
- **数据目录整理**（data/database/ + data/uploads/）
- **健康检查端点**（/health /model/status /vision/status）
- **跨平台工程规范**（AI_CONTEXT.md + kill_port.sh + start_all.sh）
- **项目文档完整**（CLAUDE.md, AGENTS.md, ROADMAP.md, SESSION_HANDOFF.md）

## Known Issues
1. GitHub push 需代理（127.0.0.1:7890），代理未运行时 `git push` 失败
2. prompt_generator 测试偶发 502（DeepSeek API 限流）
3. Git Bash 下 curl 无法连接 localhost（用 127.0.0.1 替代，浏览器正常）
4. Docker 配置文件已创建但未在当前环境测试

## Not Yet Built
- 本地设置页 / BYOK 配置 UI（V1.7）
- 语义搜索 / 向量检索（V1.8，需案例库 ≥50 个）
- 多人 SaaS / 登录 / 云存储（V2.0）

## Next Step
V1.7 — 本地设置页 / BYOK 配置

## Local Run
```bash
# 一键启动
bash scripts/start_all.sh --open-browser

# 检查配置
python scripts/check-env.py

# Docker 启动
docker compose up --build
```

## Environment Variables

| Key | Default | Required |
|-----|---------|----------|
| DEEPSEEK_API_KEY | — | Yes |
| DEEPSEEK_BASE_URL | https://api.deepseek.com | No |
| DEEPSEEK_DEFAULT_MODEL | deepseek-v4-flash | No |
| DEEPSEEK_REASONING_MODEL | deepseek-v4-pro | No |
| DATABASE_URL | sqlite:///./data/database/aesthetic.db | No |
| UPLOAD_DIR | ./data/uploads | No |
| VISION_PROVIDER | placeholder | No |
| OPENAI_API_KEY | — | If VISION_PROVIDER=openai |
| OPENAI_VISION_MODEL | gpt-4o-mini | No |
| NEXT_PUBLIC_API_BASE_URL | http://127.0.0.1:8000 | No |

## Pending Git Commits
```
aa1ff1e V1.6: Docker, env config, local deployment preparation
8da77d7 Project context solidification
6605b4c Fix: Reliable service startup via pythonw
69b7d16 Fix: Cross-platform engineering rules
ab08540 V1.5.1: Reference case library with images
```
