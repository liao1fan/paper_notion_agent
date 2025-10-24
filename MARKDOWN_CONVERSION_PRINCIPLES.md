# Markdown 转 Notion 技术原理详解

## 核心问题回顾

当前代码问题：
```python
# ❌ 错误做法：直接分割字符串
lines = markdown_text.split('\n')
for line in lines:
    blocks.append({
        "paragraph": {
            "rich_text": [{"text": {"content": line}}]  # 缺少 annotations
        }
    })
```

为什么错误？
1. `**加粗**` 被当作普通文本，包含星号
2. 无法识别嵌套结构（列表、引用等）
3. 没有 `annotations` 对象来控制样式

---

## 方案 1: Martian (JavaScript) - 原版最成熟方案

### 技术架构

```
┌─────────────────┐
│  Markdown 文本   │
│  "**bold** text" │
└────────┬─────────┘
         │
         ▼
┌─────────────────────────────────┐
│  unified + remark-parse         │  ← 将 Markdown 解析为 AST
│  (Markdown Parser)              │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Markdown AST (抽象语法树)        │
│  {                              │
│    type: 'paragraph',           │
│    children: [                  │
│      {type: 'strong', ...},     │
│      {type: 'text', ...}        │
│    ]                            │
│  }                              │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  自定义 Transformer              │  ← 遍历 AST，转换为 Notion 对象
│  (src/transformers/)            │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Notion API Blocks              │
│  [                              │
│    {                            │
│      type: "paragraph",         │
│      paragraph: {               │
│        rich_text: [             │
│          {                      │
│            text: {content: "bold"},│
│            annotations: {       │
│              bold: true         │  ← ✅ 正确的格式
│            }                    │
│          }                      │
│        ]                        │
│      }                          │
│    }                            │
│  ]                              │
└─────────────────────────────────┘
```

### 核心代码逻辑

#### 1. 解析 Markdown

使用 `unified` + `remark-parse`：
```javascript
import {unified} from 'unified';
import remarkParse from 'remark-parse';

const processor = unified()
  .use(remarkParse);  // 解析 Markdown

const ast = processor.parse(markdownText);
```

#### 2. 遍历 AST 节点

```javascript
// 遍历 AST，识别不同类型的节点
function visitNode(node) {
  switch(node.type) {
    case 'strong':  // **粗体**
      return {
        annotations: {bold: true},
        text: {content: node.children[0].value}
      };

    case 'emphasis':  // *斜体*
      return {
        annotations: {italic: true},
        text: {content: node.children[0].value}
      };

    case 'list':  // 列表
      return convertList(node);

    // ... 其他类型
  }
}
```

#### 3. 处理嵌套列表

```javascript
function convertList(listNode) {
  const items = listNode.children.map(item => {
    const block = {
      type: 'bulleted_list_item',
      bulleted_list_item: {
        rich_text: convertInline(item.children[0])
      }
    };

    // ✅ 关键：递归处理子列表
    if (item.children.length > 1) {
      block.bulleted_list_item.children =
        convertList(item.children[1]);  // 递归
    }

    return block;
  });

  return items;
}
```

### 优点
- ✅ 最成熟、文档最全
- ✅ 支持 GFM (GitHub Flavored Markdown)
- ✅ 自动处理 Notion API 限制
- ✅ 活跃维护（2025年）

### 缺点
- ❌ JavaScript/TypeScript，需要 Node.js
- ❌ Python 项目集成需要额外步骤

### 集成方式

**方式 A: subprocess 调用**

```python
import subprocess
import json

def markdown_to_notion(md_text: str) -> list:
    # 调用 Node.js 脚本
    result = subprocess.run(
        ['node', 'convert.js'],
        input=md_text,
        capture_output=True,
        text=True
    )
    return json.loads(result.stdout)
```

**方式 B: MCP Server**

创建独立的 MCP 服务，通过 MCP 协议调用。

**方式 C: HTTP API**

使用现成的在线服务：https://md2notion.hilars.dev

---

## 方案 2: mistletoe + 自定义渲染器 (Python)

### 技术架构

```
┌─────────────────┐
│  Markdown 文本   │
└────────┬─────────┘
         │
         ▼
┌─────────────────────────────────┐
│  mistletoe.Document()           │  ← Markdown 解析器
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Token 树 (类似 AST)             │
│  Document                       │
│    ├─ Paragraph                │
│    │   ├─ Strong ("**bold**")  │
│    │   └─ RawText               │
│    └─ List                     │
│        ├─ ListItem (主)        │
│        │   └─ List (嵌套)      │
│        └─ ListItem             │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  自定义 NotionRenderer          │  ← 继承 BaseRenderer
│  - render_strong()              │
│  - render_emphasis()            │
│  - render_list()                │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Notion API Blocks              │
└─────────────────────────────────┘
```

### 核心代码实现

#### 1. 创建自定义渲染器

```python
from mistletoe import Document
from mistletoe.base_renderer import BaseRenderer

class NotionRenderer(BaseRenderer):
    """自定义 Notion API 渲染器"""

    def __init__(self):
        super().__init__()
        self.blocks = []
        self.current_rich_text = []

    def render_strong(self, token):
        """处理粗体 **text**"""
        content = self.render_inner(token)
        return {
            "type": "text",
            "text": {"content": content},
            "annotations": {
                "bold": True,
                "italic": False,
                "strikethrough": False,
                "underline": False,
                "code": False,
                "color": "default"
            }
        }

    def render_emphasis(self, token):
        """处理斜体 *text*"""
        content = self.render_inner(token)
        return {
            "type": "text",
            "text": {"content": content},
            "annotations": {
                "bold": False,
                "italic": True,  # ← 斜体
                # ...
            }
        }

    def render_paragraph(self, token):
        """处理段落"""
        rich_text = []

        # 遍历段落中的所有子 token
        for child in token.children:
            rich_text.append(self.render(child))

        return {
            "type": "paragraph",
            "paragraph": {
                "rich_text": rich_text
            }
        }

    def render_list(self, token):
        """处理列表（关键：支持嵌套）"""
        items = []

        for list_item in token.children:
            item_block = self._render_list_item(list_item)
            items.append(item_block)

        return items

    def _render_list_item(self, token):
        """渲染单个列表项"""
        # 1. 提取主内容
        main_content = []
        children = []

        for child in token.children:
            if isinstance(child, List):
                # ✅ 递归处理嵌套列表
                children.extend(self.render_list(child))
            else:
                main_content.append(self.render(child))

        # 2. 构建 block
        block = {
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": main_content
            }
        }

        # 3. 添加子项（如果有）
        if children:
            block["bulleted_list_item"]["children"] = children

        return block
```

#### 2. 使用渲染器

```python
from mistletoe import Document

def markdown_to_notion_blocks(markdown_text: str) -> list:
    """将 Markdown 转换为 Notion blocks"""

    # 解析 Markdown
    with NotionRenderer() as renderer:
        doc = Document(markdown_text)
        blocks = renderer.render(doc)

    return blocks
```

#### 3. 处理混合格式

```python
# Markdown: "This is **bold and _italic_** text"

# Token 树:
Paragraph
  ├─ RawText("This is ")
  ├─ Strong
  │   ├─ RawText("bold and ")
  │   └─ Emphasis
  │       └─ RawText("italic")
  └─ RawText(" text")

# 渲染结果:
[
  {
    "text": {"content": "This is "},
    "annotations": {"bold": false, "italic": false}
  },
  {
    "text": {"content": "bold and "},
    "annotations": {"bold": true, "italic": false}
  },
  {
    "text": {"content": "italic"},
    "annotations": {"bold": true, "italic": true}  # ← 叠加
  },
  {
    "text": {"content": " text"},
    "annotations": {"bold": false, "italic": false}
  }
]
```

### 优点
- ✅ 纯 Python 实现
- ✅ 完全控制转换逻辑
- ✅ 可以针对项目需求定制

### 缺点
- ❌ 需要自己处理各种边界情况
- ❌ 开发工作量大（估计 500-1000 行代码）
- ❌ 需要维护和测试

### 参考实现
- md2notion (已废弃): https://github.com/Cobertos/md2notion/blob/master/md2notion/NotionPyRenderer.py

---

## 方案 3: markdown-it-py + 自定义插件 (Python)

### 技术架构

```
┌─────────────────┐
│  Markdown 文本   │
└────────┬─────────┘
         │
         ▼
┌─────────────────────────────────┐
│  markdown_it.MarkdownIt()       │  ← 更现代的解析器
│    .enable(['table', 'strikethrough'])│
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Token 流                       │
│  [                              │
│    Token(type='paragraph_open'),│
│    Token(type='inline', ...),   │
│    Token(type='paragraph_close')│
│  ]                              │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  自定义 Renderer                │
│  - renderToken()                │
│  - renderInline()               │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Notion API Blocks              │
└─────────────────────────────────┘
```

### 核心代码

```python
from markdown_it import MarkdownIt
from markdown_it.token import Token

class NotionRenderer:
    """基于 markdown-it-py 的渲染器"""

    def render(self, tokens: list[Token]) -> list:
        blocks = []
        i = 0

        while i < len(tokens):
            token = tokens[i]

            if token.type == 'paragraph_open':
                # 找到对应的 inline 和 close token
                inline_token = tokens[i + 1]
                para_block = self.render_paragraph(inline_token)
                blocks.append(para_block)
                i += 3  # skip open, inline, close

            elif token.type == 'bullet_list_open':
                # 收集所有 list_item
                list_blocks = self.render_list(tokens, i)
                blocks.extend(list_blocks)
                i = self.find_closing_token(tokens, i) + 1

            else:
                i += 1

        return blocks

    def render_inline(self, token: Token) -> list:
        """渲染内联元素（关键：处理格式）"""
        rich_text = []

        if not token.children:
            return []

        i = 0
        while i < len(token.children):
            child = token.children[i]

            if child.type == 'text':
                rich_text.append({
                    "type": "text",
                    "text": {"content": child.content},
                    "annotations": self.default_annotations()
                })

            elif child.type == 'strong_open':
                # 找到对应的内容和 close token
                content_token = token.children[i + 1]
                rich_text.append({
                    "type": "text",
                    "text": {"content": content_token.content},
                    "annotations": {
                        **self.default_annotations(),
                        "bold": True  # ← 设置粗体
                    }
                })
                i += 2  # skip content and close

            elif child.type == 'em_open':
                content_token = token.children[i + 1]
                rich_text.append({
                    "type": "text",
                    "text": {"content": content_token.content},
                    "annotations": {
                        **self.default_annotations(),
                        "italic": True  # ← 设置斜体
                    }
                })
                i += 2

            i += 1

        return rich_text
```

### 优点
- ✅ 纯 Python，更现代化的 API
- ✅ 插件系统，易于扩展
- ✅ 性能好

### 缺点
- ❌ Token 流处理比 AST 复杂
- ❌ 需要手动匹配 open/close token
- ❌ 开发工作量较大

---

## 三种方案对比

| 特性 | Martian (JS) | mistletoe (Python) | markdown-it-py (Python) |
|------|-------------|-------------------|------------------------|
| **语言** | JavaScript | Python | Python |
| **成熟度** | ⭐⭐⭐⭐⭐ 最成熟 | ⭐⭐⭐ 中等 | ⭐⭐⭐⭐ 较成熟 |
| **文档** | ⭐⭐⭐⭐⭐ 详细 | ⭐⭐⭐ 一般 | ⭐⭐⭐⭐ 好 |
| **集成难度** | 🔴 需要 Node.js | 🟢 直接集成 | 🟢 直接集成 |
| **开发工作量** | 🟢 使用现成的 | 🟡 中等（500行） | 🟡 中等（400行） |
| **维护成本** | 🟢 低（官方维护） | 🔴 高（需自己维护） | 🟡 中（需自己维护） |
| **功能完整性** | ⭐⭐⭐⭐⭐ 全功能 | ⭐⭐⭐⭐ 可定制 | ⭐⭐⭐⭐ 可定制 |
| **嵌套列表** | ✅ 自动处理 | ✅ 需自己实现 | ✅ 需自己实现 |
| **性能** | ⭐⭐⭐⭐ 好 | ⭐⭐⭐⭐ 好 | ⭐⭐⭐⭐⭐ 很好 |

---

## 推荐决策树

```
开始
  │
  ├─ 可以接受 Node.js 依赖？
  │   ├─ Yes → 使用 Martian (方案 1) ⭐ 推荐
  │   └─ No  → 继续
  │
  ├─ 需要完全控制转换逻辑？
  │   ├─ Yes → 自己实现（方案 2 或 3）
  │   └─ No  → 尝试找 Python 替代品
  │
  └─ 有时间开发和测试？
      ├─ Yes → mistletoe (方案 2) - 更直观
      │        或 markdown-it-py (方案 3) - 更现代
      └─ No  → 使用 Martian + subprocess
```

---

## 实际代码示例

### 当前代码（错误）

```python
# paper_digest/digest_agent_core.py:697-762
def _markdown_to_notion_blocks(markdown_text: str) -> list:
    blocks = []
    lines = markdown_text.split('\n')  # ❌ 简单分割

    for line in lines:
        if line.startswith('##'):
            # 标题 - ❌ 没有解析内联格式
            blocks.append({
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{
                        "text": {"content": line[2:].strip()}
                    }]
                }
            })
        elif line.startswith('- '):
            # 列表 - ❌ 不支持嵌套
            blocks.append({
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{
                        "text": {"content": line[2:].strip()}
                    }]
                }
            })
        else:
            # 段落 - ❌ **bold** 被当作普通文本
            blocks.append({
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{
                        "text": {"content": line}
                    }]
                }
            })

    return blocks
```

### 正确做法（使用 Martian）

```python
import subprocess
import json

def _markdown_to_notion_blocks(markdown_text: str) -> list:
    """使用 Martian 转换 Markdown"""

    # 准备 Node.js 脚本
    js_code = """
    const {markdownToBlocks} = require('@tryfabric/martian');
    const fs = require('fs');
    const input = fs.readFileSync(0, 'utf-8');
    const blocks = markdownToBlocks(input);
    console.log(JSON.stringify(blocks));
    """

    # 调用 Node.js
    result = subprocess.run(
        ['node', '-e', js_code],
        input=markdown_text,
        capture_output=True,
        text=True,
        check=True
    )

    blocks = json.loads(result.stdout)
    return blocks[:100]  # Notion 限制
```

### 测试对比

```python
# 测试输入
md_text = """
## 标题

这是 **粗体** 和 *斜体* 文本。

- 主列表项
  - 子列表项 1
  - 子列表项 2
"""

# ❌ 当前输出（错误）
[
  {
    "type": "paragraph",
    "paragraph": {
      "rich_text": [{
        "text": {"content": "这是 **粗体** 和 *斜体* 文本。"}
        # ← 星号被保留！
      }]
    }
  }
]

# ✅ Martian 输出（正确）
[
  {
    "type": "heading_2",
    "heading_2": {
      "rich_text": [{
        "text": {"content": "标题"},
        "annotations": {"bold": false, ...}
      }]
    }
  },
  {
    "type": "paragraph",
    "paragraph": {
      "rich_text": [
        {"text": {"content": "这是 "}},
        {
          "text": {"content": "粗体"},
          "annotations": {"bold": true}  # ← 正确！
        },
        {"text": {"content": " 和 "}},
        {
          "text": {"content": "斜体"},
          "annotations": {"italic": true}  # ← 正确！
        },
        {"text": {"content": " 文本。"}}
      ]
    }
  },
  {
    "type": "bulleted_list_item",
    "bulleted_list_item": {
      "rich_text": [{"text": {"content": "主列表项"}}],
      "children": [  # ← 嵌套！
        {
          "type": "bulleted_list_item",
          "bulleted_list_item": {
            "rich_text": [{"text": {"content": "子列表项 1"}}]
          }
        },
        {
          "type": "bulleted_list_item",
          "bulleted_list_item": {
            "rich_text": [{"text": {"content": "子列表项 2"}}]
          }
        }
      ]
    }
  }
]
```

---

## 总结

### 核心原理
所有方案的本质都是：
1. **解析** Markdown → AST/Token 树
2. **遍历** 树节点，识别类型
3. **转换** 为 Notion API 格式（带 annotations）
4. **递归** 处理嵌套结构

### 关键差异
- **Martian**: 最成熟，但需要 Node.js
- **mistletoe**: AST 更直观，适合自定义
- **markdown-it-py**: Token 流处理，性能好

### 建议
1. **首选**: Martian (如果可以接受 Node.js)
2. **备选**: mistletoe (纯 Python，自己实现)
3. **最后**: markdown-it-py (更复杂，但性能更好)

---

**文档时间**: 2025-10-21
