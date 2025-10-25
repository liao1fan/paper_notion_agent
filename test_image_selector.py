#!/usr/bin/env python3
"""
测试图片选择器

测试场景：
1. 从提取的图片中选择最重要的图片
2. 验证选择的图片和 caption
3. 检查 caption 包含的关键信息
"""

import sys
from pathlib import Path

# 添加 src 到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from src.services.image_selector import ImageSelector, select_important_images


def test_image_selector():
    """测试图片选择器"""

    print("\n" + "=" * 80)
    print("图片选择器测试")
    print("=" * 80 + "\n")

    # 模拟图片数据
    mock_images = [
        {
            "filename": "page2_img0.png",
            "caption": "Figure 1: System Architecture Diagram showing the complete pipeline",
            "page": 2,
            "width": 800,
            "height": 600,
            "total_pages": 20
        },
        {
            "filename": "page3_img0.png",
            "caption": "Experimental Results Comparison",
            "page": 3,
            "width": 600,
            "height": 400,
            "total_pages": 20
        },
        {
            "filename": "page5_img0.jpeg",
            "caption": "",  # 无 caption
            "page": 5,
            "width": 300,
            "height": 200,
            "total_pages": 20
        },
        {
            "filename": "page8_img0.png",
            "caption": "Figure 2: The proposed method shows 3x speedup",
            "page": 8,
            "width": 700,
            "height": 500,
            "total_pages": 20
        },
        {
            "filename": "page10_img0.png",
            "caption": "Performance metrics across different datasets",
            "page": 10,
            "width": 650,
            "height": 450,
            "total_pages": 20
        },
        {
            "filename": "page12_img0.png",
            "caption": "Sample workflow example",
            "page": 12,
            "width": 500,
            "height": 350,
            "total_pages": 20
        },
        {
            "filename": "page14_img0.png",
            "caption": "Framework comparison with baseline methods",
            "page": 14,
            "width": 750,
            "height": 550,
            "total_pages": 20
        },
        {
            "filename": "page15_img0.png",
            "caption": "Ablation study results showing importance of each component",
            "page": 15,
            "width": 700,
            "height": 480,
            "total_pages": 20
        },
        {
            "filename": "page18_img0.png",
            "caption": "Additional implementation details",
            "page": 18,
            "width": 400,
            "height": 300,
            "total_pages": 20
        }
    ]

    # 创建选择器
    selector = ImageSelector(max_images=6)

    # 为每张图片评分
    print("评分详情：")
    print("-" * 80)
    print(f"{'图片文件':<25} {'Caption':<35} {'评分':<8}")
    print("-" * 80)

    scored = []
    for img in mock_images:
        score = selector.score_image(img)
        scored.append((img, score))
        caption_preview = img.get('caption', '(无)')[:32]
        print(f"{img['filename']:<25} {caption_preview:<35} {score:>6.2f}")

    # 按评分排序
    scored.sort(key=lambda x: x[1], reverse=True)

    print()
    print("排序结果（从高到低）：")
    print("-" * 80)
    for i, (img, score) in enumerate(scored, 1):
        caption = img.get('caption', '(无)')
        print(f"{i}. {img['filename']:<25} 分数: {score:>6.2f}")
        print(f"   Caption: {caption}")
        print()

    # 选择前 6 张
    selected = select_important_images(mock_images, max_images=6)

    print("=" * 80)
    print(f"最终选中的图片（共 {len(selected)} 张）：")
    print("=" * 80)
    for i, img in enumerate(selected, 1):
        caption = img.get('caption', '(无)')
        print(f"\n{i}. {img['filename']}")
        print(f"   页码: {img.get('page', 'unknown')}")
        print(f"   尺寸: {img.get('width', 'unknown')} x {img.get('height', 'unknown')}")
        print(f"   Caption: {caption}")

    print()
    print("=" * 80)
    print("✅ 测试完成！")
    print("=" * 80)
    print()


def test_with_real_pdf():
    """使用真实 PDF 测试"""

    from src.services.pdf_image_extractor import PDFImageExtractor
    from pathlib import Path

    pdf_path = Path("paper_digest/pdfs/Agentic Context Engineering_ Evolving Contexts for.pdf")

    if not pdf_path.exists():
        print(f"❌ PDF 文件不存在: {pdf_path}")
        return

    print("\n" + "=" * 80)
    print("真实 PDF 图片选择测试")
    print("=" * 80 + "\n")

    # 提取图片
    output_dir = Path("./test_output/image_selector_test")
    output_dir.mkdir(parents=True, exist_ok=True)

    extractor = PDFImageExtractor(str(output_dir))
    images, _ = extractor.extract(str(pdf_path))

    print(f"提取了 {len(images)} 张图片\n")

    # 选择重要图片
    selected = select_important_images(images, max_images=6)

    print("=" * 80)
    print(f"最终选中 {len(selected)} 张重要图片：")
    print("=" * 80)

    for i, img in enumerate(selected, 1):
        caption = img.get('caption', '(无)')
        score = ImageSelector().score_image(img)
        print(f"\n{i}. {img['filename']}")
        print(f"   页码: {img['page']}")
        print(f"   尺寸: {img['width']} x {img['height']}")
        print(f"   评分: {score:.2f}")
        print(f"   Caption: {caption[:60]}{'...' if len(caption) > 60 else ''}")


if __name__ == "__main__":
    # 运行测试
    test_image_selector()
    test_with_real_pdf()
