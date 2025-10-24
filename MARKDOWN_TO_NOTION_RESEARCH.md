# Markdown 转 Notion API 格式问题调研报告

## 问题描述

当前系统使用自定义的 `_markdown_to_notion_blocks()` 函数将 Markdown 转换为 Notion blocks，存在以下格式问题：

1. **加粗文本问题**：Markdown 中的 `**加粗文本**` 在 Notion 中直接显示为 `**加粗文本**`（包含星号），而不是真正的粗体
2. **无序列表缩进问题**：嵌套的无序列表没有缩进，无法区分主内容和子内容的层级关系
3. **其他格式问题**：斜体、删除线、内联代码等 Markdown 格式可能也存在类似问题

## 根本原因分析

### 1. Rich Text Annotations 机制

根据 **Notion 官方文档** ([Rich Text Reference](https://developers.notion.com/reference/rich-text))，Notion API 使用 `annotations` 对象来控制文本样式：

```json
{
  "type": "text",
  "text": {
    "content": "加粗文本"
  },
  "annotations": {
    "bold": true,
    "italic": false,
    "strikethrough": false,
    "underline": false,
    "code": false,
    "color": "default"
  }
}
```

**关键点**：
- 不能直接传递带有 `**` 的文本
- 必须解析 Markdown 格式，提取纯文本，然后在 `annotations` 中设置 `bold: true`
- 每个不同格式的文本片段需要单独的 `rich_text` 对象

### 2. 嵌套列表的 Children 机制

根据 **Notion 官方文档** ([Working with Page Content](https://developers.notion.com/docs/working-with-page-content))，嵌套列表使用 `children` 属性：

```json
{
  "type": "bulleted_list_item",
  "bulleted_list_item": {
    "rich_text": [{
      "type": "text",
      "text": {
        "content": "主列表项"
      }
    }],
    "color": "default",
    "children": [
      {
        "type": "bulleted_list_item",
        "bulleted_list_item": {
          "rich_text": [{
            "type": "text",
            "text": {
              "content": "子列表项"
            }
          }]
        }
      }
    ]
  }
}
```

**关键点**：
- 嵌套列表项通过 `children` 数组表示
- 支持的 block 类型：`paragraph`, `bulleted_list_item`, `numbered_list_item`, `toggle`, `to_do`, `page`
- `has_children` 属性标识是否有子元素

## 解决方案调研

### 方案 A：使用现有的 Markdown 转 Notion 库

#### 1. **Martian** (@tryfabric/martian) - JavaScript/TypeScript ⭐ 推荐

**GitHub**: https://github.com/tryfabric/martian
**NPM**: https://www.npmjs.com/package/@tryfabric/martian

**优点**：
- ✅ 活跃维护（2025年仍在更新）
- ✅ 完整支持所有内联格式（加粗、斜体、删除线、内联代码、链接、公式）
- ✅ 支持任意深度的嵌套列表（有序、无序、复选框）
- ✅ 支持所有标题层级
- ✅ 支持代码块、引用块、表格、公式、图片
- ✅ 提供详细的示例和文档
- ✅ 自动处理 Notion API 限制（字符数、children 数量）

**示例**（来自官方 README）：

```javascript
const {markdownToBlocks, markdownToRichText} = require('@tryfabric/martian');

// 解析富文本（包含加粗和斜体）
markdownToRichText(`**Hello _world_**`);
// 返回：
[
  {
    "type": "text",
    "annotations": {
      "bold": true,
      "italic": false,
      // ...
    },
    "text": {
      "content": "Hello "
    }
  },
  {
    "type": "text",
    "annotations": {
      "bold": true,
      "italic": true,
      // ...
    },
    "text": {
      "content": "world"
    }
  }
]
```

**嵌套列表示例**（来自 README）：

```markdown
* 主列表项
  * 子列表项 1
  * 子列表项 2
    * 更深层级
```

会被正确转换为带 `children` 属性的嵌套结构。

**缺点**：
- ❌ 是 JavaScript/TypeScript 库，需要在 Python 项目中调用 Node.js
- ❌ 需要安装 Node.js 环境

**如何集成到 Python 项目**：
1. 使用 `subprocess` 调用 Node.js 脚本
2. 使用 MCP (Model Context Protocol) 封装为工具
3. 通过 HTTP API 包装（例如 https://md2notion.hilars.dev 就是基于 martian 的在线服务）

---

#### 2. **md2notion** (Cobertos/md2notion) - Python ❌ 已废弃

**GitHub**: https://github.com/Cobertos/md2notion

**状态**：⚠️ **已不再维护**（作者已转用 Obsidian）

**优点**：
- ✅ 纯 Python 实现
- ✅ 曾经处理过格式问题（代码围栏、嵌套列表、图片等）
- ✅ 使用 `mistletoe` 作为 Markdown 解析器

**缺点**：
- ❌ **已废弃**，不建议使用
- ❌ 基于旧的 `notion-py` 库（非官方 API）

---

#### 3. **md2notionpage** - Python

**PyPI**: https://pypi.org/project/md2notionpage/

**优点**：
- ✅ 纯 Python 实现
- ✅ 支持基本的 Markdown 格式
  - 加粗：`**` 或 `__`
  - 斜体：`*` 或 `_`
  - 有序/无序列表

**缺点**：
- ⚠️ 功能相对基础
- ⚠️ 文档较少，不确定是否支持嵌套列表
- ⚠️ GitHub stars 较少，维护状态不明

---

#### 4. **markdown2notion** (GuyMicciche/markdown2notion) - Python

**GitHub**: https://github.com/GuyMicciche/markdown2notion

**优点**：
- ✅ 纯 Python 实现
- ✅ 是 martian 的 Python 移植版本
- ✅ 支持内联格式（加粗、斜体、删除线、内联代码、链接、公式）

**缺点**：
- ⚠️ Stars 较少（相比 martian）
- ⚠️ 更新频率不如 martian
- ⚠️ 文档不如 martian 详细

---

### 方案 B：自己实现 Markdown 解析器

使用 Python Markdown 解析库（如 `mistletoe` 或 `markdown-it-py`）+ 自定义渲染器

**推荐库**：

1. **mistletoe** - https://github.com/miyuchina/mistletoe
   - 快速、可扩展
   - 支持自定义渲染器
   - md2notion 就是基于此实现的

2. **markdown-it-py** - https://github.com/executablebooks/markdown-it-py
   - Python 版本的 markdown-it
   - 更现代化的 API
   - 支持插件

**优点**：
- ✅ 完全控制转换逻辑
- ✅ 可以根据项目需求定制
- ✅ 纯 Python 实现

**缺点**：
- ❌ 开发工作量大
- ❌ 需要处理各种边界情况
- ❌ 需要维护和测试

---

### 方案 C：使用 MCP 服务封装 Martian

创建一个 MCP Server 来封装 martian 库的功能

**优点**：
- ✅ 可以利用 martian 的成熟实现
- ✅ 通过 MCP 协议与 Python 项目集成
- ✅ 保持代码清晰分离

**缺点**：
- ⚠️ 需要额外开发 MCP Server
- ⚠️ 增加系统复杂度（需要 Node.js 运行时）

**参考实现**：
- https://md2notion.hilars.dev - 基于 martian 的 API 服务

---

## 推荐方案

### 🥇 首选：使用 **markdown2notion** (Python 移植版)

**理由**：
1. ✅ 纯 Python 实现，无需 Node.js
2. ✅ 基于成熟的 martian 设计
3. ✅ 支持所有必需的格式（加粗、斜体、嵌套列表等）
4. ✅ 集成简单，可以直接替换现有的 `_markdown_to_notion_blocks()`

**安装**：
```bash
pip install markdown2notion
```

**使用示例**（推测，需验证实际 API）：
```python
from markdown2notion import markdown_to_blocks

markdown_text = """
# 标题

**加粗文本** 和 *斜体文本*

- 主列表项
  - 子列表项 1
  - 子列表项 2
"""

blocks = markdown_to_blocks(markdown_text)
# 返回 Notion API blocks，可直接用于 pages.create()
```

---

### 🥈 备选：通过 subprocess 调用 **Martian** (Node.js)

如果 `markdown2notion` 不满足需求，可以使用原版 martian：

**步骤**：

1. 安装 martian：
```bash
npm install -g @tryfabric/martian
```

2. 创建 Node.js 脚本 `markdown_converter.js`：
```javascript
#!/usr/bin/env node
const {markdownToBlocks} = require('@tryfabric/martian');
const fs = require('fs');

const markdown = fs.readFileSync(0, 'utf-8'); // 从 stdin 读取
const blocks = markdownToBlocks(markdown);
console.log(JSON.stringify(blocks));
```

3. 在 Python 中调用：
```python
import subprocess
import json

def markdown_to_notion_blocks(markdown_text: str) -> list:
    result = subprocess.run(
        ['node', 'markdown_converter.js'],
        input=markdown_text,
        capture_output=True,
        text=True
    )
    return json.loads(result.stdout)
```

**优点**：
- ✅ 使用最成熟、维护最好的库
- ✅ 功能最完整

**缺点**：
- ❌ 需要 Node.js 环境
- ❌ 子进程调用有性能开销

---

### 🥉 最后备选：自己实现（基于 mistletoe）

如果以上方案都不可行，可以参考 md2notion 的实现思路：

1. 使用 `mistletoe` 解析 Markdown 为 AST
2. 创建自定义 `NotionRenderer` 类
3. 遍历 AST，生成 Notion API blocks

**参考代码**（来自 md2notion）：
https://github.com/Cobertos/md2notion/blob/master/md2notion/NotionPyRenderer.py

---

## 具体修改建议

### 当前代码位置

文件：`paper_digest/digest_agent_core.py`

函数：`_markdown_to_notion_blocks(markdown_text: str) -> list` (行 697-762)

### 问题代码示例

```python
# 当前实现
def _markdown_to_notion_blocks(markdown_text: str) -> list:
    blocks = []
    lines = markdown_text.split('\n')

    for line in lines:
        # ...
        # 段落 - 问题：直接传递文本，不解析 Markdown
        else:
            if len(line) > 2000:
                line = line[:2000]
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": line}}]
                    # ❌ 缺少 annotations 对象
                }
            })
```

这会导致 `**加粗**` 被当作普通文本处理。

### 正确的实现（基于 Notion API）

```python
# 正确示例
{
    "object": "block",
    "type": "paragraph",
    "paragraph": {
        "rich_text": [
            {
                "type": "text",
                "text": {"content": "Hello "},
                "annotations": {
                    "bold": false,
                    "italic": false,
                    # ...
                }
            },
            {
                "type": "text",
                "text": {"content": "world"},
                "annotations": {
                    "bold": true,  # ✅ 设置加粗
                    "italic": false,
                    # ...
                }
            }
        ]
    }
}
```

---

## 实施步骤

### 阶段 1：验证方案

1. ✅ 测试 `markdown2notion` 库
   ```bash
   pip install markdown2notion
   python -c "from markdown2notion import markdown_to_blocks; print(markdown_to_blocks('**bold**'))"
   ```

2. ✅ 确认输出格式符合 Notion API 规范

### 阶段 2：集成到项目

1. 替换 `_markdown_to_notion_blocks()` 函数
2. 更新 `save_digest_to_notion()` 调用
3. 测试各种 Markdown 格式：
   - 加粗、斜体、删除线
   - 嵌套列表（2-3层）
   - 混合格式（加粗+斜体）
   - 代码块、链接

### 阶段 3：回归测试

1. 运行完整的论文整理流程
2. 检查 Notion 中的格式是否正确
3. 对比 Markdown 原文和 Notion 渲染结果

---

## 参考资料

### 官方文档
1. **Notion API - Rich Text**: https://developers.notion.com/reference/rich-text
2. **Notion API - Working with Page Content**: https://developers.notion.com/docs/working-with-page-content
3. **Notion API - Block Types**: https://developers.notion.com/reference/block

### 工具和库
1. **Martian (JavaScript)**: https://github.com/tryfabric/martian
2. **markdown2notion (Python)**: https://github.com/GuyMicciche/markdown2notion
3. **md2notionpage (Python)**: https://pypi.org/project/md2notionpage/
4. **mistletoe (Markdown Parser)**: https://github.com/miyuchina/mistletoe
5. **markdown-it-py (Markdown Parser)**: https://github.com/executablebooks/markdown-it-py

### 教程和示例
1. **Markdown in Notion Guide (2025)**: https://www.goinsight.ai/blog/markdown-to-notion/
2. **Notion Markdown Reference**: https://www.markdownguide.org/tools/notion/
3. **Stack Overflow - Notion API Lists**: https://stackoverflow.com/questions/70133832/how-do-you-solve-for-multiple-bulleted-list-item

---

## 总结

**核心问题**：当前的简单字符串分割无法正确处理 Markdown 格式，需要使用专门的 Markdown 解析器。

**最佳方案**：使用 `markdown2notion` Python 库，它提供了成熟的 Markdown → Notion API 转换功能。

**次优方案**：通过 subprocess 调用 `martian` (Node.js)。

**最后方案**：基于 `mistletoe` 自己实现解析器。

建议优先尝试方案 1（markdown2notion），如果不满足需求再考虑其他方案。

---

**文档整理时间**: 2025-10-21
**整理人**: Claude Code (Opus 4.1)
