# Paper Agent Scheduler

An autonomous AI agent that fetches research paper information from Xiaohongshu posts, extracts and summarizes content through conversational interaction, and organizes it into a Notion knowledge base.

## Project Status

**Current Phase**: Phase 3 Complete ✅ - MVP Ready!

- ✅ Phase 1: Setup (Project structure, dependencies, configuration)
- ✅ Phase 2: Foundational (Models, utilities, database, agent core)
- ✅ Phase 3: User Story 1 - Manual Post Processing (MVP功能完成！)
- ⏳ Phase 4: User Story 2 - Scheduled Automation
- ⏳ Phase 5: User Story 3 - Multi-turn Conversation Context

## Features

### User Story 1 - Manual Post Processing (P1) 🎯 MVP ✅
- ✅ Fetch Xiaohongshu posts by URL
- ✅ Extract paper metadata (title, authors, summary, tags, PDF links)
- ✅ Present extracted information for user review
- ✅ Save approved content to Notion database
- ✅ Pattern-based extraction with LLM fallback
- ✅ Confidence scoring for extraction quality
- ✅ Duplicate detection via processing records

### User Story 2 - Scheduled Automation (P2)
- Configure recurring schedules via natural language
- Auto-fetch new posts from specified bloggers
- Batch processing with duplicate detection
- Comprehensive error logging and retry policies

### User Story 3 - Multi-turn Conversation (P3)
- Maintain context across multiple turns
- Handle clarifications and refinements
- Natural language interaction
- Implicit action detection

## Technical Stack

- **Runtime**: Python 3.11+
- **AI Framework**: OpenAI Agents SDK
- **LLM**: OpenAI GPT-5-mini (via custom proxy)
- **Storage**: Notion API (paper content)
- **HTTP Client**: httpx
- **Logging**: structlog (structured logging)

## Project Structure

```
spec-paper-notion-agent/
├── .env                    # Configuration (see .env.example)
├── .env.example            # Configuration template
├── requirements.txt        # Python dependencies
├── chat.py                 # Interactive CLI for chat with agent
├── paper_agents.py         # Main agent definition
├── src/
│   ├── models/
│   │   └── post.py         # Xiaohongshu post entity
│   ├── services/           # Core services
│   │   ├── paper_digest.py # Paper digest agent and tools
│   │   ├── xiaohongshu.py  # Xiaohongshu client
│   │   ├── digest_template.md # Paper digest template
│   │   └── notion_markdown_converter.py # Markdown to Notion blocks
│   └── utils/
│       ├── logger.py       # Structured logging
│       └── retry.py        # Retry utilities
├── paper_digest/           # Generated outputs
│   ├── outputs/            # Markdown files
│   └── pdfs/               # Downloaded PDFs
└── requirements.txt        # Dependencies
```

## Quick Start

### 1. Prerequisites

- Python 3.11+
- pip and venv

### 2. Installation

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

```bash
cp .env.example .env
# Edit .env with your credentials:
# - OPENAI_API_KEY
# - OPENAI_BASE_URL
# - XHS_COOKIES
# - NOTION_TOKEN
# - NOTION_DATABASE_ID
```

### 4. Run

```bash
python chat.py
```

## Usage Example

```
You: https://www.xiaohongshu.com/explore/xxxxx

Agent: 🔍 开始获取小红书帖子
       ✅ 小红书帖子获取成功 (17.34s)

       🔎 开始在 arXiv 搜索论文
       ✅ arXiv 搜索成功 (3.45s)

       📥 开始下载 PDF
       ✅ PDF 下载并读取成功 (19.12s)

       📚 开始提取论文元数据（LLM 调用 1/2）
       ✅ 论文元数据提取成功 (46.23s)

       ✍️ 开始生成论文整理（LLM 调用 2/2）
       ✅ 论文整理生成成功 (39.12s)

       💾 开始保存论文整理到 Notion
       ✅ 论文整理已保存到 Notion (8.45s)

Done! Paper saved to Notion.
```

## Recent Improvements

### Workflow Optimization (v0.2)
- **33% reduction in LLM calls** (3 → 2 calls)
- **25-50% faster execution** with merged metadata extraction
- **30% token savings** compared to previous version
- **Complete elapsed time logging** for all operations
- **Cleaner Notion schema** (removed Resources consolidation)

## Development

See documentation in the codebase for implementation details.

## License

See project license.
