# Roadmap

## ✅ V1.5.2–V1.7 (已完成)
- 案例库数据导入/导出（JSON）
- Dockerfile / docker-compose
- .env 配置检查脚本
- 本地设置页 / BYOK 配置（`data/config/app_config.json`）
- DeepSeek / OpenAI Vision 连接测试
- 设置页只返回脱敏后的 key，不把 API Key 存到浏览器 localStorage

## ✅ V1.7.1 — 首次使用向导 / Help
- 首次使用向导（`/setup`）
- 帮助中心（`/help`）
- 工作台配置状态条
- `GET /system/status` 综合状态端点

## ✅ V1.7.2 — 迭代方向选择与提示词
- 结构化迭代方向（11 字段）
- 选择迭代方向后生成对应提示词
- 生成结果保存到对应 iterate 历史记录
- 历史详情展示所有方向、选中方向和对应提示词

## ✅ V1.8 — 数据导入/导出 + 语义搜索
- 数据导出 zip（manifest + cases + sessions + images，不含 API Key）
- 数据导入（zip slip 防护、ID 重映射、合并导入）
- 案例库语义搜索（OpenAI text-embedding-3-small）
- ReferenceCaseEmbedding 模型 + reindex
- 语义搜索 fallback 到普通筛选（不崩溃）
- 前端数据管理 UI + 语义搜索 UI

## ✅ V1.8.1 — 稳定性修复 / 发布前整理
- 版本号统一
- .gitignore 补充 `*.zip`
- 全量回归测试 158 passed
- Docker 路径验证
- 导出包结构验证
- 文档同步

## ✅ V2.1.1 — 本地正式发布版稳定性修复 / 发布候选（当前版本）
- 版本号同步（preflight 使用 app.version）
- 文档准确性修正
- 210 tests passed

## ✅ V2.1.0 — 本地正式发布版 / 安装体验优化
- 一键启动脚本（start.sh / start.bat）
- 停止脚本（stop.sh）
- /system/preflight 系统预检端点
- 设置页系统诊断面板
- CHANGELOG / UPGRADE / RELEASE_NOTES 文档
- 一键启动 + 启动后诊断 + 备份提醒
- 210 tests passed

## ✅ V2.0.1 — 训练评估稳定性与数据校准
- 趋势判断阈值文档化（±3 gap, ±5pp rate）
- 关键词精度优化（去歧义、去冲突）
- 旧数据兼容增强
- 199 tests passed

## ✅ V2.0.0 — 训练效果评估系统
- 训练效果总览（频率、评分、差距趋势）
- 常见误判类型统计（10 种规则化检测）
- 审美能力维度评估（7 维度 0-100 评分）
- 周期复盘报告（7/30 天切换）
- 评估页面（/assessment）含总览卡片 + 误判/维度/复盘 Tab
- 192 测试 passed

## ✅ V1.9.1 — 案例库质量管理稳定版
- aesthetic_level 验证统一（_is_present 替换内联检查）
- _is_present 增强（支持 list/dict 非空判断）
- _tokenize_title None 防护
- audit issue 字段补全（is_training_ready + reason）
- 嵌入重复检测全量匹配（移除 break）
- missing_learning_notes 逻辑修复（AND → OR）
- 前端 null 安全加固（全面 ?? 守卫）
- 前端空状态页面
- 181 测试 passed

## ✅ V1.9.0 — 案例库质量管理
- 案例完整度评分（0-100，13 字段加权动态计算）
- 训练可用状态判定（is_training_ready）
- 案例库体检接口（GET /reference-cases/audit）
- 案例库体检页面（/audit）
- 重复案例检测（标题相似度 + embedding 相似度双层回退）
- 案例列表增强（完整度分数、训练可用标记、缺失字段提示）
- 语义搜索结合训练可用状态排序

## V2.0 — 多人化（远期）
- 用户登录/注册
- 多用户隔离
- 云存储（图片/CDN）
- 付费/订阅
- 部署到云服务

## Future Ideas
- 浏览器扩展（右键分析任意网页设计）
- Figma 插件（直接在 Figma 里分析设计稿）
- 训练课程模板（新手→进阶 30 天训练计划）
- 社区案例分享
