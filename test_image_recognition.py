"""测试图像识别功能 - 使用 cv2.matchTemplate"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

import cv2
import numpy as np
from PIL import Image

# 截图文件目录
IMAGES_DIR = Path(__file__).parent / "images"
TEMPLATES_DIR = Path(__file__).parent / "assets" / "templates"


def imread_unicode(path: Path) -> np.ndarray:
    """解决中文路径问题"""
    img = Image.open(path)
    img = img.convert('RGB')
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)


def find_template(screenshot: np.ndarray, template_path: Path, similarity: float = 0.8) -> tuple:
    """在截图中查找模板"""
    template = cv2.imread(str(template_path))
    if template is None:
        return (-1, -1), 0.0

    # 模板匹配
    result = cv2.matchTemplate(screenshot, template, cv2.TM_CCORR_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    if max_val >= similarity:
        # 返回中心点坐标
        h, w = template.shape[:2]
        center_x = max_loc[0] + w // 2
        center_y = max_loc[1] + h // 2
        return (center_x, center_y), max_val

    return (-1, -1), 0.0


def test_on_screenshot(screenshot_path: Path, templates: list, similarity: float = 0.8):
    """在指定截图中测试模板匹配"""
    print(f"\n{'='*60}")
    print(f"测试截图: {screenshot_path.name}")
    print(f"{'='*60}")

    screenshot = imread_unicode(screenshot_path)
    if screenshot is None:
        print(f"  [错误] 无法加载截图")
        return

    h, w = screenshot.shape[:2]
    print(f"  截图尺寸: {w}x{h}")

    results = []
    for template_path in templates:
        (x, y), sim = find_template(screenshot, template_path, similarity)
        if x != -1:
            results.append((template_path.name, x, y, sim))

    # 输出结果
    if results:
        print(f"\n  找到 {len(results)} 个匹配:")
        for name, x, y, sim in sorted(results, key=lambda r: r[0]):
            print(f"    {name:<30} @ ({x:>4}, {y:>4})  相似度: {sim:.4f}")
    else:
        print("\n  未找到任何匹配")

    return results


def main():
    import os
    screenshots = [Path(IMAGES_DIR / f) for f in os.listdir(IMAGES_DIR) if f.endswith('.png')]
    screenshots.sort(key=lambda p: p.stat().st_mtime)

    if not screenshots:
        print(f"错误: 在 {IMAGES_DIR} 中未找到截图文件")
        return

    templates = sorted(TEMPLATES_DIR.rglob("*.png"))
    if not templates:
        print(f"错误: 在 {TEMPLATES_DIR} 中未找到模板文件")
        return

    print(f"找到 {len(templates)} 个模板，{len(screenshots)} 张截图")
    print(f"\n模板列表:")
    for t in templates:
        print(f"  - {t.relative_to(TEMPLATES_DIR)}")

    for screenshot in screenshots:
        test_on_screenshot(screenshot, templates, similarity=0.75)

    print(f"\n{'='*60}")
    print("测试完成")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
