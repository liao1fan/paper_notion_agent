# 数据一致性指南

## 问题背景

在分布式系统中，保持**本地存储**和**远程数据库**的数据一致性是一个经典挑战。

### 原有问题

1. **双写不一致**：先写 Notion ✅ → 再写本地 ❌ = Notion 有数据，本地没记录
2. **单向同步**：只有本地→Notion，没有 Notion→本地
3. **无对账机制**：手动在 Notion 删除数据后，本地索引不知道
4. **错误信息不明确**：失败时无法判断是 Notion 错误还是本地错误

---

## 解决方案：Notion 作为单一数据源（Single Source of Truth）

### 核心策略

```
┌─────────────────────────────────────────────────┐
│         Notion Database (Source of Truth)       │
│  - 用户真正查看和管理数据的地方                    │
│  - 发生冲突时，以 Notion 为准                     │
└─────────────────────────────────────────────────┘
                      ↓
                    同步
                      ↓
┌─────────────────────────────────────────────────┐
│      Local Database (Cache/Index)              │
│  - 仅用于性能优化和去重                           │
│  - 定期从 Notion 同步                            │
│  - 本地失败不影响整体成功                          │
└─────────────────────────────────────────────────┘
```

---

## 实现改进

### 1. ✅ NotionClient 新增查询功能

**文件**: `src/services/notion.py`

新增 `query_by_source_url()` 方法：

```python
async def query_by_source_url(self, source_url: str) -> Optional[str]:
    """
    通过 Source URL 查询 Notion 数据库，检查是否已存在该页面

    Returns:
        Page ID if found, None otherwise
    """
```

**用途**：在保存前查询 Notion 是否已存在，避免重复创建。

---

### 2. ✅ 改进的 save_to_notion 逻辑

**文件**: `tools.py`

#### 新的保存流程

```
1. 验证输入数据
      ↓
2. 初始化 Notion 客户端
      ↓
3. 查询 Notion 是否已存在（通过 Source URL）
      ↓
4. 如果已存在 → 返回提示（不重复创建）
      ↓
5. 如果不存在 → 保存到 Notion（关键步骤）
      ↓
6. 更新本地索引（非关键步骤）
      ↓
   本地失败？→ 记录日志，但不影响整体成功
      ↓
7. 返回成功（只要 Notion 保存成功）
```

#### 关键特性

- **以 Notion 为准**：查询 Notion 而不是本地数据库
- **事务性保存**：Notion 成功 = 整体成功，本地失败不影响
- **明确的错误信息**：区分 `notion_api_error` 和 `unexpected_error`

---

### 3. ✅ Notion → 本地同步工具

**文件**: `sync_from_notion.py`

#### 功能

1. 从 Notion 数据库获取所有页面
2. 解析页面数据（Source URL, page_id, post_id）
3. 清空本地数据库
4. 批量插入同步数据

#### 使用方法

```bash
# 手动同步
python sync_from_notion.py

# 定期同步（cron job）
0 2 * * * cd /path/to/project && python sync_from_notion.py
```

#### 适用场景

- ✅ 手动在 Notion 中删除/修改数据后
- ✅ 定期对账，确保本地索引与 Notion 一致
- ✅ 初次部署时，从 Notion 导入已有数据

---

### 4. ✅ 动态 Schema 对齐

**文件**: `src/models/notion_entry.py`, `src/services/notion.py`

#### 改进

- 保存前动态获取 Notion 数据库 schema
- `to_notion_properties(schema)` 根据实际字段名匹配
- 支持多种命名（如 Name/Title/名称/标题）
- 类型验证（title, rich_text, url, multi_select）

#### 好处

- ✅ 适应不同的 Notion 数据库配置
- ✅ 字段不存在时自动跳过
- ✅ 清晰的日志：显示匹配的字段

---

## 使用指南

### 日常使用

1. **正常保存**：
   ```python
   # Agent 会自动调用 save_to_notion
   # 1. 查询 Notion 是否已存在
   # 2. 不存在则保存到 Notion
   # 3. 更新本地索引
   ```

2. **手动在 Notion 中操作后**：
   ```bash
   # 运行同步工具，更新本地索引
   python sync_from_notion.py
   ```

### 故障恢复

#### 场景 1：Notion 保存成功，本地失败

```bash
# 现象：Notion 中有数据，本地数据库没有

# 解决：运行同步工具
python sync_from_notion.py
```

#### 场景 2：手动删除 Notion 页面

```bash
# 现象：本地数据库还有记录

# 解决：运行同步工具（清空本地后重新同步）
python sync_from_notion.py
```

#### 场景 3：本地数据库损坏

```bash
# 解决：删除本地数据库，重新初始化并同步
rm data/processing_records.db
python sync_from_notion.py
```

---

## 对比：改进前 vs 改进后

| 维度 | 改进前 | 改进后 |
|------|--------|--------|
| **数据源** | 本地数据库检查重复 | Notion 作为 source of truth |
| **查重逻辑** | 查询本地数据库 | 查询 Notion API |
| **保存顺序** | Notion → 本地（失败则整体失败） | Notion → 本地（本地失败不影响） |
| **手动操作** | 无法同步 | 运行 `sync_from_notion.py` |
| **对账机制** | 无 | 定期同步工具 |
| **错误处理** | 笼统的错误信息 | 明确区分错误类型 |
| **Schema 匹配** | 硬编码字段名 | 动态对齐 |

---

## 最佳实践

### 1. 定期同步

建议每天定时运行同步工具：

```bash
# crontab -e
0 2 * * * cd /path/to/project && /path/to/.venv/bin/python sync_from_notion.py >> logs/sync.log 2>&1
```

### 2. 监控日志

关注以下日志：

- `本地索引更新失败（Notion 已保存成功）`：需要运行同步工具
- `Notion query failed`：检查 Token 和权限
- `Failed to insert record`：检查本地数据库状态

### 3. 初次部署

```bash
# 1. 配置环境变量
cp .env.example .env
vim .env

# 2. 初始化本地数据库
python -c "import asyncio; from src.storage.database import init_database; asyncio.run(init_database('data/processing_records.db'))"

# 3. 从 Notion 同步已有数据
python sync_from_notion.py

# 4. 启动应用
python chat.py
```

---

## FAQ

### Q1: 为什么不让本地数据库也作为 source of truth？

**A**: 因为用户实际查看和管理数据的地方是 Notion。如果以本地为准，手动在 Notion 中的操作（删除/修改）会被覆盖。

### Q2: 本地索引失败会影响用户吗？

**A**: 不会。只要 Notion 保存成功，数据就是安全的。下次运行同步工具时会自动修复本地索引。

### Q3: 多久运行一次同步工具？

**A**: 建议每天一次。如果频繁手动操作 Notion，可以增加频率或手动运行。

### Q4: 如果 Notion API 失败怎么办？

**A**: 保存会失败，返回明确的错误信息。用户可以稍后重试。数据不会丢失（本地的 `_pending_post` 和 `_pending_extraction` 仍然存在，可以重新保存）。

---

## 技术细节

### Notion API Query

```python
response = await client.databases.query(
    database_id=database_id,
    filter={
        "property": "Source URL",
        "url": {
            "equals": "https://..."
        }
    },
    page_size=1,
)
```

### 本地数据库 Schema

```sql
CREATE TABLE processing_records (
    post_id TEXT PRIMARY KEY,
    post_url TEXT NOT NULL,
    blogger_id TEXT NOT NULL,
    status TEXT NOT NULL,
    notion_page_id TEXT,
    processed_at TEXT NOT NULL,
    error_message TEXT,
    UNIQUE(post_id)
)
```

---

## 总结

通过实现**单一数据源**策略，我们解决了数据一致性问题：

1. ✅ **Notion 作为 source of truth**：查询、保存都以 Notion 为准
2. ✅ **本地作为缓存/索引**：失败不影响整体成功
3. ✅ **双向同步机制**：从 Notion 同步到本地
4. ✅ **明确的错误处理**：区分不同类型的错误
5. ✅ **动态 Schema 对齐**：适应不同的 Notion 配置

**核心原则**：当本地和远程发生冲突时，**Always Trust Notion**。
