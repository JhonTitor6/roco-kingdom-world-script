"""Dot检测集成测试 - 验证inactive/active dot检测逻辑"""
import pytest
import numpy as np
import cv2
from pathlib import Path
from PIL import Image
from unittest.mock import MagicMock, patch
import time

from win_util.controller import WinController


# 测试数据：(图片名, 我方inactive期望值, 敌方inactive期望值)
TEST_CASES = [
    ("洛克王国：世界   2026_4_3 21_39_20.png", 0, 1),
    ("洛克王国：世界   2026_4_3 21_39_54.png", 0, 3),
    ("洛克王国：世界   2026_4_3 21_45_15.png", 0, 0),
    ("洛克王国：世界   2026_4_3 23_35_23.png", 1, 3),
    ("洛克王国：世界   2026_4_6 14_33_43.png", 0, 1),
    ("洛克王国：世界   2026_4_11 12_41_37.png", 3, 2),
    ("洛克王国：世界   2026_4_10 23_31_52.png", 3, 0),
    ("洛克王国：世界   2026_4_6 16_17_07.png", 0, 3),
]


def imread_unicode(path: Path) -> np.ndarray:
    """解决中文路径问题"""
    img = Image.open(path)
    img = img.convert('RGB')
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)


def save_debug_image(img: np.ndarray, name: str, matches: list, region: tuple, template_size: tuple) -> Path:
    """保存带匹配标记的调试图片

    Args:
        img: 原始截图
        name: 保存文件名前缀
        matches: 匹配位置列表 [(x, y), ...]
        region: 区域 (x0, y0, x1, y1)
        template_size: 模板尺寸 (w, h)
    """
    debug_dir = Path("logs/debug")
    debug_dir.mkdir(parents=True, exist_ok=True)

    # 复制图片用于标记
    debug_img = img.copy()

    # 在原图上标记区域
    x0, y0, x1, y1 = region
    cv2.rectangle(debug_img, (x0, y0), (x1, y1), (255, 255, 0), 2)

    # 标记匹配位置（在原图坐标系中）
    for mx, my in matches:
        cv2.rectangle(debug_img, (mx, my), (mx + template_size[0], my + template_size[1]), (0, 255, 0), 2)

    # 裁剪区域放大显示
    crop_img = img[y0:y1, x0:x1]
    if crop_img.size > 0:
        # 放大2倍便于观察
        h, w = crop_img.shape[:2]
        crop_img = cv2.resize(crop_img, (w * 2, h * 2))

    # 拼接原图标记和区域裁剪（需要相同高度）
    if crop_img.size > 0:
        h = min(debug_img.shape[0], crop_img.shape[0])
        debug_img = cv2.resize(debug_img, (800, h))
        crop_img = cv2.resize(crop_img, (crop_img.shape[1], h))
        debug_img = cv2.hconcat([debug_img, crop_img])

    timestamp = int(time.time() * 1000)
    filename = f"{name}_{timestamp}.png"
    filepath = debug_dir / filename
    cv2.imwrite(str(filepath), debug_img)
    print(f"\n调试图片已保存: {filepath}")
    return filepath


class TestDotDetection:
    """Dot检测测试"""

    @pytest.fixture
    def inactive_template(self, templates_dir):
        """加载inactive dot模板路径"""
        template_path = templates_dir / "dots" / "dot_inactive.png"
        if not template_path.exists():
            pytest.skip(f"模板不存在: {template_path}")
        return str(template_path)

    @pytest.fixture
    def controller(self):
        """创建WinController实例用于测试（mock掉ScreenCapture避免窗口依赖）"""
        with patch('win_util.image.ScreenCapture') as mock_capture:
            mock_capture_instance = MagicMock()
            mock_capture.return_value = mock_capture_instance
            mock_capture_instance.capture_window_region.return_value = None
            controller = WinController()
            controller.image_finder.screenshot_cache = None
            return controller

    @pytest.mark.parametrize("image_name,expected_ally,expected_enemy", TEST_CASES)
    def test_inactive_dot_detection(self, images_dir, inactive_template, controller, image_name, expected_ally, expected_enemy):
        """参数化测试：检测inactive dot

        Args:
            image_name: 测试图片名
            expected_ally: 我方inactive dots期望值
            expected_enemy: 敌方inactive dots期望值
        """
        screenshot_path = images_dir / image_name
        if not screenshot_path.exists():
            pytest.skip(f"测试截图不存在: {screenshot_path}")

        screenshot = imread_unicode(screenshot_path)

        # 定义区域（竖屏2560x1440）
        ally_region = (141, 132, 329, 166)   # 左上
        enemy_region = (2300, 132, 2490, 166)  # 右上

        controller.image_finder.screenshot_cache = screenshot

        ally_matches = controller.find_images_all(inactive_template,
                                                 x0=ally_region[0], y0=ally_region[1],
                                                 x1=ally_region[2], y1=ally_region[3],
                                                 similarity=0.8)
        enemy_matches = controller.find_images_all(inactive_template,
                                                  x0=enemy_region[0], y0=enemy_region[1],
                                                  x1=enemy_region[2], y1=enemy_region[3],
                                                  similarity=0.8)

        ally_positions = [(x, y) for x, y, _ in ally_matches]
        enemy_positions = [(x, y) for x, y, _ in enemy_matches]

        ally_count = len(ally_positions)
        enemy_count = len(enemy_positions)

        print(f"\n图片: {image_name}")
        print(f"我方区域 inactive dots: {ally_count} (期望: {expected_ally})")
        print(f"敌方区域 inactive dots: {enemy_count} (期望: {expected_enemy})")
        print(f"匹配位置 - 我方: {ally_positions}, 敌方: {enemy_positions}")

        # 保存调试图片
        template = cv2.imread(inactive_template)
        template_size = (template.shape[1], template.shape[0]) if template is not None else (0, 0)
        safe_name = image_name.replace("：", "_").replace(" ", "_")
        save_debug_image(screenshot, f"inactive_{safe_name}_ally", ally_positions, ally_region, template_size)
        save_debug_image(screenshot, f"inactive_{safe_name}_enemy", enemy_positions, enemy_region, template_size)

        assert ally_count == expected_ally, f"图片 {image_name} 我方inactive dots检测异常: 检测到{ally_count}, 期望{expected_ally}"
        assert enemy_count == expected_enemy, f"图片 {image_name} 敌方inactive dots检测异常: 检测到{enemy_count}, 期望{expected_enemy}"
