"""
PDF 图片和 Caption 提取模块

功能：
1. 从 PDF 中提取所有图片（保留原始格式）
2. 识别图片位置和关联的 caption
3. 保存图片文件，返回结构化元数据
4. 维护原始 block 顺序用于 Markdown 生成
"""

import fitz  # PyMuPDF
from pathlib import Path
from typing import Dict, List, Tuple
import json
import logging

# 尝试导入 PIL 用于图片处理
try:
    from PIL import Image, ImageDraw, ImageChops
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

logger = logging.getLogger(__name__)


class PDFImageExtractor:
    """PDF 图片提取器"""

    def __init__(self, output_dir: str = "./paper_digest/images"):
        """
        初始化提取器

        Args:
            output_dir: 图片保存目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.processed_xrefs = set()  # 跟踪已处理的图片 xref，避免重复

    def extract(self, pdf_path: str) -> Tuple[List[Dict], List[Dict]]:
        """
        完整提取：图片文件 + block 顺序信息

        Args:
            pdf_path: PDF 文件路径

        Returns:
            images: 图片元数据列表
                [
                    {
                        "filename": "page1_img0.png",
                        "local_path": "/path/to/page1_img0.png",
                        "page": 1,
                        "xref": 5,
                        "width": 800,
                        "height": 600,
                        "format": "png",
                        "caption": "Figure 1: ...",
                        "bbox": (100, 200, 900, 800)
                    },
                    ...
                ]
            blocks: 按顺序保存的所有 block（文本+图片）
                [
                    {"type": "text", "page": 1, "bbox": (0, 0, 800, 100), "content": "..."},
                    {"type": "image", "page": 1, "bbox": (100, 200, 900, 800), "image_ref": "page1_img0.png"},
                    ...
                ]
        """
        doc = fitz.open(pdf_path)
        all_images = []
        all_blocks = []
        self.processed_xrefs.clear()

        try:
            for page_num in range(len(doc)):
                page = doc[page_num]

                # 获取页面结构化内容
                page_dict = page.get_text("dict")
                page_blocks = page_dict.get("blocks", [])

                # 1. 先扫描一遍找到所有图片，用于 caption 查找
                image_info_map = {}  # xref -> {bbox, ...}
                for block in page_blocks:
                    if block["type"] == 1:  # 图片块
                        xref = block.get("xref")
                        if xref:
                            image_info_map[xref] = block.get("bbox")

                # 2. 遍历所有 block，维护顺序
                for block in page_blocks:
                    bbox = block.get("bbox")

                    if block["type"] == 0:  # 文本块
                        text = self._extract_text_from_block(block)
                        if text.strip():  # 只保存非空文本
                            all_blocks.append({
                                "type": "text",
                                "page": page_num + 1,
                                "bbox": bbox,
                                "content": text
                            })

                    elif block["type"] == 1:  # 图片块
                        # 直接从 block 中获取图片数据
                        if "image" not in block:
                            continue

                        xref = block.get("xref")
                        # 跟踪 xref 避免重复，如果没有 xref 则用索引跟踪
                        block_id = xref if xref else f"page{page_num}_idx{len(all_images)}"
                        if block_id in self.processed_xrefs:
                            continue

                        self.processed_xrefs.add(block_id)

                        # 从 block 直接提取图片文件，传递 PDF 文档对象以正确处理颜色空间
                        img_info = self._extract_image_from_block(block, page_num, doc)
                        if not img_info:
                            continue

                        # 查找 caption
                        caption = self._find_caption_for_image(
                            page_blocks,
                            block,
                            page_dict.get("width"),
                            page_dict.get("height")
                        )
                        img_info["caption"] = caption

                        all_images.append(img_info)

                        # 添加到 block 序列
                        all_blocks.append({
                            "type": "image",
                            "page": page_num + 1,
                            "bbox": bbox,
                            "image_ref": img_info["filename"],  # 用于关联
                            "caption": caption
                        })

        finally:
            doc.close()

        logger.info(
            f"✅ PDF 图片提取完成 - 提取 {len(all_images)} 张图片, {len(all_blocks)} 个 blocks"
        )

        return all_images, all_blocks

    def _extract_text_from_block(self, block: Dict) -> str:
        """从文本块提取内容"""
        lines = []
        for line in block.get("lines", []):
            line_text = ""
            for span in line.get("spans", []):
                line_text += span.get("text", "")
            if line_text.strip():
                lines.append(line_text.strip())
        return "\n".join(lines)

    def _extract_image_from_block(self, block: Dict, page_num: int, pdf_doc=None) -> Dict:
        """
        从 block 直接提取单张图片文件，并修复颜色空间问题

        Args:
            block: PyMuPDF 的图片 block 字典
            page_num: 页码（0-indexed）
            pdf_doc: PDF 文档对象，用于正确提取图片

        Returns:
            图片元数据字典，如果失败返回 None
        """
        try:
            if "image" not in block:
                return None

            xref = block.get("xref", 0)
            image_ext = block.get("ext", "png")
            width = block.get("width", 0)
            height = block.get("height", 0)

            # 优先使用 PDF 文档对象正确提取图片，避免颜色空间问题
            image_bytes = None
            if pdf_doc and xref:
                try:
                    # 使用 PyMuPDF 的 extract_image 方法确保正确的颜色处理
                    image_data = pdf_doc.extract_image(xref)
                    if image_data:
                        image_bytes = image_data["image"]
                        # 尝试获取正确的扩展名
                        if "ext" in image_data:
                            image_ext = image_data["ext"]
                        logger.debug(f"使用 extract_image 方法提取图片: xref={xref}")
                except Exception as e:
                    logger.debug(f"extract_image 方法失败: {e}，使用 block 数据")
                    image_bytes = None

            # 如果上述方法失败，使用 block 中的图片数据
            if image_bytes is None:
                image_bytes = block["image"]
                logger.debug(f"使用 block 数据提取图片: xref={xref}")

            # 尝试修复黑色背景问题（如果 PIL 可用）
            if HAS_PIL:
                fixed_bytes = self._fix_black_background_image(image_bytes, image_ext)
                if len(fixed_bytes) != len(image_bytes):
                    image_bytes = fixed_bytes
                    logger.info(f"✅ 修复了黑色背景问题: xref={xref}")

            # 保存图片文件
            image_filename = f"page{page_num + 1}_img{xref}.{image_ext}"
            image_path = self.output_dir / image_filename

            with open(image_path, "wb") as f:
                f.write(image_bytes)

            logger.info(f"✅ 图片已保存: {image_filename}")

            return {
                "filename": image_filename,
                "local_path": str(image_path),
                "page": page_num + 1,
                "xref": xref,
                "width": width,
                "height": height,
                "format": image_ext,
                "bbox": block.get("bbox"),
            }

        except Exception as e:
            logger.error(f"提取图片失败: {e}")
            return None

    @staticmethod
    def _fix_black_background_image(image_bytes: bytes, image_ext: str) -> bytes:
        """
        修复全黑背景的图片（PDF 颜色空间问题）

        当 PDF 中的某些图片提取出来是全黑时，可能是：
        1. Alpha 通道反转
        2. 颜色空间编码问题
        3. 图片使用了特殊的索引颜色

        尝试修复这些问题

        Args:
            image_bytes: 图片原始数据
            image_ext: 图片格式

        Returns:
            修复后的图片字节数据（如果修复失败则返回原始数据）
        """
        if not HAS_PIL:
            return image_bytes

        try:
            from io import BytesIO

            # 打开图片
            img = Image.open(BytesIO(image_bytes))

            # 检查是否是全黑或几乎全黑（可能是反转的 Alpha）
            import numpy as np
            img_array = np.array(img.convert('RGB'))
            avg_brightness = img_array.mean()

            # 如果平均亮度太低（接近黑色），尝试修复
            if avg_brightness < 30:  # 全黑或接近全黑
                logger.warning(f"检测到全黑图片，尝试修复颜色空间...")

                # 方案 1: 反转颜色（可能是 Alpha 通道反转）
                try:
                    inverted = ImageChops.invert(img.convert('RGB'))
                    inverted_array = np.array(inverted)
                    inverted_brightness = inverted_array.mean()

                    if inverted_brightness > 150:  # 反转后变成白色背景
                        logger.info("✅ 通过颜色反转修复黑色背景")
                        # 保存修复后的图片
                        output = BytesIO()
                        inverted.save(output, format=image_ext.upper())
                        return output.getvalue()
                except Exception as e:
                    logger.debug(f"颜色反转失败: {e}")

                # 方案 2: 提取 Alpha 通道作为主图
                try:
                    if img.mode == 'RGBA':
                        alpha = img.split()[3]  # 获取 Alpha 通道
                        alpha_array = np.array(alpha)
                        alpha_brightness = alpha_array.mean()

                        if alpha_brightness > 150:  # Alpha 通道是白色
                            logger.info("✅ 使用 Alpha 通道作为主图")
                            output = BytesIO()
                            alpha.convert('RGB').save(output, format=image_ext.upper())
                            return output.getvalue()
                except Exception as e:
                    logger.debug(f"Alpha 通道提取失败: {e}")

            return image_bytes

        except Exception as e:
            logger.debug(f"图片颜色修复失败: {e}，使用原始数据")
            return image_bytes

    def _find_caption_for_image(
        self,
        blocks: List[Dict],
        image_block: Dict,
        page_width: float = 595,  # A4 默认宽度
        page_height: float = 842   # A4 默认高度
    ) -> str:
        """
        查找图片的 caption（启发式方法）

        启发式规则：
        1. Caption 通常在图片正下方
        2. 垂直距离 < 50 像素
        3. 包含 "Figure", "Fig.", "图", "Table", "表" 等关键词
        4. 水平对齐：至少 50% 重叠
        """
        img_bbox = image_block.get("bbox", (0, 0, 0, 0))
        img_x0, img_y0, img_x1, img_y1 = img_bbox

        caption_candidates = []

        for block in blocks:
            if block["type"] != 0:  # 不是文本块
                continue

            text_bbox = block.get("bbox", (0, 0, 0, 0))
            text_x0, text_y0, text_x1, text_y1 = text_bbox

            # 检查文本是否在图片正下方
            is_below = text_y0 >= img_y1
            vertical_distance = text_y0 - img_y1 if is_below else float('inf')

            # 距离阈值：50 像素
            if not is_below or vertical_distance > 50:
                continue

            # 检查水平对齐（至少 50% 重叠）
            horizontal_overlap = min(img_x1, text_x1) - max(img_x0, text_x0)
            image_width = img_x1 - img_x0
            overlap_ratio = horizontal_overlap / image_width if image_width > 0 else 0

            if overlap_ratio < 0.5:
                continue

            # 提取文本内容
            text = block.get("text", "")
            if not text.strip():
                continue

            # 检查是否包含 caption 关键词
            text_lower = text.lower()
            caption_keywords = ["figure", "fig.", "图", "table", "表", "图表"]

            has_keyword = any(kw in text_lower for kw in caption_keywords)
            if not has_keyword:
                continue

            # 是一个候选 caption
            caption_candidates.append({
                "text": text,
                "distance": vertical_distance,
                "overlap_ratio": overlap_ratio,
            })

        # 选择最佳候选（距离最近的）
        if caption_candidates:
            best_caption = min(caption_candidates, key=lambda x: x["distance"])
            return best_caption["text"].strip()

        return ""

    def to_json(self, images: List[Dict], output_file: str = None) -> str:
        """
        将提取的图片信息保存为 JSON

        Args:
            images: 图片元数据列表
            output_file: 输出文件路径，如果为 None，输出到 output_dir/images.json

        Returns:
            JSON 字符串
        """
        if output_file is None:
            output_file = self.output_dir / "images.json"

        output_file = Path(output_file)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(images, f, ensure_ascii=False, indent=2)

        logger.info(f"图片元数据已保存到: {output_file}")

        return json.dumps(images, ensure_ascii=False, indent=2)


# ========== 便捷函数 ==========

def extract_pdf_images(pdf_path: str, output_dir: str = None) -> Tuple[List[Dict], List[Dict]]:
    """
    便捷函数：一行代码提取 PDF 图片

    Args:
        pdf_path: PDF 文件路径
        output_dir: 图片保存目录，如果为 None 使用默认值

    Returns:
        (images, blocks)
    """
    if output_dir is None:
        output_dir = "./paper_digest/images"

    extractor = PDFImageExtractor(output_dir)
    return extractor.extract(pdf_path)
