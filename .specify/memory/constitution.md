<!--
============================================================================
SYNC IMPACT REPORT
============================================================================
Version Change: [TEMPLATE] → 1.0.0
Modified Principles: Initial constitution creation
Added Sections:
  - Core Principles (5 principles defined)
  - Development Constraints
  - Workflow & Quality Gates
  - Governance

Templates Status:
  ✅ plan-template.md - Reviewed, no updates needed (Constitution Check section already flexible)
  ✅ spec-template.md - Reviewed, aligned with user story focus
  ✅ tasks-template.md - Reviewed, aligned with test-optional and parallel execution principles
  ✅ No command files found in .specify/commands/

Follow-up TODOs: None - all placeholders filled
============================================================================
-->

# Paper Notion Agent Constitution

## Core Principles

### I. Agent-First Architecture

The system is built around an autonomous agent that orchestrates all workflows. The agent must:
- Use OpenAI Agents SDK as the core runtime
- Accept sampling_callback parameter for scheduled task execution
- Integrate with MCP servers (schedule-task-mcp, Notion MCP, context MCP) via standardized interfaces
- Operate independently once scheduled, requiring no human intervention per execution
- Maintain clear separation between agent logic, data fetching, and content organization

**Rationale**: Agent autonomy ensures reliable scheduled execution and reduces operational overhead.

### II. Scheduled Automation (NON-NEGOTIABLE)

All paper processing workflows MUST be triggered via schedule-task-mcp's scheduling mechanism. Manual execution is for development/testing only.
- Schedule definitions MUST be configurable (e.g., daily, weekly)
- Agent MUST use sampling_callback to enable scheduled invocation
- Failed executions MUST be logged and retried according to configurable policy
- Schedule changes MUST NOT require code changes (configuration-driven)

**Rationale**: The core value proposition is automated, hands-off paper processing.

### III. Directory Confinement

All development, testing, and execution MUST occur within `/Users/liao1fan/workspace/personal/paper_notion_agent/spec-paper-notion-agent`.
- Code MUST NOT access parent directories or sibling directories outside this boundary
- File paths MUST be validated to prevent directory traversal
- Dependencies MUST be installed in local `.venv` within the project directory

**Rationale**: Prevents unintended side effects and maintains project isolation.

### IV. Notion as Single Source of Truth

All processed paper content MUST be stored in Notion. The system does not maintain a separate database.
- Notion database structure defines the data model (title, authors, summary, tags, source URL, etc.)
- Agent MUST validate Notion connectivity before processing papers
- Failed Notion writes MUST halt processing and raise alerts
- Notion API rate limits MUST be respected with exponential backoff

**Rationale**: Centralized knowledge management in user's existing Notion workspace avoids data fragmentation.

### V. Observability & Debugging

Every agent execution MUST produce structured logs. Logs include:
- Timestamp, execution ID, scheduled vs. manual trigger
- Papers fetched (source, count)
- Processing status per paper (success/failure, duration)
- Notion write results (database ID, page ID)
- Errors with full stack traces

**Rationale**: Scheduled systems require robust logging to diagnose issues without real-time monitoring.

## Development Constraints

### Technology Stack (MANDATORY)

- **Language**: Python 3.11+
- **Agent SDK**: OpenAI Agents SDK (with sampling_callback modification)
- **MCP Servers**:
  - `schedule-task-mcp` v0.2.0 (scheduling, sampling integration)
  - Notion MCP or Notion API SDK (content storage)
  - context MCP (API documentation, dependency code lookup)
- **Environment**: Local `.venv` virtual environment
- **Source Platform**: Xiaohongshu (小红书) - user "大模型知识分享" (ID: 467792329)

### Xiaohongshu Data Fetching

- Papers originate from Xiaohongshu posts (each post = one paper)
- Fetching mechanism MUST handle Xiaohongshu's anti-scraping measures (rate limiting, authentication)
- If official API unavailable, use compliant web scraping with respectful rate limits
- Parse post content to extract: paper title, authors, abstract/summary, PDF link (if available), tags

### API Documentation & Dependency Management

- Use context MCP to fetch documentation for OpenAI Agents SDK, Notion API, schedule-task-mcp
- Avoid hardcoding API schemas; query context MCP when integration questions arise
- Keep dependency versions pinned in `requirements.txt`

## Workflow & Quality Gates

### Development Workflow

1. **Setup**: Create `.venv`, install dependencies, configure MCP servers
2. **Agent Modification**: Extend OpenAI Agents SDK to accept `sampling_callback` (per schedule-task-mcp docs)
3. **Integration Testing**: Test Xiaohongshu fetching, Notion writes, schedule-task-mcp callbacks independently
4. **End-to-End Testing**: Run manual agent execution, verify Notion database population
5. **Schedule Activation**: Configure schedule-task-mcp, test scheduled execution
6. **Monitoring**: Verify logs, confirm autonomous operation

### Testing Requirements (OPTIONAL)

Tests are optional unless explicitly requested. When included:
- Unit tests for parsing logic (Xiaohongshu post → structured data)
- Integration tests for Notion API (create page, verify content)
- Mock tests for scheduled execution (verify sampling_callback integration)

### Quality Gates

Before activating scheduled execution:
- [ ] Directory confinement validated (no file access outside project directory)
- [ ] Notion database schema created and accessible
- [ ] Agent successfully processes ≥3 sample papers manually
- [ ] Logs demonstrate full observability (fetch → process → store → result)
- [ ] Schedule-task-mcp callback invokes agent without errors

## Governance

### Amendment Process

1. Propose change with version bump rationale (MAJOR/MINOR/PATCH per semantic versioning)
2. Update constitution.md with new version, amended date
3. Review dependent templates (plan, spec, tasks) for consistency
4. Document migration impact (e.g., "Principle V expansion requires logging upgrade")
5. Commit with message format: `docs: amend constitution to vX.Y.Z (description)`

### Versioning Policy

- **MAJOR** (X.0.0): Breaking principle changes (e.g., remove Notion, change agent SDK)
- **MINOR** (1.X.0): New principles or significant expansions (e.g., add security principle)
- **PATCH** (1.0.X): Clarifications, typos, non-semantic refinements

### Compliance

- All feature specifications MUST reference this constitution in the "Constitution Check" section
- Implementation plans MUST justify any principle deviations in "Complexity Tracking"
- Code reviews MUST verify directory confinement and logging completeness

**Version**: 1.0.0 | **Ratified**: 2025-10-18 | **Last Amended**: 2025-10-18
