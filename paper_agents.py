"""
Paper Agent 定义 - 重构版

主 Agent (paper_agent):
1. 解析用户请求（立即执行 vs 定时任务）
2. 识别链接类型（XHS/PDF/其他）
3. 使用 handoff 转交给 digest_agent 处理论文整理
4. 集成 schedule-task-mcp 处理定时任务

Sub-Agent (digest_agent):
- 专注于论文下载、解析、整理、保存
"""

import os
import re
from pathlib import Path
from typing import Annotated
import json

from agents import Agent, function_tool, handoff

# 获取项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent

# 导入 digest_agent (从 src/services)
from src.services.paper_digest import digest_agent, _init_digest_globals


# ============= 主 Agent 工具 =============

@function_tool
async def identify_link_type(
    url: Annotated[str, "用户提供的URL链接"]
) -> str:
    """
    识别链接类型

    参数:
        url: 用户提供的URL链接

    返回:
        JSON格式的识别结果
    """
    url = url.strip()

    # 识别小红书链接
    xhs_patterns = [
        r'xiaohongshu\.com',
        r'xhslink\.com',
    ]
    for pattern in xhs_patterns:
        if re.search(pattern, url, re.IGNORECASE):
            return json.dumps({
                "type": "xiaohongshu",
                "url": url,
                "message": "这是小红书帖子链接，将获取帖子内容并提取论文信息。"
            }, ensure_ascii=False, indent=2)

    # 识别 PDF 链接
    pdf_patterns = [
        r'\.pdf$',
        r'arxiv\.org/pdf',
        r'\.pdf\?',
    ]
    for pattern in pdf_patterns:
        if re.search(pattern, url, re.IGNORECASE):
            return json.dumps({
                "type": "pdf",
                "url": url,
                "message": "这是PDF文件链接，将直接下载PDF并分析。"
            }, ensure_ascii=False, indent=2)

    # 识别 arXiv abs 链接
    if re.search(r'arxiv\.org/abs', url, re.IGNORECASE):
        # 转换为 PDF 链接
        arxiv_id = re.search(r'abs/(\d+\.\d+)', url)
        if arxiv_id:
            pdf_url = f"https://arxiv.org/pdf/{arxiv_id.group(1)}.pdf"
            return json.dumps({
                "type": "arxiv",
                "url": pdf_url,
                "original_url": url,
                "message": f"这是arXiv论文链接，已转换为PDF链接: {pdf_url}"
            }, ensure_ascii=False, indent=2)

    # 其他链接
    return json.dumps({
        "type": "unknown",
        "url": url,
        "message": "无法识别的链接类型。可能是论文主页或其他类型，请提供小红书链接或PDF链接。"
    }, ensure_ascii=False, indent=2)


# ============= Agent 定义 =============

# 主 Paper Agent
paper_agent = Agent(
    name="paper_agent",
    instructions="""你是一个专业的研究论文整理调度助手（Paper Agent）。

你的职责是：

1. **判断任务类型**
   - 如果用户要求定时执行（如"1分钟后"、"每天早上8点"、"每周"等），使用 schedule-task-mcp 的 create_task 工具创建定时任务
   - 如果是立即执行，继续下一步

2. **识别链接类型**（立即任务）
   - 使用 identify_link_type 识别用户提供的链接类型
   - 支持的类型：小红书链接、PDF链接、arXiv链接

3. **转交给 Digest Agent 处理**（立即任务）
   - 使用 transfer_to_digest_agent 将论文整理任务交给专业的 digest_agent
   - 传递必要的信息：链接类型、URL、任何额外的上下文

⚠️ 重要提示：
- 你只负责调度和任务管理，不直接处理论文整理
- 论文整理（下载、解析、生成、保存）由 digest_agent 完成
- 你可以使用 schedule-task-mcp 提供的工具来管理定时任务

工作流程示例：

**立即执行**：
用户: "帮我整理这篇论文 https://www.xiaohongshu.com/explore/xxx"
你:
  1. 调用 identify_link_type -> 识别为小红书链接
  2. 调用 transfer_to_digest_agent -> 转交给 digest_agent

**定时任务**：
用户: "1分钟后，https://xxx 提取出来并整理到notion"
你:
  1. 使用 schedule-task-mcp 的 create_task 工具创建定时任务
  2. 告诉用户任务已创建，会在指定时间自动执行

请保持对话友好、专业。
""",
    model="gpt-5-mini",
    tools=[
        identify_link_type,
    ],
    handoffs=[
        handoff(
            agent=digest_agent,
            tool_name_override="transfer_to_digest_agent",
            tool_description_override="""将论文整理任务转交给 Digest Agent。

当需要处理论文（下载PDF、提取信息、生成整理、保存到Notion）时使用此工具。

传递给 digest_agent 的信息应包括：
- 链接类型（xiaohongshu/pdf/arxiv）
- URL 链接
- 任何其他上下文信息

示例输入：
"请帮我整理这篇论文，这是小红书链接：https://www.xiaohongshu.com/explore/xxx"
或
"请处理这个PDF：https://arxiv.org/pdf/2505.10831.pdf，标题是：Creating General User Models from Computer Use"
"""
        )
    ]
)


# 初始化函数（供 chat.py 调用）
def init_paper_agents(openai_client):
    """
    初始化 paper agents 的全局变量

    Args:
        openai_client: OpenAI AsyncOpenAI 客户端
    """
    _init_digest_globals(openai_client)
