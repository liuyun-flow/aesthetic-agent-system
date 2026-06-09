# V2.1.1 发布说明

## 关于本版本

V2.1.1 是 V2.1.0 的稳定性修复版，修正版本号同步和文档准确性问题。

## V2.1.0 回顾

V2.1.0 是 Aesthetic Training Agent System 的「本地正式发布版」，专注于降低安装和首次使用门槛。

## 新增功能

### 一键启动脚本

现在只需一条命令即可启动整个系统：

```bash
# Mac / Linux
bash scripts/start.sh

# Windows（双击运行）
scripts\start.bat
```

脚本会自动：
- 检测 Docker 是否安装
- 检查 .env 配置文件（不存在则从模板创建）
- 创建数据目录
- 启动前后端服务
- 输出访问地址

停止服务：`bash scripts/stop.sh`

### 系统诊断

新增 `GET /system/preflight` 端点，检查：

- 数据库、配置目录、上传目录是否存在且可写
- DeepSeek、Vision、Embedding 是否已配置
- 各组件状态描述（中文）

设置页（`/settings`）新增「系统诊断」面板，一目了然显示所有系统状态，并给出可执行的建议操作。

### 文档完善

新增三份用户文档：
- `CHANGELOG.md` — 完整版本变更记录
- `UPGRADE.md` — 版本升级步骤与回滚方法
- `RELEASE_NOTES.md` — 本文档

README 已重写为面向用户的安装手册。

## 系统要求

- Docker Desktop（推荐）
- 或 Python 3.11+ / Node.js 18+（本地开发）
- DeepSeek API Key（必须）
- OpenAI API Key（可选，用于 Vision 图片识别和语义搜索）

## 快速开始

1. 复制并编辑配置：`cp backend/.env.example backend/.env`
2. 编辑 `.env`，设置 `DEEPSEEK_API_KEY`
3. 运行：`bash scripts/start.sh`
4. 打开：http://127.0.0.1:3000

## 已知限制

- 误判检测基于关键词规则（非 LLM）
- 语义搜索需要 OpenAI API Key
- 导出不含 embeddings（导入后需重建索引）
- 导入为合并模式，不做去重

## 下一步

- V2.1.1：稳定性审查
- V2.2：训练效果图表（折线图、雷达图）
- V3.0：多人模式（远期规划）
