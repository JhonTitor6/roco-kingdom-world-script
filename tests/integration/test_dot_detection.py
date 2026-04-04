"""Dot检测集成测试 - 验证inactive/active dot检测逻辑"""
import pytest
import numpy as np
import cv2
from pathlib import Path
from PIL import Image
import time


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


def match_template_nms(img: np.ndarray, template: np.ndarray, threshold: float = 0.9995, distance_threshold: float = 10) -> list:
    """模板匹配 + 简单距离去重

    Args:
        img: 待搜索图像
        template: 模板图像
        threshold: 匹配阈值 (默认0.9995，高置信度避免误检测)
        distance_threshold: 曼哈顿距离阈值，小于此值认为是重复检测

    Returns:
        匹配位置列表 [(x, y), ...]
    """
    result = cv2.matchTemplate(img, template, cv2.TM_CCORR_NORMED)
    locations = np.where(result >= threshold)
    matches = [(x, y, result[y, x]) for x, y in zip(locations[1], locations[0])]

    if not matches:
        return []

    # 按置信度降序排序
    matches.sort(key=lambda m: m[2], reverse=True)

    # 简单去重：曼哈顿距离超过阈值视为新点
    unique_points = []
    for x, y, conf in matches:
        is_duplicate = False
        for ux, uy in unique_points:
            if abs(x - ux) <= distance_threshold and abs(y - uy) <= distance_threshold:
                is_duplicate = True
                break
        if not is_duplicate:
            unique_points.append((x, y))

    return unique_points


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
        """加载inactive dot模板"""
        template_path = templates_dir / "dots" / "dot_inactive.png"
        if not template_path.exists():
            pytest.skip(f"模板不存在: {template_path}")
        return imread_unicode(template_path)

    @pytest.fixture
    def active_template(self, templates_dir):
        """加载active dot模板"""
        template_path = templates_dir / "dots" / "dot_active.png"
        if not template_path.exists():
            pytest.skip(f"模板不存在: {template_path}")
        return imread_unicode(template_path)

    @pytest.fixture
    def screenshot(self, screenshot_path):
        """加载截图"""
        return imread_unicode(screenshot_path)

    def test_inactive_dot_detection_in_regions(self, screenshot, inactive_template):
        """测试在指定区域内检测inactive dot

        根据VLM分析（用户确认）：
        - 我方（左上）：1个死亡
        - 敌方（右上）：3个死亡
        """
        # 定义区域（竖屏2560x1440）
        ally_region = (136, 132, 332, 168)   # 左上
        enemy_region = (2297, 132, 2494, 168)  # 右上

        # 裁剪区域
        ally_img = screenshot[ally_region[1]:ally_region[3], ally_region[0]:ally_region[2]]
        enemy_img = screenshot[enemy_region[1]:enemy_region[3], enemy_region[0]:enemy_region[2]]

        # 模板匹配
        ally_matches = match_template_nms(ally_img, inactive_template, threshold=0.9)
        enemy_matches = match_template_nms(enemy_img, inactive_template, threshold=0.9)

        ally_count = len(ally_matches)
        enemy_count = len(enemy_matches)

        print(f"\n我方区域 inactive dots: {ally_count}")
        print(f"敌方区域 inactive dots: {enemy_count}")
        print(f"匹配位置 - 我方: {ally_matches}, 敌方: {enemy_matches}")

        # 保存调试图片
        template_size = (inactive_template.shape[1], inactive_template.shape[0])
        save_debug_image(screenshot, "inactive_ally", ally_matches, ally_region, template_size)
        save_debug_image(screenshot, "inactive_enemy", enemy_matches, enemy_region, template_size)

        # 基于当前截图和cv2 NMS的实际检测结果，禁止修改期望值
        assert ally_count == 1, f"我方inactive dots检测异常: {ally_count}"
        assert enemy_count == 3, f"敌方inactive dots检测异常: {enemy_count}"

    def test_active_dot_detection_in_regions(self, screenshot, active_template):
        """测试在指定区域内检测active dot"""
        ally_region = (136, 132, 332, 168)   # 左上
        enemy_region = (2297, 132, 2494, 168)  # 右上

        ally_img = screenshot[ally_region[1]:ally_region[3], ally_region[0]:ally_region[2]]
        enemy_img = screenshot[enemy_region[1]:enemy_region[3], enemy_region[0]:enemy_region[2]]

        ally_matches = match_template_nms(ally_img, active_template)
        enemy_matches = match_template_nms(enemy_img, active_template)

        ally_count = len(ally_matches)
        enemy_count = len(enemy_matches)

        print(f"\n我方区域 active dots: {ally_count}")
        print(f"敌方区域 active dots: {enemy_count}")
        print(f"匹配位置 - 我方: {ally_matches}, 敌方: {enemy_matches}")

        # 保存调试图片
        template_size = (active_template.shape[1], active_template.shape[0])
        save_debug_image(screenshot, "active_ally", ally_matches, ally_region, template_size)
        save_debug_image(screenshot, "active_enemy", enemy_matches, enemy_region, template_size)

        # 基于当前截图和cv2 NMS的实际检测结果，禁止修改期望值
        assert ally_count == 3, f"我方active dots检测异常: {ally_count}"
        assert enemy_count == 1, f"敌方active dots检测异常: {enemy_count}"

    def test_screenshot_and_template_sizes(self, screenshot, inactive_template, active_template):
        """验证截图和模板尺寸"""
        print(f"\n截图尺寸: {screenshot.shape}")
        print(f"inactive模板尺寸: {inactive_template.shape}")
        print(f"active模板尺寸: {active_template.shape}")

        assert screenshot is not None
        assert inactive_template is not None
        assert active_template is not None
