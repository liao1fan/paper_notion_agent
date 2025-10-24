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
- **LLM**: OpenAI GPT-4o-mini (via custom proxy)
- **Storage**: SQLite (local state), Notion API (paper content)
- **Scheduling**: APScheduler
- **HTTP Client**: httpx
- **Data Validation**: Pydantic v2
- **Logging**: structlog (JSON format)

## Project Structure

```
spec-paper-notion-agent/
├── .env                    # Configuration (see .env.example)
├── .env.example            # Configuration template
├── requirements.txt        # Python dependencies
├── src/
│   ├── main.py            # Application entry point
│   ├── agent/             # Agent core and tools
│   │   ├── core.py        # Agent initialization
│   │   ├── tools.py       # Agent tool definitions
│   │   └── callbacks.py   # Scheduled execution callbacks
│   ├── models/            # Data models (Pydantic)
│   │   ├── config.py      # Environment configuration
│   │   ├── post.py        # Xiaohongshu post entity
│   │   ├── extraction.py  # Paper metadata entity
│   │   ├── task.py        # Scheduled task entity
│   │   ├── record.py      # Processing record entity
│   │   ├── notion_entry.py # Notion database mapping
│   │   └── context.py     # Conversation context
│   ├── services/          # External integrations
│   │   ├── xiaohongshu.py # Post fetching (Phase 3)
│   │   ├── notion.py      # Notion API client (Phase 3)
│   │   ├── processor.py   # Content extraction (Phase 3)
│   │   └── scheduler.py   # Task scheduling (Phase 4)
│   ├── storage/           # Database operations
│   │   ├── database.py    # SQLite operations
│   │   └── migrations/    # Schema migrations
│   └── utils/             # Utilities
│       ├── logger.py      # Structured logging
│       ├── retry.py       # Exponential backoff
│       └── validators.py  # Path and data validation
├── data/                  # SQLite databases (gitignored)
├── logs/                  # Execution logs (gitignored)
└── specs/                 # Feature specifications
    └── 001-paper-agent-scheduler/
        ├── spec.md        # Feature specification
        ├── plan.md        # Implementation plan
        ├── tasks.md       # Task breakdown (80 tasks)
        ├── data-model.md  # Entity definitions
        └── contracts/     # API contracts
```

## Setup

### 1. Prerequisites

- Python 3.11 or higher
- pip and venv

### 2. Installation

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Required environment variables:
- `OPENAI_BASE_URL`: OpenAI API endpoint
- `OPENAI_API_KEY`: OpenAI API key
- `XHS_COOKIES`: Xiaohongshu browser session cookies
- `NOTION_TOKEN`: Notion integration secret
- `NOTION_DATABASE_ID`: Target Notion database ID

### 4. Run

```bash
# Activate virtual environment (if not already activated)
source .venv/bin/activate

# Run the application
python -m src.main
```

## 使用示例

### 基本对话流程

```
您: https://www.xiaohongshu.com/explore/xxxxx

助手: 我来帮您获取这个帖子的内容...
[Agent 自动调用 fetch_xiaohongshu_post 工具]

助手: 帖子内容获取成功！现在我来提取论文信息...
[Agent 自动调用 extract_paper_info 工具]

助手: 论文信息提取完成！以下是提取的信息：

标题: Attention Is All You Need
作者: Ashish Vaswani, Noam Shazeer, Niki Parmar
摘要: We propose a new architecture...
标签: transformer, attention, nlp
置信度: 0.95

请确认信息是否正确？如果正确，我将保存到 Notion。

您: 确认

助手: 好的，我现在保存到 Notion...
[Agent 自动调用 save_to_notion 工具]

助手: ✓ 论文《Attention Is All You Need》已成功保存到 Notion 知识库！
Notion 页面链接: https://notion.so/xxxxx
```

### 可用命令

- 发送小红书帖子 URL 开始处理
- `help` - 显示帮助信息
- `exit` 或 `quit` - 退出程序

## Development Status

### Completed (Phase 3 - MVP完成！) ✅

✅ **Setup & Configuration**
- Project directory structure
- Environment configuration with validation
- Dependency management
- Git repository initialized

✅ **Data Models** (7 entities with Pydantic validation)
- `AppConfig`: Environment variable loading with validation
- `Post`: Xiaohongshu post representation
- `PaperExtraction`: Extracted paper metadata
- `ScheduledTask`: Recurring automation jobs
- `ProcessingRecord`: Duplicate detection
- `NotionEntry`: Notion database mapping
- `ConversationContext`: Multi-turn state management

✅ **Utilities**
- Structured logging (JSON format, file rotation ready)
- Exponential backoff retry decorator
- Path validation for directory confinement
- URL and data validators

✅ **Storage Layer**
- SQLite database initialization
- Schema for processing_records and scheduled_tasks
- CRUD operations with async support
- Migration framework ready

✅ **Agent Core**
- OpenAI client configuration with custom base URL
- Agent initialization with instructions
- AppContext for shared resources
- Placeholder for tools and callbacks

✅ **Testing**
- Environment validation working
- Database initialization verified
- Agent creation successful
- Structured logging functional

✅ **Xiaohongshu Client** (T021-T025)
- HTTP client with cookie-based authentication
- Rate limiting (10 req/min configurable)
- HTML parsing and JSON extraction from `window.__INITIAL_STATE__`
- Comprehensive error handling (AuthenticationError, PostNotFoundError, RateLimitError, FetchError)
- Cookie validation method

✅ **Notion Client** (T026-T029)
- Async Notion API wrapper with notion-client
- Page creation with exponential backoff retry
- Connection validation and schema validation
- Rate limit compliance with semaphore-controlled concurrency
- Batch creation support

✅ **Paper Processor** (T030-T034)
- Pattern-based extraction using regex patterns
- LLM fallback extraction with GPT-4o-mini
- Confidence scoring algorithm
- Hybrid extraction merging pattern and LLM results
- Processing record tracking in SQLite

✅ **Agent Tools** (T035-T037)
- `fetch_xiaohongshu_post` - 获取小红书帖子内容
- `extract_paper_info` - 提取论文信息（支持 LLM）
- `save_to_notion` - 保存到 Notion 知识库
- All tools with Chinese docstrings and user-friendly error messages

✅ **Conversation Loop** (T038-T040)
- Runner initialization with OpenAI client
- Interactive console interface with welcome message
- User input/output handling
- Context management across conversation turns
- Error handling and recovery
- Help and exit commands

### Next Steps (Phase 4 & 5)

**Phase 4: Scheduled Automation (P2)**
- APScheduler integration for recurring tasks
- Natural language to cron expression parsing
- Batch processing with duplicate detection
- Task management (create, list, update, delete)
- Scheduled execution callbacks

**Phase 5: Multi-turn Conversation Context (P3)**
- Advanced context retention across multiple turns
- Implicit action detection
- Conversation history replay
- Refinement and clarification handling

## Architecture Principles

From [constitution.md](.specify/memory/constitution.md):

1. **Agent-First Architecture**: OpenAI Agents SDK as core runtime
2. **Scheduled Automation** (NON-NEGOTIABLE): All automation via APScheduler
3. **Directory Confinement**: All operations within project directory
4. **Notion as Single Source of Truth**: No separate database for paper content
5. **Observability & Debugging**: Structured logging for all executions

## License

See project license.

## Documentation

- **Specification**: [specs/001-paper-agent-scheduler/spec.md](specs/001-paper-agent-scheduler/spec.md)
- **Implementation Plan**: [specs/001-paper-agent-scheduler/plan.md](specs/001-paper-agent-scheduler/plan.md)
- **Task Breakdown**: [specs/001-paper-agent-scheduler/tasks.md](specs/001-paper-agent-scheduler/tasks.md)
- **Data Model**: [specs/001-paper-agent-scheduler/data-model.md](specs/001-paper-agent-scheduler/data-model.md)
- **Constitution**: [.specify/memory/constitution.md](.specify/memory/constitution.md)
