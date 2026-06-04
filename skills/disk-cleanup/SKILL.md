---
name: disk-cleanup
description: 安全清理磁盘空间。分析空间占用、按安全等级分类清理（缓存/临时文件/应用数据）、检测运行中进程锁定的文件、在清理前向用户确认高风险项目。触发场景：用户说"清理磁盘""C盘满了""释放空间""磁盘空间不足""帮我清理电脑"等。
---

# 磁盘清理 Skill

## 核心原则

**安全第一，分类清理。** 不碰用户数据和系统文件，只清理可重建的缓存和临时文件。高风险项目必须先展示分析结果、等待用户确认后再执行。

## 清理流程

### 第一步：分析空间占用

先定位目标磁盘的大户目录，用 `du` 逐层下钻：

```bash
# 顶层分析
du -sh /<target>/Users/<name>/AppData 2>/dev/null
du -sh /<target>/Users/<name>/* 2>/dev/null | sort -rh | head -20
```

然后针对大户目录深入分析，直到定位到具体可清理的缓存/临时目录。

### 第二步：分类与标注

将发现的每一项按安全等级分类：

| 等级 | 标记 | 说明 | 处理方式 |
|------|------|------|---------|
| 🟢 **安全** | 缓存/临时文件，删除后应用会自动重建 | pip cache、浏览器缓存、视频播放器缓存、QQ/微信更新包、日志文件 | 列出后直接清理 |
| 🟡 **需确认** | 可能含用户数据或影响应用功能 | WPS 插件池、QQ 聊天数据、微信插件、Steam 下载缓存 | 展示详情，询问用户 |
| 🔴 **高风险** | 系统文件、用户文档、程序本体 | Windows 目录、Documents、Programs | 绝不触碰 |
| ⚠️ **被锁定** | 文件正被运行中的进程占用 | 微信 mmap、Chrome Cache（浏览器开着时）、WPS addons（WPS 开着时） | 告知用户关闭对应程序后重试 |

### 第三步：执行清理

按安全等级分批清理：

1. 先清理 🟢 安全项目（无需确认）
2. 对 🟡 项目逐一展示分析结果，等用户选择
3. 对 ⚠️ 被锁定的文件，检测并结束对应进程后再清理

**遇到 "Device or resource busy" 错误时**：
- 用 `tasklist` 或 `ps` 确认进程是否还在运行
- Windows: `powershell.exe -Command "Stop-Process -Name <进程名> -Force"`
- 进程结束后重试删除

### 第四步：汇报结果

清理完成后汇报：
- 清理前后磁盘可用空间对比
- 每项释放的具体大小
- 因锁定未清理的项目（如有关闭对应软件后可再清理）

## 常见清理目标参考

以下是实战中常见的大户，优先检查这些位置：

### Windows（C:\Users\<name>\AppData）

| 路径模式 | 典型大小 | 安全等级 | 内容 |
|---------|---------|---------|------|
| `Roaming/Tencent/QQLive` | 1-2 GB | 🟢 | 腾讯视频缓存 |
| `Roaming/Tencent/QQLiveAppStore` | 0.5-1 GB | 🟢 | 视频应用商店缓存 |
| `Roaming/Tencent/QQ/libcef` | 0.5-1 GB | 🟢 | QQ 浏览器引擎 |
| `Roaming/Tencent/QQ/Skins` | 0.2-0.5 GB | 🟢 | QQ 皮肤 |
| `Roaming/Tencent/QQ/Temp` | 0.2-0.5 GB | 🟢 | QQ 临时文件 |
| `Roaming/Tencent/QQ/WebKit` | 10-30 MB | 🟢 | QQ 浏览器缓存 |
| `Roaming/Tencent/xwechat/update` | 0.5-1 GB | 🟢 | 微信安装包 |
| `Roaming/Tencent/xwechat/log` | 1-10 MB | 🟢 | 微信日志 |
| `Roaming/Tencent/QQTempSys` | 20-50 MB | 🟢 | QQ 系统临时文件 |
| `Roaming/Kingsoft/wps/addons/pool` | 1-2 GB | 🟡 | WPS 插件池 |
| `Roaming/Kingsoft/wps/addons/data` | 0.5-1 GB | 🟡 | WPS 插件数据 |
| `Roaming/Tencent/QQ/Misc` | 0.2-0.5 GB | 🟡 | QQ 杂项（含配置） |
| `Roaming/Tencent/xwechat/xplugin` | 0.5-1 GB | 🟡 | 微信小程序插件 |
| `Local/pip` | 0.5-1 GB | 🟢 | pip 下载缓存 |
| `Local/Google/Chrome/User Data/*/Cache` | 0.2-0.5 GB | 🟢 | Chrome 浏览器缓存 |
| `Local/Temp` | 50-200 MB | 🟢 | Windows 临时文件 |

### macOS / Linux

| 路径 | 说明 |
|------|------|
| `~/Library/Caches` | macOS 应用缓存 |
| `~/.cache` | Linux 用户缓存 |
| `~/.npm/_cacache` | npm 缓存 |
| `~/.cargo/registry` | Cargo 注册表缓存 |
| `/tmp` | 系统临时文件 |
| `~/.local/share/Trash` | 回收站 |

## 进程锁定文件处理

删除失败时，不要放弃——先检查是否有进程在占用：

```bash
# Windows: 查看目标进程
tasklist 2>/dev/null | grep -i <关键词>

# 通过 PowerShell 结束进程（比 taskkill 更可靠）
powershell.exe -Command "Stop-Process -Name <进程名> -Force"

# macOS/Linux: 使用 lsof 查看文件占用
lsof | grep <路径>
```

然后再重试删除。PowerShell `Stop-Process` 比 Windows `taskkill` 更可靠——后者在 Git Bash 等环境下容易出现路径编码问题。

## 安全边界

**绝对不删：**
- `C:\Windows`、`/System`、`/boot`
- `Documents`、`Desktop`、`Downloads`（除非用户明确要求清理特定文件）
- `Program Files`、`/Applications`
- 任何 `.sys`、`.dll`、`.so`、`.dylib` 系统库文件
- 注册表文件和用户配置数据库（NTUSER.DAT 等）

**可以清理：**
- 所有 `cache`、`Cache`、`temp`、`Temp`、`tmp` 目录
- 视频/音乐应用的流媒体缓存
- 软件更新安装包（`update`、`updates` 目录）
- 浏览器缓存
- 包管理器缓存（pip、npm、cargo 等）
- 日志文件（`*.log`、`log/`）
