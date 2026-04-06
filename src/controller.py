"""游戏控制器 - 封装 win_util"""
from pathlib import Path
from typing import Optional, Tuple, List, Union
import time

from src.utils import random_sleep
from loguru import logger
from win_util import WinController
from win_util.mouse import left_click

from src.exceptions import ImageNotFoundError


class GameController:
    """封装 win_util 的游戏控制器"""

    # 模板基础路径
    TEMPLATE_BASE = Path(__file__).parent.parent / "assets" / "templates"

    def __init__(self, hwnd: int, settings: dict):
        self.hwnd = hwnd
        self.settings = settings
        self.win = WinController(hwnd=hwnd)
        self._similarity = settings.get("similarity", 0.8)

    def capture(self) -> None:
        """更新截图缓存"""
        self.win.update_screenshot_cache()

    def get_screenshot(self):
        """获取当前截图"""
        return self.win.image_finder.screenshot_cache

    def _find_single_image(
        self,
        template_path: str,
        similarity: float = None,
        x0: int = 0,
        y0: int = 0,
        x1: int = 99999,
        y1: int = 99999,
    ) -> Tuple[int, int]:
        """查找单个模板图像

        Args:
            template_path: 相对于 TEMPLATE_BASE 的路径
            similarity: 相似度阈值
            x0: 区域左上角x坐标
            y0: 区域左上角y坐标
            x1: 区域右下角x坐标
            y1: 区域右下角y坐标

        Returns:
            (x, y) 坐标，未找到返回 (-1, -1)
        """
        sim = similarity or self._similarity
        full_path = self.TEMPLATE_BASE / template_path

        result = self.win.image_finder.bg_find_pic_by_cache(
            str(full_path), x0, y0, x1, y1, similarity=sim
        )

        if result == (-1, -1):
            logger.debug(f"图像未找到: {template_path}")
            return -1, -1

        logger.debug(f"图像找到: {template_path} @ {result}")
        return result

    def find_image(
        self,
        template,
        similarity: float = None,
        x0: int = 0,
        y0: int = 0,
        x1: int = 99999,
        y1: int = 99999,
        _capture: bool = True,
    ) -> Tuple[int, int]:
        """在截图缓存中查找图像

        Args:
            template: 相对于 TEMPLATE_BASE 的路径，支持单字符串或字符串列表
            similarity: 相似度阈值
            x0: 区域左上角x坐标
            y0: 区域左上角y坐标
            x1: 区域右下角x坐标
            y1: 区域右下角y坐标
            _capture: 是否在查找前更新截图，默认 True

        Returns:
            (x, y) 坐标，未找到返回 (-1, -1)
        """
        # 更新截图
        if _capture:
            self.capture()

        # 兼容单字符串和列表
        templates = [template] if isinstance(template, str) else template

        for t in templates:
            pos = self._find_single_image(t, similarity, x0, y0, x1, y1)
            if pos != (-1, -1):
                return pos
        return -1, -1

    def find_image_with_timeout(
        self,
        template,
        timeout: float = 5,
        similarity: float = None,
        x0: int = 0,
        y0: int = 0,
        x1: int = 99999,
        y1: int = 99999,
    ) -> Optional[Tuple[int, int]]:
        """等待图像出现

        Args:
            template: 模板路径，支持单字符串或字符串列表
            timeout: 超时时间（秒）
            similarity: 相似度
            x0: 区域左上角x坐标
            y0: 区域左上角y坐标
            x1: 区域右下角x坐标
            y1: 区域右下角y坐标

        Returns:
            (x, y) 或 None
        """
        start = time.time()
        while time.time() - start < timeout:
            pos = self.find_image(template, similarity, x0, y0, x1, y1)
            if pos != (-1, -1):
                return pos
            random_sleep(0.3)
        return None

    def wait_for_image_disappear(
        self, template: Union[str, List[str]], timeout: float = 5, similarity: float = None
    ) -> bool:
        """等待图像消失"""
        start = time.time()
        while time.time() - start < timeout:
            pos = self.find_image(template, similarity)
            if pos == (-1, -1):
                return True
            random_sleep(0.3)
        return False

    def click_at(self, x: int, y: int, x_range: int = 10, y_range: int = 10) -> bool:
        """在指定位置点击（前台点击）"""
        # 添加随机偏移模拟人工点击
        import random
        offset_x = random.randint(-x_range, x_range) if x_range > 0 else 0
        offset_y = random.randint(-y_range, y_range) if y_range > 0 else 0
        return left_click((x + offset_x, y + offset_y))

    def find_and_click(self, template: Union[str, List[str]], similarity: float = None) -> bool:
        """查找图像并点击（立即返回）"""
        pos = self.find_image(template, similarity)
        if pos == (-1, -1):
            return False
        return self.click_at(*pos)

    def find_and_click_with_timeout(
        self, template: Union[str, List[str]], timeout: float = 5, similarity: float = None
    ) -> bool:
        """等待图像出现后点击

        Args:
            template: 模板路径，支持单字符串或字符串列表
            timeout: 超时时间（秒）
            similarity: 相似度阈值

        Returns:
            是否成功找到并点击
        """
        pos = self.find_image_with_timeout(template, timeout=timeout, similarity=similarity)
        if pos is None:
            return False
        return self.click_at(*pos)

    def press_key(self, key: str) -> None:
        """按键"""
        self.win.keyboard.bg_press_key(key)

    def ocr_text(self, image) -> List[str]:
        """OCR 识别文本"""
        return self.win.ocr.find_all_texts(image)

    def find_text_position(self, text: str, similarity: float = 0.3) -> Optional[Tuple[int, int]]:
        """查找文本位置"""
        screenshot = self.get_screenshot()
        if screenshot is None:
            return None
        return self.win.ocr.find_text_position(screenshot, text, similarity_threshold=similarity)

    def save_debug_screenshot(self, name: str) -> Path:
        """保存调试截图"""
        import cv2
        screenshot = self.get_screenshot()
        if screenshot is None:
            return None
        debug_dir = Path(__file__).parent.parent / "logs" / "debug"
        debug_dir.mkdir(exist_ok=True)
        path = debug_dir / f"{name}_{int(time.time())}.png"
        cv2.imwrite(str(path), screenshot)
        logger.debug(f"调试截图已保存: {path}")
        return path

    def find_images_all(
        self,
        template: Union[str, List[str]],
        similarity: float = None,
        x0: int = 0,
        y0: int = 0,
        x1: int = 99999,
        y1: int = 99999
    ) -> List[Tuple[int, int]]:
        """查找所有匹配的图像

        Args:
            template: 相对于 TEMPLATE_BASE 的路径，支持单字符串或字符串列表
            similarity: 相似度阈值
            x0, y0: 搜索区域左上角
            x1, y1: 搜索区域右下角

        Returns:
            匹配位置的列表 [(x1, y1), (x2, y2), ...]，未找到返回空列表
        """
        sim = similarity or self._similarity
        self.capture()

        # 兼容单字符串和列表
        templates = [template] if isinstance(template, str) else template

        results = []
        for t in templates:
            full_path = self.TEMPLATE_BASE / t
            matches = self.win.image_finder.bg_find_pic_all_by_cache(
                str(full_path),
                x0=x0, y0=y0, x1=x1, y1=y1,
                similarity=sim
            )
            results.extend(matches)

        logger.debug(f"找到 {len(results)} 个匹配: {template} @ {results}")
        return results
