# Paper Notion Agent - 新架构说明

## 概述

Paper Notion Agent 是一个智能论文整理系统，使用 OpenAI Agents SDK 构建，支持多种论文来源（小红书、PDF链接等），自动提取元数据并保存到 Notion 知识库。

## 架构设计

### 多 Agent 协作架构

```
┌─────────────────────────────────────────────────────────────┐
│                      用户输入                                 │
│  "请帮我整理这篇论文: https://www.xiaohongshu.com/xxx"        │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────────────────┐
│              主 Agent (paper_agent)                       │
│  - 解析用户请求（立即执行 vs 定时任务）                     │
│  - 识别链接类型（XHS/PDF/arXiv）                          │
│  - 使用 handoff 转交给 digest_agent                       │
│  - 集成 schedule-task-mcp（定时任务）                     │
│                                                             │
│  工具:                                                      │
│    - parse_user_request                                   │
│    - identify_link_type                                   │
│    - schedule-task-mcp tools (create_task, etc.)          │
│                                                             │
│  Handoffs:                                                 │
│    - transfer_to_digest_agent                             │
└───────────────────────┬───────────────────────────────────┘
                        │ handoff
                        ▼
┌───────────────────────────────────────────────────────────┐
│            Sub-Agent (digest_agent)                       │
│  - 获取论文内容（XHS/PDF）                                  │
│  - 下载并读取 PDF                                          │
│  - 提取元数据（作者、年份、期刊等）                         │
│  - 生成中文论文整理                                         │
│  - 保存到 Notion                                           │
│                                                             │
│  工具:                                                      │
│    - fetch_xiaohongshu_post                               │
│    - extract_paper_title                                  │
│    - download_pdf_from_url                                │
│    - read_local_pdf                                       │
│    - extract_pdf_metadata                                 │
│    - generate_paper_digest                                │
│    - save_digest_to_notion                                │
└───────────────────────────────────────────────────────────┘
```

## 核心文件

### 1. **paper_agents_new.py** - 主 Agent 定义

- 定义 `paper_agent`（主调度 Agent）
- 实现链接识别工具
- 实现请求解析工具
- 配置 handoff 到 digest_agent

### 2. **paper_digest/digest_agent_core.py** - Sub-Agent 定义

- 定义 `digest_agent`（论文整理 Agent）
- 实现所有论文处理工具
- 支持多种输入源（XHS URL、PDF URL、本地 PDF）

### 3. **chat_new.py** - 对话机器人

- 集成主 Agent 和 Sub-Agent
- 支持 MCP Sampling（定时任务自动触发）
- 提供交互式对话界面

### 4. **test_new_architecture.py** - 测试脚本

- 测试链接识别逻辑
- 验证 Agent 结构
- 确保 handoff 机制正确配置

## 功能特性

### 1. 智能链接识别

支持识别以下链接类型：

- **小红书链接**: `xiaohongshu.com/explore/...`
- **PDF 链接**: `*.pdf`, `arxiv.org/pdf/...`
- **arXiv 摘要链接**: `arxiv.org/abs/...` (自动转换为 PDF 链接)
- **其他链接**: 提示用户提供有效链接

### 2. 多 Agent 协作（Handoff）

- **主 Agent** 负责调度和任务管理
- **Digest Agent** 专注于论文处理
- 使用 OpenAI Agents SDK 的 `handoff` 机制无缝转交任务
- 保留对话历史，Sub-Agent 可以访问完整上下文

### 3. 定时任务支持

- 集成 `schedule-task-mcp` 服务
- 支持 cron 表达式定义定时任务
- 支持 MCP Sampling，任务自动触发 Agent 执行
- 示例：`"每天早上8点整理 xxx 链接"`

### 4. 完整论文元数据提取

从 PDF 中提取：
- 作者列表
- 发表年份
- 期刊/会议名称
- 摘要
- 机构信息
- DOI（如果有）
- ArXiv ID（如果有）

### 5. 结构化论文整理

使用模板生成中文论文整理，包含：
- 文章背景与基本观点
- 现有解决方案的思路与问题
- 本文提出的思想与方法
- 方法实现细节
- 方法有效性证明（实验）
- 局限性与未来方向

## 使用方式

### 立即执行任务

```
用户: 请帮我整理这篇论文 https://www.xiaohongshu.com/explore/xxx

主 Agent:
  1. 识别为小红书链接
  2. 转交给 digest_agent

Digest Agent:
  1. 获取小红书内容
  2. 提取论文标题
  3. 搜索并下载 PDF
  4. 提取元数据
  5. 生成中文整理
  6. 保存到 Notion
```

### 定时任务

```
用户: 每天早上8点帮我整理这个链接 https://arxiv.org/abs/xxx

主 Agent:
  1. 识别为定时任务
  2. 使用 schedule-task-mcp 创建任务
  3. 任务会在每天早上8点自动触发 digest_agent
```

### PDF 直链

```
用户: 这是PDF直接链接 https://arxiv.org/pdf/2505.10831.pdf

主 Agent:
  1. 识别为 PDF 链接
  2. 转交给 digest_agent

Digest Agent:
  1. 直接下载 PDF
  2. 读取全文内容
  3. 提取元数据
  4. 生成中文整理
  5. 保存到 Notion
```

## 技术栈

- **OpenAI Agents SDK**: 多 Agent 编排和 handoff
- **MCP (Model Context Protocol)**: 工具集成和 Sampling
- **schedule-task-mcp**: 定时任务管理
- **Notion API**: 知识库存储
- **PyMuPDF (fitz)**: PDF 内容提取
- **httpx**: HTTP 请求
- **GPT-5-mini / GPT-5**: 大语言模型

## 与旧架构对比

| 特性 | 旧架构 | 新架构 |
|------|-------|-------|
| Agent 数量 | 1个（单一 Agent） | 2个（主 + Sub） |
| 职责分离 | ❌ 所有功能耦合 | ✅ 清晰的职责划分 |
| 链接识别 | ⚠️ 手动判断 | ✅ 智能自动识别 |
| Handoff 机制 | ❌ 不支持 | ✅ 完整支持 |
| 定时任务 | ✅ 支持 | ✅ 支持（更好的集成） |
| 代码复用 | ❌ 多个重复文件 | ✅ 单一核心实现 |
| 可维护性 | ⚠️ 中等 | ✅ 高 |

## 文件清理

已删除的冗余文件：
- `paper_digest/digest_agent.py`
- `paper_digest/digest_agent_tavily.py`
- `paper_digest/digest_agent_enhanced.py`
- `paper_digest/digest_agent_simple.py`
- `paper_digest/digest_agent_enhanced_v2.py`

保留的核心文件：
- `paper_digest/digest_agent_core.py` - 唯一的 digest agent 实现
- `paper_digest/process_downloaded_pdf.py` - 独立的 PDF 处理脚本
- `paper_digest/digest_template.md` - 论文整理模板

## 测试

运行测试脚本：

```bash
.venv/bin/python test_new_architecture.py
```

测试内容：
- ✅ 链接识别逻辑
- ✅ Agent 结构验证
- ✅ Handoff 机制配置

## 启动应用

```bash
.venv/bin/python chat_new.py
```

## 下一步

1. ✅ 核心架构已完成
2. ✅ 测试验证通过
3. ⏳ 实际运行测试（需要配置环境变量）
4. ⏳ 生产环境部署

## 注意事项

- 需要配置 `.env` 文件中的环境变量：
  - `OPENAI_API_KEY`
  - `NOTION_TOKEN`
  - `NOTION_DATABASE_ID`
  - `XHS_COOKIES`（用于小红书内容抓取）
- schedule-task-mcp 需要单独安装：`npm install -g schedule-task-mcp`

---

**最后更新**: 2025-10-21
**架构版本**: 2.0
**状态**: ✅ 已完成并测试
