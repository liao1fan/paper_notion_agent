#!/usr/bin/env python3
"""
Digest Agent Core - 论文整理核心 Agent（作为 sub-agent）

功能：
1. 接收多种输入源（XHS URL、PDF URL、PDF 本地路径）
2. 下载 PDF 并读取全文内容
3. 生成结构化论文整理
4. 保存到 Notion 数据库

作为 sub-agent 被主 paper_agent 调用
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Annotated
import json
import httpx
import fitz  # PyMuPDF
import time

from agents import Agent, function_tool
from openai import AsyncOpenAI
from ..utils.logger import get_logger

# 初始化日志
logger = get_logger(__name__)

# 项目路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent  # spec-paper-notion-agent/
DIGEST_ROOT = Path(__file__).resolve().parent  # src/services/
OUTPUT_DIR = PROJECT_ROOT / "paper_digest" / "outputs"  # 保持输出在原位置
PDF_DIR = PROJECT_ROOT / "paper_digest" / "pdfs"  # 保持PDF在原位置

# 确保目录存在
OUTPUT_DIR.mkdir(exist_ok=True)
PDF_DIR.mkdir(exist_ok=True)

# 全局变量
_openai_client = None
_current_paper = {}


def _init_digest_globals(openai_client):
    """初始化全局变量"""
    global _openai_client
    _openai_client = openai_client


@function_tool
async def fetch_xiaohongshu_post(
    post_url: Annotated[str, "小红书帖子的完整URL"]
) -> str:
    """
    获取小红书帖子内容

    参数:
        post_url: 小红书帖子URL

    返回:
        JSON格式的帖子信息（包含 raw_content）
    """
    global _current_paper
    start_time = time.time()

    # 导入 xiaohongshu 服务
    from .xiaohongshu import XiaohongshuClient

    try:
        logger.info("🔍 开始获取小红书帖子")
        client = XiaohongshuClient(
            cookies=os.getenv("XHS_COOKIES"),
            openai_client=_openai_client  # ✨ 传递 OpenAI client 用于 LLM 解析
        )
        post = await client.fetch_post(post_url)

        _current_paper = {
            "post_id": post.post_id,
            "post_url": str(post.post_url),
            "blogger_name": post.blogger_name,
            "raw_content": post.raw_content,
        }

        elapsed = time.time() - start_time
        logger.info(
            "✅ 小红书帖子获取成功",
            post_id=post.post_id,
            content_length=len(post.raw_content),
            elapsed_time=f"{elapsed:.2f}s"
        )

        return json.dumps({
            "success": True,
            "post_id": post.post_id,
            "content": post.raw_content,
            "message": f"✅ 帖子内容获取成功！（耗时 {elapsed:.2f}s）"
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(
            "❌ 小红书帖子获取失败",
            error=str(e),
            elapsed_time=f"{elapsed:.2f}s"
        )
        return json.dumps({
            "success": False,
            "error": f"获取帖子失败: {str(e)}"
        }, ensure_ascii=False, indent=2)


@function_tool
async def extract_paper_metadata(
    xiaohongshu_content: Annotated[str, "小红书帖子内容（可选）"] = "",
    pdf_content: Annotated[str, "PDF的文本内容"] = "",
    pdf_metadata: Annotated[str, "PDF的元数据（JSON格式）"] = ""
) -> str:
    """
    从 PDF 和小红书内容中提取所有论文信息（一次 LLM 调用）

    参数:
        xiaohongshu_content: 小红书帖子内容（可选）
        pdf_content: PDF 文本内容
        pdf_metadata: PDF 元数据 (JSON格式)

    返回:
        JSON格式的完整论文信息，包括：
        - title: 论文英文标题
        - authors: 作者列表（数组）
        - publication_date: 发表日期（YYYY-MM-DD）
        - venue: 期刊/会议名称
        - abstract: 摘要
        - affiliations: 机构
        - keywords: 关键词列表（数组）
        - doi: DOI
        - arxiv_id: ArXiv ID
        - project_page: 项目主页
        - other_resources: 其他资源
    """
    global _openai_client, _current_paper
    start_time = time.time()

    try:
        logger.info("📚 开始提取论文元数据（LLM 调用 1/2）")
        prompt = f"""你是论文信息提取专家。请从以下内容中提取完整的论文信息。

# PDF 元数据
{pdf_metadata}

# PDF 内容（前5000字）
{pdf_content[:5000] if pdf_content else "[未提供]"}

# 小红书内容（参考）
{xiaohongshu_content[:2000] if xiaohongshu_content else "[未提供]"}

请提取以下信息，必须返回 JSON 格式：

{{
    "title": "论文英文标题（必填）",
    "authors": ["作者1", "作者2"],
    "publication_date": "YYYY-MM-DD（如果只有年份，使用 YYYY-01-01）",
    "venue": "期刊/会议名称",
    "abstract": "英文摘要",
    "affiliations": "Stanford University; MIT",
    "keywords": ["keyword1", "keyword2", "tag1"],
    "doi": "10.1234/example（如果有）",
    "arxiv_id": "2410.xxxxx（如果是 arXiv 论文）",
    "project_page": "项目主页链接（如果有）",
    "other_resources": "代码仓库、数据集等（可用分号分隔）"
}}

⚠️ 要求：
1. title 必须提取，其他字段没有信息可以设为 null
2. publication_date 必须是完整的 YYYY-MM-DD 格式
3. authors 和 keywords 必须是数组格式
4. 其他字段可以是字符串或数组，设置为可用的格式
5. 如果信息不足，使用 null 值
"""

        response = await _openai_client.chat.completions.create(
            model="gpt-5-mini",
            messages=[{
                "role": "system",
                "content": "你是专业的论文信息提取专家。你必须准确完整地提取论文的所有元数据。"
            }, {
                "role": "user",
                "content": prompt
            }],
            response_format={"type": "json_object"}
        )

        extracted_info = json.loads(response.choices[0].message.content)

        # 验证必填字段
        if not extracted_info.get("title"):
            extracted_info["title"] = "Unknown Paper"

        _current_paper.update(extracted_info)

        elapsed = time.time() - start_time
        logger.info(
            "✅ 论文元数据提取成功",
            title=extracted_info.get("title", "Unknown"),
            authors_count=len(extracted_info.get("authors", [])),
            keywords_count=len(extracted_info.get("keywords", [])),
            elapsed_time=f"{elapsed:.2f}s"
        )

        return json.dumps({
            "success": True,
            **extracted_info,
            "message": f"✅ 论文信息提取成功（标题 + 元数据）！（耗时 {elapsed:.2f}s）"
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(
            "❌ 论文元数据提取失败",
            error=str(e),
            elapsed_time=f"{elapsed:.2f}s"
        )
        return json.dumps({
            "success": False,
            "error": f"提取失败: {str(e)}"
        }, ensure_ascii=False, indent=2)


@function_tool
async def search_arxiv_pdf(
    paper_title: Annotated[str, "论文标题"]
) -> str:
    """
    在 arXiv 搜索论文 PDF 链接

    参数:
        paper_title: 论文标题

    返回:
        JSON格式的PDF链接信息
    """
    start_time = time.time()
    try:
        import urllib.parse

        logger.info("🔎 开始在 arXiv 搜索论文", paper_title=paper_title[:100])

        # arXiv API 搜索
        query = urllib.parse.quote(paper_title)
        api_url = f"http://export.arxiv.org/api/query?search_query=ti:{query}&max_results=3"

        proxy = os.getenv('http_proxy')
        mounts = None
        if proxy:
            mounts = {
                "http://": httpx.AsyncHTTPTransport(proxy=proxy),
                "https://": httpx.AsyncHTTPTransport(proxy=proxy),
            }

        async with httpx.AsyncClient(timeout=30.0, mounts=mounts) as client:
            response = await client.get(api_url)
            response.raise_for_status()

            # 解析 XML 响应
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)

            # 查找第一个匹配的论文
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            entries = root.findall('atom:entry', ns)

            if entries:
                entry = entries[0]
                # 获取 arXiv ID
                arxiv_id_elem = entry.find('atom:id', ns)
                if arxiv_id_elem is not None:
                    arxiv_id_full = arxiv_id_elem.text
                    # 提取 ID 部分（例如：http://arxiv.org/abs/2410.04618 -> 2410.04618）
                    arxiv_id = arxiv_id_full.split('/abs/')[-1]
                    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

                    # 获取标题确认
                    title_elem = entry.find('atom:title', ns)
                    found_title = title_elem.text.strip() if title_elem is not None else "Unknown"

                    elapsed = time.time() - start_time
                    logger.info(
                        "✅ arXiv 搜索成功",
                        arxiv_id=arxiv_id,
                        found_title=found_title[:100],
                        elapsed_time=f"{elapsed:.2f}s"
                    )

                    return json.dumps({
                        "success": True,
                        "pdf_url": pdf_url,
                        "arxiv_id": arxiv_id,
                        "arxiv_abs_url": f"https://arxiv.org/abs/{arxiv_id}",
                        "found_title": found_title,
                        "message": f"✅ 在 arXiv 找到论文！（耗时 {elapsed:.2f}s）\nPDF: {pdf_url}\narXiv ID: {arxiv_id}"
                    }, ensure_ascii=False, indent=2)

        # 未找到
        elapsed = time.time() - start_time
        logger.warning(
            "⚠️ arXiv 未找到论文",
            paper_title=paper_title[:100],
            elapsed_time=f"{elapsed:.2f}s"
        )
        return json.dumps({
            "success": False,
            "error": f"在 arXiv 未找到论文《{paper_title}》。可能不是 arXiv 论文，或标题不完全匹配。"
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(
            "❌ arXiv 搜索失败",
            error=str(e),
            elapsed_time=f"{elapsed:.2f}s"
        )
        return json.dumps({
            "success": False,
            "error": f"arXiv 搜索失败: {str(e)}"
        }, ensure_ascii=False, indent=2)


@function_tool
async def download_pdf_from_url(
    pdf_url: Annotated[str, "PDF文件的URL"],
    paper_title: Annotated[str, "论文标题（用于命名文件）"] = "paper"
) -> str:
    """
    下载 PDF 并读取全部内容

    参数:
        pdf_url: PDF 文件的 URL
        paper_title: 论文标题

    返回:
        包含 PDF 内容和元数据的 JSON
    """
    global _current_paper
    start_time = time.time()

    try:
        logger.info("📥 开始下载 PDF", pdf_url=pdf_url[:100], paper_title=paper_title[:50])

        # 清理文件名
        safe_title = paper_title[:50].replace('/', '_').replace(':', '_').replace('?', '_')
        local_path = PDF_DIR / f"{safe_title}.pdf"

        # 下载 PDF
        proxy = os.getenv('http_proxy')
        mounts = None
        if proxy:
            mounts = {
                "http://": httpx.AsyncHTTPTransport(proxy=proxy),
                "https://": httpx.AsyncHTTPTransport(proxy=proxy),
            }

        async with httpx.AsyncClient(
            timeout=60.0,
            follow_redirects=True,
            mounts=mounts
        ) as client:
            response = await client.get(pdf_url)
            response.raise_for_status()

            with open(local_path, 'wb') as f:
                f.write(response.content)

        # 读取 PDF 内容
        logger.info("📖 开始读取 PDF 内容")
        pdf_content, pdf_metadata = _read_pdf_file(str(local_path))

        _current_paper["pdf_path"] = str(local_path)
        _current_paper["pdf_url"] = pdf_url
        _current_paper["pdf_content"] = pdf_content
        _current_paper["pdf_metadata"] = pdf_metadata

        elapsed = time.time() - start_time
        logger.info(
            "✅ PDF 下载并读取成功",
            file_size=f"{len(response.content) / 1024 / 1024:.2f}MB",
            pages=pdf_metadata.get("pages", 0),
            content_length=len(pdf_content),
            elapsed_time=f"{elapsed:.2f}s"
        )

        return json.dumps({
            "success": True,
            "local_path": str(local_path),
            "pdf_url": pdf_url,
            "pdf_content": pdf_content[:5000],  # 返回前5000字符预览
            "pdf_metadata": json.dumps(pdf_metadata, ensure_ascii=False),
            "message": f"✅ PDF 下载并读取成功！文件: {local_path}（耗时 {elapsed:.2f}s）"
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(
            "❌ PDF 下载失败",
            error=str(e),
            elapsed_time=f"{elapsed:.2f}s"
        )
        return json.dumps({
            "success": False,
            "error": f"处理失败: {str(e)}"
        }, ensure_ascii=False, indent=2)


@function_tool
async def read_local_pdf(
    pdf_path: Annotated[str, "PDF文件的本地路径"]
) -> str:
    """
    读取本地 PDF 文件内容

    参数:
        pdf_path: PDF 文件的本地路径

    返回:
        包含 PDF 内容和元数据的 JSON
    """
    global _current_paper
    start_time = time.time()

    try:
        logger.info("📖 开始读取本地 PDF", pdf_path=pdf_path)

        pdf_content, pdf_metadata = _read_pdf_file(pdf_path)

        _current_paper["pdf_path"] = pdf_path
        _current_paper["pdf_content"] = pdf_content
        _current_paper["pdf_metadata"] = pdf_metadata

        elapsed = time.time() - start_time
        file_size = os.path.getsize(pdf_path) / 1024 / 1024 if os.path.exists(pdf_path) else 0
        logger.info(
            "✅ 本地 PDF 读取成功",
            pdf_path=pdf_path,
            file_size=f"{file_size:.2f}MB",
            pages=pdf_metadata.get("pages", 0),
            content_length=len(pdf_content),
            elapsed_time=f"{elapsed:.2f}s"
        )

        return json.dumps({
            "success": True,
            "pdf_path": pdf_path,
            "pdf_content": pdf_content[:5000],
            "pdf_metadata": json.dumps(pdf_metadata, ensure_ascii=False),
            "message": f"✅ PDF 读取成功！文件: {pdf_path}（耗时 {elapsed:.2f}s）"
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(
            "❌ 本地 PDF 读取失败",
            error=str(e),
            elapsed_time=f"{elapsed:.2f}s"
        )
        return json.dumps({
            "success": False,
            "error": f"读取失败: {str(e)}"
        }, ensure_ascii=False, indent=2)


def _read_pdf_file(pdf_path: str):
    """读取 PDF 文件内容和元数据（内部函数）"""
    doc = fitz.open(pdf_path)
    total_pages = doc.page_count

    # 提取元数据
    metadata = doc.metadata
    metadata_dict = {
        "title": metadata.get("title", ""),
        "author": metadata.get("author", ""),
        "subject": metadata.get("subject", ""),
        "keywords": metadata.get("keywords", ""),
        "creator": metadata.get("creator", ""),
        "producer": metadata.get("producer", ""),
        "creationDate": metadata.get("creationDate", ""),
        "modDate": metadata.get("modDate", ""),
        "pages": total_pages,
    }

    # 分批读取全部内容（每次10页）
    PAGES_PER_BATCH = 10
    all_pdf_text = []
    current_page = 0

    while current_page < total_pages:
        end_page = min(current_page + PAGES_PER_BATCH, total_pages)
        batch_text = ""

        for page_num in range(current_page, end_page):
            page = doc[page_num]
            batch_text += f"\n\n--- Page {page_num + 1} ---\n\n"
            batch_text += page.get_text()

        all_pdf_text.append(batch_text)
        current_page = end_page

    doc.close()

    # 合并所有内容
    full_pdf_content = "".join(all_pdf_text)

    # 截断到合理长度（~50000字符）
    MAX_CHARS = 50000
    if len(full_pdf_content) > MAX_CHARS:
        pdf_content = full_pdf_content[:MAX_CHARS] + "\n\n[内容已截断，后续内容略]"
    else:
        pdf_content = full_pdf_content

    return pdf_content, metadata_dict






@function_tool
async def generate_paper_digest(
    xiaohongshu_content: Annotated[str, "小红书帖子内容"] = "",
    paper_title: Annotated[str, "论文标题"] = "",
    pdf_content: Annotated[str, "PDF全文内容"] = "",
    authors: Annotated[str, "作者列表（JSON数组字符串）"] = "[]",
    publication_date: Annotated[str, "发表日期（YYYY-MM-DD）"] = "",
    venue: Annotated[str, "期刊/会议名称"] = "",
    abstract: Annotated[str, "摘要"] = "",
    affiliations: Annotated[str, "机构"] = "",
    keywords: Annotated[str, "关键词列表（JSON数组字符串）"] = "[]",
    project_page: Annotated[str, "项目主页"] = "",
    other_resources: Annotated[str, "其他资源"] = "",
) -> str:
    """
    生成结构化论文整理

    参数:
        xiaohongshu_content: 小红书帖子内容
        paper_title: 论文标题
        pdf_content: PDF 全文内容
        authors: 作者列表
        publication_date: 发表日期
        venue: 期刊/会议
        abstract: 摘要
        affiliations: 机构
        keywords: 关键词
        project_page: 项目主页
        other_resources: 其他资源

    返回:
        Markdown格式的论文整理
    """
    global _openai_client, _current_paper
    start_time = time.time()

    # 读取模板
    template_path = Path(__file__).parent / "digest_template.md"
    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()

    try:
        logger.info("✍️ 开始生成论文整理（LLM 调用 2/2）", paper_title=paper_title[:100])
        prompt = f"""
你是论文整理专家。请根据以下信息，按照模板生成高质量的论文整理。

# 论文基本信息
- **标题**: {paper_title}
- **作者**: {authors}
- **机构**: {affiliations}
- **发表时间**: {publication_date}
- **期刊/会议**: {venue}
- **标签**: {keywords}
- **项目页**: {project_page if project_page else "[无]"}
- **其他资源**: {other_resources if other_resources else "[无]"}

# 小红书内容（参考）
{xiaohongshu_content}

# 论文摘要
{abstract if abstract else "[未提取到摘要]"}

# PDF 全文内容（重点参考）
{pdf_content[:20000] if pdf_content else "[未提供PDF内容]"}

# 整理模板
{template_content}

# 要求（⚠️ 严格执行）
1. **必须严格按照模板结构**，包含所有章节
2. **优先使用 PDF 全文内容**，其次参考小红书内容
3. **详细填充以下章节**：
   - 文章背景与基本观点
   - 现有解决方案的思路与问题
   - 本文提出的思想与方法
   - 方法实现细节
   - 方法有效性证明（实验）
   - 局限性与未来方向
4. **如果信息不足**，明确标注 "[信息不足]"
5. **保持学术性和专业性**
6. **使用 Markdown 格式**
7. **基本信息必须准确填写**（包括完整日期、标签、项目页、其他资源）

请输出完整的论文整理（Markdown格式）：
"""

        response = await _openai_client.chat.completions.create(
            model="gpt-5-mini",  # 使用 gpt-5-mini，大上下文窗口
            messages=[{
                "role": "system",
                "content": "你是专业的论文整理专家，擅长结构化整理学术论文。你必须详细、完整地填充论文整理模板的所有章节。"
            }, {
                "role": "user",
                "content": prompt
            }],
        )

        digest_content = response.choices[0].message.content

        # 保存到文件
        safe_title = paper_title[:50].replace('/', '_').replace(':', '_') if paper_title else "paper"
        output_file = OUTPUT_DIR / f"{safe_title}.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(digest_content)

        _current_paper["digest_content"] = digest_content
        _current_paper["digest_file"] = str(output_file)

        elapsed = time.time() - start_time
        logger.info(
            "✅ 论文整理生成成功",
            paper_title=paper_title[:100],
            content_length=len(digest_content),
            output_file=str(output_file),
            elapsed_time=f"{elapsed:.2f}s"
        )

        return json.dumps({
            "success": True,
            "output_file": str(output_file),
            "digest_content": digest_content,
            "message": f"✅ 论文整理生成成功！文件: {output_file}（耗时 {elapsed:.2f}s）"
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(
            "❌ 论文整理生成失败",
            error=str(e),
            elapsed_time=f"{elapsed:.2f}s"
        )
        return json.dumps({
            "success": False,
            "error": f"生成失败: {str(e)}"
        }, ensure_ascii=False, indent=2)


@function_tool
async def save_digest_to_notion(
    paper_title: Annotated[str, "论文标题"],
    digest_content: Annotated[str, "论文整理内容（Markdown格式）"],
    source_url: Annotated[str, "来源URL"] = "",
    pdf_url: Annotated[str, "PDF链接"] = "",
    authors: Annotated[str, "作者列表（JSON数组字符串或逗号分隔）"] = "",
    affiliations: Annotated[str, "机构"] = "",
    publication_date: Annotated[str, "发表日期（YYYY-MM-DD格式）"] = "",
    venue: Annotated[str, "期刊/会议名称"] = "",
    abstract: Annotated[str, "摘要"] = "",
    keywords: Annotated[str, "关键词（JSON数组字符串或逗号分隔）"] = "",
    doi: Annotated[str, "DOI"] = "",
    arxiv_id: Annotated[str, "ArXiv ID"] = "",
    project_page: Annotated[str, "项目主页"] = "",
    other_resources: Annotated[str, "其他资源（代码仓库、数据集等）"] = "",
) -> str:
    """
    将论文整理保存到 Notion

    参数:
        paper_title: 论文标题
        digest_content: 论文整理内容
        source_url: 来源链接
        pdf_url: PDF链接
        authors: 作者
        affiliations: 机构
        publication_date: 发表日期
        venue: 期刊/会议
        abstract: 摘要
        keywords: 关键词
        doi: DOI
        arxiv_id: ArXiv ID
        project_page: 项目主页
        other_resources: 其他资源

    返回:
        保存结果
    """
    from notion_client import AsyncClient
    start_time = time.time()

    try:
        logger.info("💾 开始保存论文整理到 Notion", paper_title=paper_title[:100])
        client = AsyncClient(auth=os.getenv('NOTION_TOKEN'))

        # 构建 properties
        properties = {
            "Name": {
                "title": [{"text": {"content": paper_title[:2000]}}]
            }
        }

        # Authors - 处理 JSON 数组或逗号分隔字符串
        if authors:
            try:
                authors_list = json.loads(authors) if authors.startswith('[') else [a.strip() for a in authors.split(',')]
                authors_str = ", ".join(authors_list)
                properties["Authors"] = {"rich_text": [{"text": {"content": authors_str[:2000]}}]}
            except:
                properties["Authors"] = {"rich_text": [{"text": {"content": authors[:2000]}}]}

        if affiliations:
            properties["Affiliations"] = {"rich_text": [{"text": {"content": affiliations[:2000]}}]}
        if venue:
            properties["Venue"] = {"rich_text": [{"text": {"content": venue[:2000]}}]}

        # Abstract - 使用中文摘要（从 digest_content 提取）
        if abstract:
            chinese_abstract = _extract_chinese_abstract(digest_content)
            if chinese_abstract:
                properties["Abstract"] = {"rich_text": [{"text": {"content": chinese_abstract[:2000]}}]}

        # Keywords - multi_select 类型
        if keywords:
            try:
                keywords_list = json.loads(keywords) if keywords.startswith('[') else [k.strip() for k in keywords.split(',')]
                properties["Keywords"] = {"multi_select": [{"name": kw} for kw in keywords_list[:10]]}  # Notion 限制
            except:
                pass

        # DOI
        if doi:
            properties["DOI"] = {"rich_text": [{"text": {"content": doi[:2000]}}]}

        # ArXiv ID
        if arxiv_id:
            properties["ArXiv ID"] = {"rich_text": [{"text": {"content": arxiv_id[:2000]}}]}

        # Publication Date - date 类型
        if publication_date:
            try:
                # 验证日期格式 YYYY-MM-DD
                if len(publication_date) == 10 and publication_date[4] == '-' and publication_date[7] == '-':
                    properties["Publication Date"] = {"date": {"start": publication_date}}
            except:
                pass

        # Other Resources - rich_text 类型
        if other_resources:
            properties["Other Resources"] = {"rich_text": [{"text": {"content": other_resources[:2000]}}]}

        # 转换 Markdown 为 Notion blocks
        blocks = _markdown_to_notion_blocks(digest_content)

        response = await client.pages.create(
            parent={"database_id": os.getenv('NOTION_DATABASE_ID')},
            properties=properties,
            children=blocks[:100],
        )

        page_id = response["id"]
        page_url = f"https://notion.so/{page_id.replace('-', '')}"

        await client.aclose()

        elapsed = time.time() - start_time
        logger.info(
            "✅ 论文整理已保存到 Notion",
            paper_title=paper_title[:100],
            page_id=page_id,
            page_url=page_url,
            properties_count=len(properties),
            blocks_count=len(blocks[:100]),
            elapsed_time=f"{elapsed:.2f}s"
        )

        return json.dumps({
            "success": True,
            "page_id": page_id,
            "page_url": page_url,
            "message": f"✅ 论文整理已保存到 Notion！（耗时 {elapsed:.2f}s）\n\n查看链接: {page_url}"
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(
            "❌ 保存到 Notion 失败",
            error=str(e),
            elapsed_time=f"{elapsed:.2f}s"
        )
        return json.dumps({
            "success": False,
            "error": f"保存失败: {str(e)}"
        }, ensure_ascii=False, indent=2)


def _extract_chinese_abstract(digest_content: str) -> str:
    """从生成的中文论文整理中提取摘要部分"""
    import re

    patterns = [
        r'##\s*📝\s*摘要\s*\(.*?\)\s*\n+(.*?)(?=\n##|\n---|\Z)',
        r'##\s*摘要\s*\(.*?\)\s*\n+(.*?)(?=\n##|\n---|\Z)',
        r'##\s*摘要\s*\n+(.*?)(?=\n##|\n---|\Z)',
    ]

    for pattern in patterns:
        match = re.search(pattern, digest_content, re.DOTALL)
        if match:
            abstract = match.group(1).strip()
            # Clean markdown formatting
            abstract = re.sub(r'\*\*(.+?)\*\*', r'\1', abstract)
            abstract = re.sub(r'\*(.+?)\*', r'\1', abstract)
            abstract = ' '.join(abstract.split())
            return abstract[:2000]

    # Fallback: 使用前200字符
    return digest_content[:200].replace('#', '').strip()


def _markdown_to_notion_blocks(markdown_text: str) -> list:
    """
    将 Markdown 转换为 Notion API blocks

    使用 mistletoe 解析 Markdown 并转换为 Notion blocks
    支持：加粗、斜体、删除线、内联代码、嵌套列表等

    Args:
        markdown_text: Markdown 文本

    Returns:
        Notion API blocks 列表
    """
    try:
        # 使用相对导入
        from .notion_markdown_converter import markdown_to_notion_blocks

        blocks = markdown_to_notion_blocks(markdown_text)
        return blocks
    except Exception as e:
        # 如果转换失败，记录错误并返回空列表
        import traceback
        print(f"Markdown转换失败: {e}")
        traceback.print_exc()
        return []


# Digest Agent 定义
digest_agent = Agent(
    name="digest_agent",
    instructions="""你是论文深度整理专家（Digest Agent）。⚡ 仅需 2 次 LLM 调用，大幅加速！

你的职责是接收论文相关信息，完成以下任务：

## 执行流程（仅需 2 次 LLM 调用！）

**第一阶段：获取 PDF 并提取所有元数据**
1. **获取论文内容**
   - 如果提供了小红书 URL，使用 fetch_xiaohongshu_post 获取内容
   - 如果提供了 PDF URL，使用 download_pdf_from_url 下载
   - 如果提供了本地 PDF 路径，使用 read_local_pdf 读取

2. **搜索论文 PDF**（如果没有提供 PDF URL）
   - 优先使用 search_arxiv_pdf 在 arXiv 搜索论文
   - 从搜索结果中获取 PDF URL 和 arXiv ID

3. **⚡ 一次 LLM 调用提取所有元数据**（替代旧的两个单独调用）
   - 使用 extract_paper_metadata **一次调用同时提取**：
     * 论文标题（title）
     * 作者（authors）
     * 发表日期（publication_date，YYYY-MM-DD）
     * 期刊/会议（venue）
     * 摘要（abstract）
     * 机构（affiliations）
     * 关键词（keywords）
     * DOI
     * ArXiv ID
     * 项目页（project_page）
     * 其他资源（other_resources）
   - ⚠️ 必须传入 xiaohongshu_content、pdf_content、pdf_metadata

**第二阶段：生成论文整理并保存**
4. **⚡ 一次 LLM 调用生成完整论文整理**
   - 使用 generate_paper_digest 生成结构化的中文论文整理
   - 传入所有提取的元数据
   - 必须包含所有模板章节，内容详细

5. **保存到 Notion**
   - 使用 save_digest_to_notion 保存整理内容和所有元数据
   - ⚠️ **必须传递 extract_paper_metadata 返回的所有字段**：
     * paper_title - 论文标题
     * digest_content - 生成的论文整理内容
     * source_url - 小红书 URL（如果有）
     * pdf_url - PDF 链接
     * authors - 作者列表（JSON 数组字符串）
     * affiliations - 机构
     * publication_date - 完整发表日期（YYYY-MM-DD）
     * venue - 期刊/会议名称
     * abstract - 英文摘要
     * keywords - 关键词列表（JSON 数组字符串）
     * doi - DOI（如果有）
     * arxiv_id - ArXiv ID（如果有）
     * project_page - 项目主页（如果有）
     * other_resources - 其他资源（如果有）

⚠️ 关键要求：
- ✅ **只进行 2 次 LLM 调用**（extract_paper_metadata 一次，generate_paper_digest 一次）
- ✅ 不再使用已删除的函数
- ✅ 必须严格按照顺序执行
- ✅ 每个步骤都要检查结果是否成功
- ✅ 元信息必须准确且完整
- ✅ 调用 save_digest_to_notion 时传递所有字段（特别是 authors 和 keywords 要转为 JSON 数组字符串）
- ❌ 如果某个步骤失败，报告错误并停止

你专注于论文整理工作，不处理定时任务相关的事情。
""",
    model="gpt-5",
    tools=[
        fetch_xiaohongshu_post,
        search_arxiv_pdf,
        download_pdf_from_url,
        read_local_pdf,
        extract_paper_metadata,  # ✨ 新的合并函数（替代旧的两个）
        generate_paper_digest,
        save_digest_to_notion,
    ]
)
