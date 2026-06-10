# 本地部署指南 / Local Deployment Guide

**V2.1.3** — Aesthetic Training Agent System

---

## 这是什么 / What This Is

Aesthetic Training Agent System 是一个**本地部署工具**（Local Release），不是 SaaS。

- ✅ 运行在你自己的电脑上
- ✅ 数据存储在你自己的硬盘上
- ✅ 你需要自己的 API Key
- ❌ 没有云端服务
- ❌ 没有登录系统
- ❌ 没有公开网页版

---

## 环境要求 / Requirements

| 项目 | 要求 |
|------|------|
| **操作系统** | Windows 10+ / macOS 12+ / Linux (Docker) |
| **Docker** | Docker Desktop 最新版。**必须安装。** |
| **DeepSeek API Key** | **必需。** [获取地址](https://platform.deepseek.com/api_keys) |
| **OpenAI API Key** | 可选但推荐。用于 Vision（图片识别）和 Embedding（语义搜索） |
| **浏览器** | Chrome / Firefox / Edge 最新版 |

**你不需要安装：** Python、Node.js、SQLite — Docker 镜像内置一切。

---

## Windows 部署

### 1. 安装 Docker Desktop

从 [docker.com](https://www.docker.com/products/docker-desktop/) 下载安装 Docker Desktop。

安装完成后：
- 打开 Docker Desktop
- 等待左下角状态变为绿色 "Engine running"
- 如果提示需要 WSL2，按提示安装即可

### 2. 下载项目

从 GitHub Releases 下载最新版 zip 包（`aesthetic-agent-system-v2.1.3.zip`），解压到你想要的位置。

### 3. 启动

**双击 `scripts\start.bat`**

脚本会自动：
- 检测 Docker 是否在运行
- 检测 `docker compose` 命令
- 如果 `.env` 不存在，从 `.env.example` 复制并提示你编辑 API Key
- 创建数据目录
- 构建并启动前后端服务

### 4. 打开浏览器

访问 **http://localhost:3000**

### 5. 配置 API Key

1. 点击导航栏「设置」
2. 在「DeepSeek 配置」区域填入你的 API Key
3. 点击「测试连接」确认可用
4. （推荐）在「Vision 配置」区域选择 `openai` 并填入 OpenAI API Key
5. 打开「系统诊断」面板确认各项状态正常

### 6. 开始训练

访问 http://localhost:3000 ，上传一张设计图或粘贴一段设计描述，开始你的第一次审美训练。

---

## Windows 常见问题

### Docker 没安装怎么办？

从 https://www.docker.com/products/docker-desktop/ 下载安装。Windows 10 需要启用 Hyper-V 或安装 WSL2（安装程序会引导你完成）。

### Docker Desktop 没启动怎么办？

打开 Docker Desktop 应用，等待右下角状态变为 "Engine running" 后再双击 `start.bat`。

### start.bat 双击没反应？

1. 右键点击 `start.bat` → 以管理员身份运行
2. 检查 Docker Desktop 是否正在运行
3. 打开终端（cmd），cd 到项目目录，手动运行 `scripts\start.bat` 查看错误信息

### 端口被占用怎么办？

默认使用端口 8000（后端）和 3000（前端）。如果被占用：

```bash
# 查看是谁占用了端口
netstat -ano | findstr :8000
netstat -ano | findstr :3000

# 关闭占用进程（或修改 docker-compose.yml 改用其他端口）
```

### .env 不存在怎么办？

`start.bat` 会自动从 `.env.example` 复制一份。你只需在复制后编辑 `backend\.env`，填入 `DEEPSEEK_API_KEY`。

### start.bat 一闪而过怎么办？

这说明脚本遇到错误。打开终端（cmd），cd 到项目目录，手动运行 `scripts\start.bat`，这样你可以看到错误信息。

### API Key 未配置怎么办？

- 设置页 → 填入 Key → 测试连接
- 或者编辑 `backend\.env` 文件，设置 `DEEPSEEK_API_KEY=你的key`
- 已在运行的服务不需要重启——设置页的修改即时生效

### 如何停止服务？

- 双击 `scripts\stop.bat`
- 或在终端运行：`docker compose down`
- 数据保留在 `backend\data\` 目录中，不会丢失

### 如何重启服务？

- 双击 `scripts\restart.bat`
- 或先运行 `stop.bat` 再运行 `start.bat`

### 如何备份数据？

1. 打开 http://localhost:3000/settings
2. 数据管理区域 → 导出备份包 (.zip)
3. 保存到安全位置

备份包包含：参考案例、训练记录、提示词历史、上传图片。**不包含 API Key**。

### 如何升级？

参见 [升级指南](UPGRADE.md)。升级前务必导出备份。

### 如何卸载？

1. 如果数据还想保留：先导出备份
2. `docker compose down` 停止服务
3. 删除整个项目目录
4. 删除 Docker 镜像（可选）：`docker rmi aesthetic-agent-system-backend aesthetic-agent-system-frontend`

**注意：** 删除项目目录会同时删除 `backend/data/` 里的所有数据（包括训练记录和上传图片）。卸载前请确认已备份。

### 白屏/Ctrl+F5 问题？

如果前端显示空白页或加载失败：

1. 按 `Ctrl+F5` 强制刷新
2. 如果仍然白屏：清除浏览器缓存
3. 如果问题持续：`docker compose down && docker compose up --build -d`
4. 这是 chunk 缓存失效导致的问题——V2.1.2 已加入自动恢复

---

## Mac 部署

### 1. 安装 Docker Desktop for Mac

从 [docker.com](https://www.docker.com/products/docker-desktop/) 下载安装。

- **Apple Silicon (M1/M2/M3/M4)：** Docker Desktop 原生支持，无需额外配置
- **Intel Mac：** 同样支持

> ⚠️ 本项目在 Apple Silicon Mac 上**理论上**通过 Docker 支持。但建议在真实 Mac 上做一次完整测试确认。

### 2. 下载项目

从 GitHub Releases 下载最新版 zip，解压。

### 3. 启动

打开终端（Terminal），进入项目目录：

```bash
cd ~/Downloads/aesthetic-agent-system  # 或你的解压位置

# 如果 start.sh 没有执行权限
chmod +x scripts/start.sh

# 启动
./scripts/start.sh
```

### 4. 后续步骤

与 Windows 相同：打开 http://localhost:3000 → 设置 → 配置 API Key → 系统诊断 → 开始训练。

---

## Mac 常见问题

### 如何停止服务？

```bash
bash scripts/stop.sh
# 或
docker compose down
```

### 端口冲突？

```bash
# 查看占用端口的进程
lsof -i :8000
lsof -i :3000
# kill 对应进程
```

### "permission denied" 运行 start.sh？

```bash
chmod +x scripts/start.sh
chmod +x scripts/stop.sh
```

### Docker Desktop 启动很慢？

首次启动 Docker Desktop 可能需要 1-2 分钟。等待菜单栏图标停止动画后再运行 `start.sh`。

### 如何确认数据没有被删除？

`docker compose down` 只停止容器，不删除 volume 数据。你的所有训练数据、上传图片、配置都保留在 `backend/data/` 目录。

---

## Linux 部署

Linux 用户通常对 Docker 比较熟悉。简要步骤：

```bash
# 1. 安装 Docker 和 docker compose plugin
# 参考: https://docs.docker.com/engine/install/

# 2. 下载并解压项目

# 3. 启动
chmod +x scripts/start.sh
./scripts/start.sh

# 4. 访问 http://localhost:3000
```

### Linux 注意事项

- 确保当前用户在 `docker` 组中（否则需要 `sudo`）
- 如果使用 `sudo docker compose`，脚本中的 compose 检测可能需要调整
- 推荐安装 `docker compose` 插件（`docker compose` 命令格式），而非旧版 `docker-compose`

---

## API Key 配置说明

### 配置方式

有两种方式配置 API Key，任选其一：

**方式一：设置页（推荐）**

打开 http://localhost:3000/settings ，在页面中配置。修改即时生效，不需要重启。

**方式二：.env 文件**

编辑 `backend/.env`：

```env
DEEPSEEK_API_KEY=sk-your-key-here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_DEFAULT_MODEL=deepseek-v4-flash
DEEPSEEK_REASONING_MODEL=deepseek-v4-pro

VISION_PROVIDER=openai
OPENAI_API_KEY=sk-your-openai-key-here
OPENAI_VISION_MODEL=gpt-4o-mini
```

### 配置优先级

`data/config/app_config.json`（设置页配置）> `.env` 环境变量 > 默认值

### 安全说明

- API Key 保存在 `backend/data/config/app_config.json`（服务器本地）
- 前端**永远**不会收到完整 Key（接口返回脱敏版本如 `sk-a***3f8b`）
- 导出备份**不包含** API Key
- Key 不会打印到日志
- `.env` 和 `app_config.json` 已加入 `.gitignore`

---

## 数据目录说明

```
backend/data/
├── config/
│   └── app_config.json     # API Key 配置（不进入备份包）
├── database/
│   └── aesthetic.db        # SQLite 数据库（所有训练数据）
└── uploads/                # 上传的图片
```

Docker 通过 `docker-compose.yml` 的 volumes 将这三个目录挂载到容器中，**docker compose down 不会丢失数据**。

### 备份建议

- 定期导出备份（设置页 → 数据管理 → 导出）
- 备份 `.zip` 文件保存到其他位置（U 盘、云盘等）
- 升级前务必先导出备份
- 备份包不包含 API Key，导入后需要重新配置

---

## 端口说明

| 端口 | 服务 | 说明 |
|------|------|------|
| 3000 | 前端 (Next.js) | 浏览器访问地址 |
| 8000 | 后端 (FastAPI) | API 接口，前端内部调用 |

如果需要修改端口：编辑 `docker-compose.yml`，修改 `ports` 映射。

---

## 从源码运行（不使用 Docker）

如果你不想用 Docker：

### 后端

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env，设置 DEEPSEEK_API_KEY
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 前端

```bash
cd frontend
npm install
npm run dev                      # http://127.0.0.1:3000
```

需要：Python 3.11+ / Node.js 18+

---

## 获取帮助

- 应用内帮助中心：http://localhost:3000/help
- 首次使用向导：http://localhost:3000/setup
- 系统诊断：http://localhost:3000/settings → 系统诊断面板
