# Paper Digest 使用指南

**最后更新**: 2025-10-20 16:00

---

## 📚 快速开始

### 1. 处理单个 PDF（推荐）

```bash
cd /Users/liao1fan/workspace/personal/paper_notion_agent/spec-paper-notion-agent
.venv/bin/python paper_digest/process_downloaded_pdf.py
```

**功能**：
- ✅ 分批读取 PDF（每次10页，直到读完）
- ✅ 提取完整元数据（作者、日期、期刊/会议）
- ✅ 使用 gpt-5-mini 生成详细论文整理
- ✅ 保存到 Notion（包括所有元数据）
- ✅ 本地保存 Markdown 文件

**输出示例**：
```
  ✅ 元数据提取完成
    - 作者: ['Omar Shaikh', 'Shardul Sapkota', 'Shan Rizvi']
    - 发表日期: 2025-09-21
    - 期刊/会议: The 38th Annual ACM Symposium on User Interface Software and Technology (UIST '25)

  ✅ 已保存到 Notion: https://notion.so/292246d3ac6281249ac1d89583e82b8a
    - 作者: Omar Shaikh, Shardul Sapkota, Shan Rizvi...
    - 发表日期: 2025-09-21
    - 期刊/会议: The 38th Annual ACM Symposium on User Interface Software and Technology (UIST '25)
```

---

## 🔍 验证工具

### 检查数据库 Schema

```bash
.venv/bin/python check_notion_schema.py
```

**输出**：
```
数据库字段列表：
  - Name: title
  - Summary: rich_text
  - Tags: multi_select
  - Source URL: url
  - Authors: rich_text ✅
  - PDF Link: url
  - Publication Date: date ✅
  - Venue: rich_text ✅
  ...
```

### 验证最新保存的元数据

```bash
.venv/bin/python verify_notion_metadata.py
```

**输出**：
```
📄 最新的页面信息：
标题: Creating General User Models from Computer Use
作者: Omar Shaikh, Shardul Sapkota, Shan Rizvi, ...
发表日期: 2025-09-21
期刊/会议: The 38th Annual ACM Symposium on User Interface Software and Technology (UIST '25)
PDF链接: https://arxiv.org/pdf/2505.10831

✅ 验证完成
```

---

## 📋 配置要求

### 环境变量 (.env)

```bash
# OpenAI
OPENAI_API_KEY=your_key
OPENAI_BASE_URL=your_base_url

# Notion
NOTION_TOKEN=your_token
NOTION_DATABASE_ID=your_database_id

# 小红书（可选）
XHS_COOKIES=your_cookies

# 代理（可选）
http_proxy=http://127.0.0.1:7891
https_proxy=http://127.0.0.1:7891
```

### Python 依赖

```bash
pip install openai python-dotenv httpx notion-client PyMuPDF
```

---

## 📊 Notion 数据库 Schema

### 必需字段

| 字段名 | 类型 | 用途 |
|--------|------|------|
| Name | title | 论文标题 |
| Summary | rich_text | 摘要 |
| Tags | multi_select | 标签 |
| Source URL | url | 来源链接 |
| **Authors** | rich_text | **作者列表** |
| **Publication Date** | date | **发表日期** |
| **Venue** | rich_text | **期刊/会议** |
| PDF Link | url | PDF 链接 |

### 可选字段

| 字段名 | 类型 | 用途 |
|--------|------|------|
| ArXiv ID | rich_text | ArXiv 编号 |
| Processed Date | date | 处理时间 |
| Blogger | rich_text | 分享者 |
| Confidence | number | 置信度 |
| Notes | rich_text | 备注 |

---

## 🔧 元数据处理

### 提取过程

1. **读取 PDF**：分批读取（每次10页），直到读完整个 PDF
2. **提取元数据**：使用 gpt-4o-mini 分析 PDF 内容，提取：
   - 作者列表（完整）
   - 发表日期（尽量具体到 YYYY-MM-DD）
   - 期刊/会议名称（完整）
   - 摘要

### 日期格式支持

输入格式 → 保存格式：
- `2025` → `2025-01-01`
- `2025-09` → `2025-09-01`
- `2025-09-21` → `2025-09-21`

### 作者列表处理

- 从 PDF 提取：`["Omar Shaikh", "Shardul Sapkota", ...]`
- 保存到 Notion：`"Omar Shaikh, Shardul Sapkota, ..."`

---

## 📁 文件结构

```
paper_digest/
├── process_downloaded_pdf.py    # 主程序（推荐使用）✅
├── digest_template.md           # 论文整理模板
├── pdfs/                        # PDF 存放目录
│   └── Creating General...pdf
├── outputs/                     # Markdown 输出目录
│   └── Creating General...md
├── STATUS_REPORT.md             # 项目状态报告
├── METADATA_ALIGNMENT_COMPLETE.md  # 元数据对齐完成报告
└── USAGE_GUIDE.md               # 本文档
```

---

## ✅ 功能完成度

| 功能 | 状态 | 说明 |
|------|------|------|
| 找到 PDF 链接 | ✅ | 支持 |
| 读取 PDF 全文 | ✅ | 分批10页读取 |
| 提取作者 | ✅ | 完整列表 |
| 提取日期 | ✅ | 精确到天（YYYY-MM-DD） |
| 提取期刊/会议 | ✅ | 完整名称 |
| 生成详细整理 | ✅ | 使用 gpt-5-mini |
| 保存到 Notion | ✅ | 包括所有元数据 |
| 本地保存 | ✅ | Markdown 格式 |
| 元数据对齐 | ✅ | 所有字段正确保存 |

---

## 🎯 最佳实践

### 1. 处理流程

```bash
# 1. 准备 PDF
# 将 PDF 放到 paper_digest/pdfs/ 目录

# 2. 运行处理脚本
.venv/bin/python paper_digest/process_downloaded_pdf.py

# 3. 验证结果
.venv/bin/python verify_notion_metadata.py

# 4. 检查 Notion 页面
# 访问输出的 Notion 链接
```

### 2. 验证元数据

确保以下字段正确填充：
- ✅ Authors（完整作者列表）
- ✅ Publication Date（YYYY-MM-DD 格式）
- ✅ Venue（期刊/会议完整名称）
- ✅ PDF Link（可访问的 PDF 链接）

### 3. 故障排查

#### PDF 读取失败
```bash
# 检查 PDF 是否在正确位置
ls paper_digest/pdfs/

# 检查 PDF 是否损坏
.venv/bin/python -c "import fitz; doc = fitz.open('paper_digest/pdfs/your.pdf'); print(doc.page_count)"
```

#### 元数据提取不准确
- 检查 PDF 是否是扫描版（需要 OCR）
- 增加读取的页数（修改 `PAGES_PER_BATCH`）
- 检查 OpenAI API key 是否有效

#### Notion 保存失败
```bash
# 验证 Notion 连接
.venv/bin/python check_notion_schema.py

# 检查必需字段是否存在
# - Name (title)
# - Authors (rich_text)
# - Publication Date (date)
# - Venue (rich_text)
```

---

## 📞 相关文档

- **项目状态报告**: `STATUS_REPORT.md`
- **元数据对齐报告**: `METADATA_ALIGNMENT_COMPLETE.md`
- **Tavily 测试报告**: `TAVILY_TEST_RESULTS.md`
- **完整总结**: `FINAL_SUMMARY.md`

---

## 🎓 技术栈

- **LLM**:
  - gpt-5-mini: 生成论文整理（大上下文窗口）
  - gpt-4o-mini: 提取元数据（JSON 输出）
- **PDF 处理**: PyMuPDF (fitz)
- **Notion API**: notion-client (AsyncClient)
- **HTTP Client**: httpx（支持代理）

---

## 🚀 下一步

### 可选优化
1. **批量处理**: 支持多个 PDF 一次性处理
2. **进度显示**: 添加进度条
3. **错误重试**: 自动重试失败的步骤
4. **OCR 支持**: 处理扫描版 PDF

### 集成建议
1. 与主流程 `chat.py` 集成
2. 添加 Web UI
3. 支持定时任务

---

**文档版本**: v1.0
**最后更新**: 2025-10-20 16:00
**状态**: ✅ 已完成并可用
