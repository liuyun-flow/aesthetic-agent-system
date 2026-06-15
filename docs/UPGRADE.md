# 升级指南

## 从 V2.4.x 升级到 V2.5.0

V2.5.0 是质量与可靠性版（CI / 缓存 / 遥测 / 测试）。新增 `llm_usage` 表 + `uploaded_images.vision_model` 列，经启动时**自动迁移**（`_migrate_v2_5`）添加，旧数据安全，无需手动处理。

**升级前务必先导出备份**（设置页 → 数据管理 → 导出）。

```bash
git pull origin main
docker compose up --build -d
```

> 可选：发布时校准评测（`evals.yml`）需在 GitHub 仓库 Settings → Secrets 添加 `DEEPSEEK_API_KEY` 才会真正运行。

## 从 V2.2.x 升级到 V2.3.0

V2.3.0 新增一键收入案例库和描述质量优化。训练记录新增 `image_id` 列，通过启动时**自动迁移**添加，旧数据安全，无需手动处理。

**升级前务必先导出备份**（设置页 → 数据管理 → 导出）。

```bash
git pull origin main
docker compose up --build -d
```

## 从 V2.1.3 升级到 V2.2.x

V2.2 / V2.2.1 为体验优化与 Agent 审美内核强化，无数据库变更。

**升级前务必先导出备份。**

```bash
git pull origin main
docker compose up --build -d
```

## 从 V2.1.2 升级到 V2.1.3

V2.1.3 是本地发布包整理版，没有数据库变更。

**升级前务必先导出备份**（设置页 → 数据管理 → 导出）。备份包保存在你的电脑上，不含 API Key。

```bash
git pull origin main
docker compose up --build -d
```

## 从 V2.1.1 升级到 V2.1.2

V2.1.2 是热修复版，修复 Windows start.bat、chunk 缓存崩溃、Help 内容过时。

升级前务必先导出备份。

```bash
git pull origin main
docker compose up --build -d
```

## 从 V2.1.0 升级到 V2.1.1

V2.1.1 是稳定性修复版。升级步骤与 V2.1.0 相同。

```bash
git pull origin main
docker compose up --build -d
```

升级前务必导出备份（设置页 → 数据管理 → 导出）。

## 从 V2.0.x 升级到 V2.1.0

### 步骤 1：备份数据

升级前**务必导出数据备份**：

1. 打开 http://127.0.0.1:3000/settings
2. 在「数据管理」区域点击「导出备份包 (.zip)」
3. 保存 `aesthetic-backup.zip` 到安全位置

> 导出包包含：参考案例、训练记录、提示词历史、上传图片、配置摘要。
> 导出包**不包含** API Key，不会泄露你的 DeepSeek/OpenAI 密钥。

### 步骤 2：保留数据目录

确保 `backend/data/` 目录不被删除。该目录包含：

```
backend/data/
├── config/app_config.json    # 你的 API Key 配置
├── database/aesthetic.db     # 所有训练数据
└── uploads/                  # 上传的图片
```

如果你使用 Docker，这三个目录已通过 `docker-compose.yml` 挂载为卷，**不会因为重建镜像而丢失**。

### 步骤 3：拉取最新代码

```bash
git pull origin main
```

### 步骤 4：重新构建并启动

```bash
# Docker 方式（推荐）
bash scripts/start.sh

# 或手动
docker compose up --build -d
```

首次启动会自动创建缺失的数据目录。

### 步骤 5：验证

1. 打开 http://127.0.0.1:3000
2. 打开设置页 → 系统诊断面板应显示各项状态
3. 导航栏新增「训练评估」（如果从 V1.x 升级）

### 回滚方法

如果升级后遇到问题：

```bash
# 1. 停止服务
docker compose down

# 2. 切回旧版本
git checkout <旧版本 commit>

# 3. 重建
docker compose up --build -d

# 4. 如数据库不兼容，删除后重启（注意：会丢失训练数据！）
# rm backend/data/database/aesthetic.db
```

---

## 从 V1.x 升级到 V2.x

V2.0 新增了训练效果评估系统和案例库质量管理。升级步骤同上，特别注意：

1. V2.x 的导出包版本为 `v2.x`，导入 V2.x 导出的备份包不会有兼容警告
2. 旧 V1.x 的训练数据会自动兼容——缺字段的训练记录会被跳过，不会崩溃
3. 建议升级后重建语义搜索索引：参考案例区域 → 点击「重建索引」

---

## 迁移旧数据库路径

如果你的 `backend/.env` 中 DATABASE_URL 为旧版路径：

```
DATABASE_URL=sqlite:///./aesthetic.db
```

在 Docker 下此路径不被 volume 保护，`docker compose down` 后数据可能丢失。请迁移：

```bash
# 1. 停止服务
bash scripts/stop.sh

# 2. 移动数据库文件
mv backend/aesthetic.db backend/data/database/aesthetic.db

# 3. 修改 backend/.env
# DATABASE_URL=sqlite:///./aesthetic.db          # 旧
DATABASE_URL=sqlite:///./data/database/aesthetic.db  # 新

# 4. 重新启动
bash scripts/start.sh
```

启动脚本会检测旧路径并给出提示。

## 环境要求

- Docker Desktop 最新版
- 或 Python 3.11+ / Node.js 18+（本地开发模式）
