"""游戏控制器 - 封装 win_util"""
from pathlib import Path
from typing import Optional, Tuple, List
import time

from loguru import logger
from win_util import WinController

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

    def find_image(self, template_path: str, similarity: float = None) -> Tuple[int, int]:
        """在截图缓存中查找图像

        Args:
            template_path: 相对于 TEMPLATE_BASE 的路径
            similarity: 相似度阈值

        Returns:
            (x, y) 坐标，未找到返回 (-1, -1)
        """
        sim = similarity or self._similarity
        full_path = self.TEMPLATE_BASE / template_path

        # 更新截图
        self.capture()

        result = self.win.image_finder.bg_find_pic_by_cache(
            str(full_path),
            similarity=sim
        )

        if result == (-1, -1):
            logger.debug(f"图像未找到: {template_path}")
            return -1, -1

        logger.debug(f"图像找到: {template_path} @ {result}")
        return result

    def find_image_with_timeout(
        self, template_path: str, timeout: float = 5, similarity: float = None
    ) -> Optional[Tuple[int, int]]:
        """等待图像出现

        Args:
            template_path: 模板路径
            timeout: 超时时间（秒）
            similarity: 相似度

        Returns:
            (x, y) 或 None
        """
        start = time.time()
        while time.time() - start < timeout:
            pos = self.find_image(template_path, similarity)
            if pos != (-1, -1):
                return pos
            time.sleep(0.3)
        return None

    def wait_for_image_disappear(
        self, template_path: str, timeout: float = 5, similarity: float = None
    ) -> bool:
        """等待图像消失"""
        start = time.time()
        while time.time() - start < timeout:
            pos = self.find_image(template_path, similarity)
            if pos == (-1, -1):
                return True
            time.sleep(0.3)
        return False

    def click_at(self, x: int, y: int, x_range: int = 20, y_range: int = 20) -> bool:
        """在指定位置点击"""
        return self.win.mouse.bg_left_click((x, y), x_range=x_range, y_range=y_range)

    def find_and_click(self, template_path: str, similarity: float = None) -> bool:
        """查找图像并点击"""
        pos = self.find_image(template_path, similarity)
        if pos == (-1, -1):
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
