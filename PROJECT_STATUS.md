# Project Status — V1.5.1

## Current Version
**V1.5.1** — 参考案例库图片增强版

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

## Known Issues
1. GitHub push 偶发网络不可达（需重试）
2. Git Bash 下无法直接 curl localhost（用 127.0.0.1 替代）
3. 旧数据库可能有 Unicode 转义字段（前端 formatter 已做兼容解析）
4. prompt_generator 测试偶发 502（DeepSeek API 限流）

## Not Yet Built
- Docker / 部署方案
- 本地设置页 / BYOK 配置 UI
- 语义搜索 / 向量检索（需案例库 ≥50 个）
- 多人 SaaS（登录/权限/云存储）

## Next Step
V1.5.2 — 案例库体验打磨与数据质量检查

## Local Run
```bash
# 一键启动
bash scripts/start_all.sh --open-browser

# 后端：http://127.0.0.1:8000
# 前端：http://127.0.0.1:3000
# API 文档：http://127.0.0.1:8000/docs
```

## Environment Variables
| Key | Default | Required |
|-----|---------|----------|
| DEEPSEEK_API_KEY | — | Yes |
| DEEPSEEK_BASE_URL | https://api.deepseek.com | No |
| DEEPSEEK_DEFAULT_MODEL | deepseek-v4-flash | No |
| DEEPSEEK_REASONING_MODEL | deepseek-v4-pro | No |
| DATABASE_URL | sqlite:///./aesthetic.db | No |
| VISION_PROVIDER | placeholder | No |
| OPENAI_API_KEY | — | If VISION_PROVIDER=openai |
| OPENAI_VISION_MODEL | gpt-4o-mini | No |
| NEXT_PUBLIC_API_BASE_URL | http://127.0.0.1:8000 | No |
