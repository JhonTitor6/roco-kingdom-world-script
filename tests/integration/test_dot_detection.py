"""Dot检测集成测试 - 验证inactive/active dot检测逻辑"""
import pytest
import numpy as np
import cv2
from pathlib import Path
from PIL import Image
from unittest.mock import MagicMock, patch
import time

from win_util.controller import WinController


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
    def screenshot_path(self, images_dir):
        """获取特定测试截图"""
        target = images_dir / "洛克王国：世界   2026_4_3 23_35_23.png"
        if not target.exists():
            pytest.skip(f"测试截图不存在: {target}")
        return target

    @pytest.fixture
    def inactive_template(self, templates_dir):
        """加载inactive dot模板路径"""
        template_path = templates_dir / "dots" / "dot_inactive.png"
        if not template_path.exists():
            pytest.skip(f"模板不存在: {template_path}")
        return str(template_path)

    @pytest.fixture
    def active_template(self, templates_dir):
        """加载active dot模板路径"""
        template_path = templates_dir / "dots" / "dot_active.png"
        if not template_path.exists():
            pytest.skip(f"模板不存在: {template_path}")
        return str(template_path)

    @pytest.fixture
    def screenshot(self, screenshot_path):
        """加载截图"""
        return imread_unicode(screenshot_path)

    @pytest.fixture
    def controller(self):
        """创建WinController实例用于测试（mock掉ScreenCapture避免窗口依赖）"""
        with patch('win_util.image.ScreenCapture') as mock_capture:
            mock_capture_instance = MagicMock()
            mock_capture.return_value = mock_capture_instance
            mock_capture_instance.capture_window_region.return_value = None
            controller = WinController()
            # 强制设置screenshot_cache为None
            controller.image_finder.screenshot_cache = None
            return controller

    def test_inactive_dot_detection_in_regions(self, screenshot, inactive_template, controller):
        """测试在指定区域内检测inactive dot

        根据VLM分析（用户确认）：
        - 我方（左上）：1个死亡
        - 敌方（右上）：3个死亡
        """
        # 定义区域（竖屏2560x1440）
        ally_region = (141, 132, 329, 166)   # 左上
        enemy_region = (2300, 132, 2490, 166)  # 右上

        # 设置screenshot_cache为测试截图，使bg_find_pic_all_by_cache能使用
        controller.image_finder.screenshot_cache = screenshot

        # 使用WinController.find_images_all进行模板匹配
        ally_matches = controller.find_images_all(inactive_template,
                                                 x0=ally_region[0], y0=ally_region[1],
                                                 x1=ally_region[2], y1=ally_region[3],
                                                 similarity=0.8)
        enemy_matches = controller.find_images_all(inactive_template,
                                                  x0=enemy_region[0], y0=enemy_region[1],
                                                  x1=enemy_region[2], y1=enemy_region[3],
                                                  similarity=0.8)

        # 提取位置信息
        ally_positions = [(x, y) for x, y, _ in ally_matches]
        enemy_positions = [(x, y) for x, y, _ in enemy_matches]

        ally_count = len(ally_positions)
        enemy_count = len(enemy_positions)

        print(f"\n我方区域 inactive dots: {ally_count}")
        print(f"敌方区域 inactive dots: {enemy_count}")
        print(f"匹配位置 - 我方: {ally_positions}, 敌方: {enemy_positions}")

        # 保存调试图片
        template = cv2.imread(inactive_template)
        template_size = (template.shape[1], template.shape[0]) if template is not None else (0, 0)
        save_debug_image(screenshot, "inactive_ally", ally_positions, ally_region, template_size)
        save_debug_image(screenshot, "inactive_enemy", enemy_positions, enemy_region, template_size)

        # 基于当前截图和cv2 NMS的实际检测结果，禁止修改期望值
        assert ally_count == 1, f"我方inactive dots检测异常: {ally_count}"
        assert enemy_count == 3, f"敌方inactive dots检测异常: {enemy_count}"

    def test_active_dot_detection_in_regions(self, screenshot, active_template, controller):
        """测试在指定区域内检测active dot"""
        ally_region = (136, 132, 332, 168)   # 左上
        enemy_region = (2297, 132, 2494, 168)  # 右上

        # 设置screenshot_cache为测试截图
        controller.image_finder.screenshot_cache = screenshot

        ally_matches = controller.find_images_all(active_template,
                                                 x0=ally_region[0], y0=ally_region[1],
                                                 x1=ally_region[2], y1=ally_region[3],
                                                 similarity=0.8)
        enemy_matches = controller.find_images_all(active_template,
                                                  x0=enemy_region[0], y0=enemy_region[1],
                                                  x1=enemy_region[2], y1=enemy_region[3],
                                                  similarity=0.8)

        ally_positions = [(x, y) for x, y, _ in ally_matches]
        enemy_positions = [(x, y) for x, y, _ in enemy_matches]

        ally_count = len(ally_positions)
        enemy_count = len(enemy_positions)

        print(f"\n我方区域 active dots: {ally_count}")
        print(f"敌方区域 active dots: {enemy_count}")
        print(f"匹配位置 - 我方: {ally_positions}, 敌方: {enemy_positions}")

        # 保存调试图片
        template = cv2.imread(active_template)
        template_size = (template.shape[1], template.shape[0]) if template is not None else (0, 0)
        save_debug_image(screenshot, "active_ally", ally_positions, ally_region, template_size)
        save_debug_image(screenshot, "active_enemy", enemy_positions, enemy_region, template_size)

        # 基于当前截图和cv2 NMS的实际检测结果，禁止修改期望值
        assert ally_count == 3, f"我方active dots检测异常: {ally_count}"
        assert enemy_count == 1, f"敌方active dots检测异常: {enemy_count}"

    def test_screenshot_and_template_sizes(self, screenshot, inactive_template, active_template):
        """验证截图和模板尺寸"""
        inactive_img = cv2.imread(inactive_template)
        active_img = cv2.imread(active_template)

        print(f"\n截图尺寸: {screenshot.shape}")
        print(f"inactive模板尺寸: {inactive_img.shape if inactive_img is not None else 'None'}")
        print(f"active模板尺寸: {active_img.shape if active_img is not None else 'None'}")

        assert screenshot is not None
        assert inactive_img is not None
        assert active_img is not None
