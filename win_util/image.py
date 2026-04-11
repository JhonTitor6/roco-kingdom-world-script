import time
from ctypes import windll
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, List, Tuple, Union, Any, Optional

import cv2
import numpy as np
import win32gui
import win32ui
from PIL import ImageGrab
from loguru import logger

if TYPE_CHECKING:
    try:
        from tests.common.environment.base import GameEnvironment
    except ImportError:
        GameEnvironment = None  # type: ignore

debug_img_base_dir = Path("yys/images/debug")

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def to_project_path(path: str) -> str:
    p = Path(path)
    # 绝对路径：不动
    if p.is_absolute():
        return str(p)
    return str(PROJECT_ROOT / p)


def match_template_nms(matches: List[Tuple[int, int, float]], distance_threshold: float = 10) -> List[Tuple[int, int, float]]:
    """模板匹配结果去重（曼哈顿距离）

    Args:
        matches: 匹配结果列表 [(x, y, score), ...]
        distance_threshold: 曼哈顿距离阈值，小于此值认为是重复检测

    Returns:
        去重后的匹配结果列表
    """
    if not matches:
        return []

    # 按置信度降序排序
    matches.sort(key=lambda m: m[2], reverse=True)

    # 简单去重：曼哈顿距离超过阈值视为新点
    unique_points = []
    for x, y, score in matches:
        is_duplicate = False
        for ux, uy, _ in unique_points:
            if abs(x - ux) <= distance_threshold and abs(y - uy) <= distance_threshold:
                is_duplicate = True
                break
        if not is_duplicate:
            unique_points.append((x, y, score))

    return unique_points


class ScreenCapture:
    """
    窗口截图和区域截图封装

    支持两种模式：
    1. hwnd 模式：使用原生 win32 调用截取窗口画面
    2. env 模式：使用 GameEnvironment 接口截取画面
    """

    def __init__(self, hwnd: Optional[int] = None, env: Optional['GameEnvironment'] = None, save_source_img=False):
        """
        初始化截图器

        :param hwnd: 窗口句柄（向后兼容）
        :param env: GameEnvironment 实例
        :param save_source_img: 是否保存原始截图
        """
        self.hwnd = hwnd
        self._env = env
        self.save_source_img = save_source_img

    def capture_window_region(self, x0=0, y0=0, x1=99999, y1=99999) -> np.ndarray:
        """
        捕获窗口指定区域

        :param x0: 区域左上角x坐标
        :param y0: 区域左上角y坐标
        :param x1: 区域右下角x坐标
        :param y1: 区域右下角y坐标
        :return: numpy 数组格式的 BGR 图像
        """
        # 优先使用 GameEnvironment 接口
        if self._env is not None:
            pil_img = self._env.capture_screen()
            # 将 PIL Image 转换为 numpy 数组
            img = np.array(pil_img.convert('RGB'))
            img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            h, w = img_bgr.shape[:2]
            x1 = min(x1, w)
            y1 = min(y1, h)
            return img_bgr[y0:y1, x0:x1]

        # 向后兼容：使用原生 win32 调用
        if self.hwnd is None:
            raise ValueError("请在初始化时传入 hwnd 或 env 参数")

        client_rect = win32gui.GetClientRect(self.hwnd)
        client_width = client_rect[2] - client_rect[0]
        client_height = client_rect[3] - client_rect[1]

        x0 = max(x0, client_rect[0])
        y0 = max(y0, client_rect[1])
        x1 = min(x1, client_width)
        y1 = min(y1, client_height)

        if x0 >= x1 or y0 >= y1:
            raise ValueError(f"无效区域: ({x0}, {y0}) - ({x1}, {y1})")

        hwnd_dc = win32gui.GetWindowDC(self.hwnd)
        mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
        save_dc = mfc_dc.CreateCompatibleDC()
        save_bitmap = win32ui.CreateBitmap()
        save_bitmap.CreateCompatibleBitmap(mfc_dc, client_width, client_height)
        save_dc.SelectObject(save_bitmap)

        windll.user32.PrintWindow(self.hwnd, save_dc.GetSafeHdc(), 2)

        bmp_info = save_bitmap.GetInfo()
        bmp_str = save_bitmap.GetBitmapBits(True)
        img = np.frombuffer(bmp_str, dtype='uint8').reshape(
            (bmp_info['bmHeight'], bmp_info['bmWidth'], 4)
        )

        win32gui.DeleteObject(save_bitmap.GetHandle())
        save_dc.DeleteDC()
        mfc_dc.DeleteDC()
        win32gui.ReleaseDC(self.hwnd, hwnd_dc)

        img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        search_img = img_bgr[y0:y1, x0:x1]

        if self.save_source_img:
            source_dir = debug_img_base_dir / "source"
            source_dir.mkdir(parents=True, exist_ok=True)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            source_img_path = source_dir / f"{timestamp}_source.bmp"
            if not source_img_path.exists():
                cv2.imwrite(str(source_img_path), img)

        return search_img

    @staticmethod
    def pil2np(pil_img) -> np.ndarray:
        return np.array(pil_img)


class ColorDetector:
    """颜色检测和匹配"""

    @staticmethod
    def get_pixel_color(x: int, y: int) -> str:
        gdi32 = windll.gdi32
        user32 = windll.user32
        hdc = user32.GetDC(None)
        pixel = gdi32.GetPixel(hdc, x, y)
        r = pixel & 0x0000ff
        g = (pixel & 0x00ff00) >> 8
        b = pixel >> 16
        return ColorDetector.rgb2hex((r, g, b)).upper()

    @staticmethod
    def find_color(x0: int, y0: int, x1: int, y1: int, color_hex: str) -> Tuple[int, int]:
        color = ColorDetector.hex2rgb(color_hex)
        img = np.array(ImageGrab.grab((x0, y0, x1, y1)))
        for i in range(img.shape[0]):
            for j in range(img.shape[1]):
                if tuple(img[i, j]) == color:
                    return x0 + j, y0 + i
        logger.debug("没找到point")
        return -1, -1

    @staticmethod
    def bg_get_pixel_color(hwnd: int, x: int, y: int) -> Union[str, None]:
        try:
            screen = ScreenCapture(hwnd).capture_window_region(x, y, x + 1, y + 1)
            b, g, r = screen[0, 0][:3]
            return f"{b:02X}{g:02X}{r:02X}"
        except Exception as e:
            logger.exception(f"获取像素颜色失败: {e}")
            return None

    @staticmethod
    def bg_check_pixel_color(hwnd: int, x: int, y: int, expected_color_bgr: str, similarity=1.0) -> bool:
        actual_color = ColorDetector.bg_get_pixel_color(hwnd, x, y)
        if not actual_color:
            return False
        expected_bgr = ColorDetector.hex2rgb(expected_color_bgr)
        actual_bgr = ColorDetector.hex2rgb(actual_color)
        diff = sum((e - a) ** 2 for e, a in zip(expected_bgr, actual_bgr)) ** 0.5
        max_diff = (3 * (255 ** 2)) ** 0.5
        actual_similarity = 1 - (diff / max_diff)
        return actual_similarity >= similarity

    @staticmethod
    def rgb2hex(rgb_tuple):
        """
        将RGB元组转换为十六进制颜色字符串
        :param rgb_tuple: (r, g, b)格式的元组
        :return: 十六进制颜色字符串(不带#)
        """
        return '{:02X}{:02X}{:02X}'.format(*rgb_tuple)

    @staticmethod
    def hex2rgb(hex_str):
        """
        将十六进制颜色字符串转换为RGB元组
        :param hex_str: 十六进制颜色字符串(带或不带#) BBGGRR
        :return: (b, g, r)格式的元组
        """
        hex_str = hex_str.lstrip('#')
        return tuple(int(hex_str[i:i + 2], 16) for i in (0, 2, 4))


class ImageMatchConfig:
    """多模板匹配配置"""

    def __init__(self, target_image_path_list: Union[List[str], str],
                 x0=0, y0=0, x1=99999, y1=99999, similarity=0.8):
        self.target_image_path_list: List[str] = (
            [target_image_path_list] if isinstance(target_image_path_list, str)
            else target_image_path_list
        )
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1
        self.similarity = similarity

    def __hash__(self):
        return hash(tuple(self.target_image_path_list))

    def __eq__(self, other):
        if not isinstance(other, ImageMatchConfig):
            return NotImplemented
        return self.target_image_path_list == other.target_image_path_list

    def __str__(self):
        return f"{self.target_image_path_list} {self.x0} {self.y0} {self.x1} {self.y1} {self.similarity}"


@dataclass
class ImageMatchResult:
    """图像匹配结果"""
    point: Tuple[int, int]
    image_path: str
    similarity: float

    @property
    def x(self) -> int:
        return self.point[0]

    @property
    def y(self) -> int:
        return self.point[1]

    @property
    def is_found(self) -> bool:
        return self.point != (-1, -1)

    def __bool__(self) -> bool:
        return self.is_found


class ImageFinder:
    """
    模板匹配、找图、点击封装，无缓存版本

    支持两种初始化模式：
    1. GameEnvironment 模式：传入 env 参数，使用环境抽象接口
    2. hwnd 模式（向后兼容）：传入 hwnd 参数，使用原生 win32 调用
    """

    def __init__(self, env: Optional['GameEnvironment'] = None, hwnd: Optional[int] = None):
        """
        初始化图像查找器

        :param env: GameEnvironment 实例，用于抽象接口调用
        :param hwnd: 窗口句柄，用于原生 win32 调用（向后兼容）
        """
        self._env = env
        self.hwnd = hwnd
        self.screenshot_capture = ScreenCapture(hwnd=hwnd, env=env)
        self.screenshot_cache: Optional[np.ndarray] = None  # 初始化为 None
        self.update_screenshot_cache()  # 第一次调用可能会失败，但会设置 screenshot_cache

    def update_screenshot_cache(self):
        try:
            self.screenshot_cache = self.screenshot_capture.capture_window_region()
            return self.screenshot_cache
        except Exception as e:
            logger.exception(f"更新截图缓存失败: {e}")
            return self.screenshot_cache

    def crop_screenshot_cache(self, x0=0, y0=0, x1=99999, y1=99999):
        """从截图缓存中裁剪指定区域"""
        if self.screenshot_cache is None:
            self.update_screenshot_cache()
        
        h, w = self.screenshot_cache.shape[:2]
        # 限制裁剪区域在图像范围内
        x0 = max(0, x0)
        y0 = max(0, y0)
        x1 = min(w, x1)
        y1 = min(h, y1)
        
        # 确保裁剪区域有效
        if x0 >= x1 or y0 >= y1:
            logger.warning(f"无效的裁剪区域: ({x0}, {y0}) - ({x1}, {y1}), 图像尺寸: ({w}, {h})")
            return self.screenshot_cache
        
        return self.screenshot_cache[y0:y1, x0:x1]

    def bg_find_pic_by_cache(self, small_picture_path, x0=0, y0=0, x1=99999, y1=99999, similarity=0.8) -> Tuple[int, int]:
        """直接截图匹配图片"""
        return self.bg_find_pic(self.screenshot_cache, small_picture_path, x0, y0, x1, y1, similarity)

    def bg_find_pic_all_by_cache(self, small_picture_path, x0=0, y0=0, x1=99999, y1=99999, similarity=0.8) -> List[Tuple[int, int, float]]:
        """直接截图匹配图片，返回所有匹配结果"""
        return self.bg_find_pic_all(self.screenshot_cache, small_picture_path, x0, y0, x1, y1, similarity)

    def bg_find_pic_all(self, screenshot: Optional[Any], small_img_path, x0=0, y0=0, x1=99999, y1=99999, similarity=0.8) -> List[Tuple[int, int, float]]:
        """
        在给定截图中匹配图片，返回所有大于相似度阈值的结果（按相似度降序排序）
        :return List[Tuple[x, y, similarity]]
        """
        if screenshot is None:
            return []

        small_img_path = to_project_path(small_img_path)
        small_img = cv2.imread(small_img_path)
        if small_img is None:
            return []

        big_img = screenshot
        if x0 or y0 or x1 < 99999 or y1 < 99999:
            h_img, w_img = big_img.shape[:2]
            x1 = min(x1, w_img)
            y1 = min(y1, h_img)
            big_img = big_img[y0:y1, x0:x1]

        result = cv2.matchTemplate(
            big_img,
            small_img,
            cv2.TM_CCOEFF_NORMED
        )

        h, w = small_img.shape[:2]
        matches = []

        # 找到所有大于阈值的匹配位置
        loc = np.where(result >= similarity)
        for pt in zip(*loc[::-1]):
            x = x0 + pt[0]
            y = y0 + pt[1]
            roi = screenshot[y:y+h, x:x+w]
            if roi.size == 0:
                continue

            # ---------- 颜色相似度（直方图比较） ----------
            tpl_hsv = cv2.cvtColor(small_img, cv2.COLOR_BGR2HSV)
            roi_hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

            # 计算 H 通道直方图（色相）
            tpl_hist_h = cv2.calcHist([tpl_hsv], [0], None, [180], [0, 180])
            roi_hist_h = cv2.calcHist([roi_hsv], [0], None, [180], [0, 180])

            # 归一化直方图
            cv2.normalize(tpl_hist_h, tpl_hist_h, 0, 1, cv2.NORM_MINMAX)
            cv2.normalize(roi_hist_h, roi_hist_h, 0, 1, cv2.NORM_MINMAX)

            # 比较直方图（BHATTACHARYYA 距离：0=相同，1=完全不同）
            hist_dist = cv2.compareHist(tpl_hist_h, roi_hist_h, cv2.HISTCMP_BHATTACHARYYA)
            # 转换为相似度（0=完全不同，1=相同）
            color_score = max(0.0, 1.0 - hist_dist)

            # ---------- 合成相似度 ----------
            gray_score = result[pt[1], pt[0]]
            final_score = 0.7 * gray_score + 0.3 * color_score

            if final_score >= similarity:
                center_x = x + w // 2
                center_y = y + h // 2
                matches.append((center_x, center_y, final_score))

        # 按相似度降序排序
        matches.sort(key=lambda m: m[2], reverse=True)

        # 距离去重
        return match_template_nms(matches)

    def bg_find_pic(self, screenshot: Optional[Any], small_img_path, x0=0, y0=0, x1=99999, y1=99999, similarity=0.8) -> Tuple[int, int]:
        """
        在给定截图中匹配图片（增强版，支持灰度和颜色特征）
        :return (x, y)
        """
        matches = self.bg_find_pic_all(screenshot, small_img_path, x0, y0, x1, y1, similarity)
        
        if not matches:
            return -1, -1
        
        center_x, center_y, final_score = matches[0]
        
        # 调试模式保存图片
        if self.screenshot_capture.save_source_img and final_score >= 0.6:
            small_img_path = to_project_path(small_img_path)
            small_img = cv2.imread(small_img_path)
            if small_img is not None:
                h, w = small_img.shape[:2]
                big_img = screenshot
                if x0 or y0 or x1 < 99999 or y1 < 99999:
                    h_img, w_img = big_img.shape[:2]
                    x1 = min(x1, w_img)
                    y1 = min(y1, h_img)
                    big_img = big_img[y0:y1, x0:x1]
                
                small_img_name = Path(small_img_path).stem
                small_img_dir = debug_img_base_dir / small_img_name
                small_img_dir.mkdir(parents=True, exist_ok=True)
                debug_img = big_img.copy()
                cv2.rectangle(debug_img, (center_x - w//2 - x0, center_y - h//2 - y0), 
                             (center_x - w//2 - x0 + w, center_y - h//2 - y0 + h), (0, 255, 0), 1)
                match_text = f"{final_score:.2f}/{similarity}@({center_x},{center_y})"
                cv2.putText(debug_img, match_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
                cv2.imwrite(str(small_img_dir / f"{final_score >= similarity}_result.png"), debug_img)
        
        logger.debug(f"匹配成功: {Path(small_img_path).stem} | 位置: ({center_x},{center_y}) | 相似度: {final_score:.4f}")
        return center_x, center_y

    def find_image(self, screenshot: Optional[Any], small_img_path: str, x0: int = 0, y0: int = 0,
                   x1: int = 99999, y1: int = 99999, similarity: float = 0.8) -> ImageMatchResult:
        """
        在给定截图中匹配图片，返回 ImageMatchResult 对象

        Args:
            screenshot: 截图 numpy 数组
            small_img_path: 小图路径
            x0, y0, x1, y1: 搜索区域
            similarity: 相似度阈值

        Returns:
            ImageMatchResult 对象，包含匹配位置、图片路径和相似度
        """
        matches = self.bg_find_pic_all(screenshot, small_img_path, x0, y0, x1, y1, similarity)

        if not matches:
            return ImageMatchResult(point=(-1, -1), image_path=small_img_path, similarity=0.0)

        center_x, center_y, final_score = matches[0]
        logger.debug(f"匹配成功: {Path(small_img_path).stem} | 位置: ({center_x},{center_y}) | 相似度: {final_score:.4f}")
        return ImageMatchResult(point=(center_x, center_y), image_path=small_img_path, similarity=final_score)

    def find_image_by_cache(self, small_img_path: str, x0: int = 0, y0: int = 0,
                           x1: int = 99999, y1: int = 99999, similarity: float = 0.8) -> ImageMatchResult:
        """使用缓存截图查找图片，返回 ImageMatchResult 对象"""
        return self.find_image(self.screenshot_cache, small_img_path, x0, y0, x1, y1, similarity)

    def bg_find_pic_with_timeout(self, small_picture_path, timeout=5, x0=0, y0=0, x1=99999, y1=99999, similarity=0.8):
        """带超时的图片查找"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            self.update_screenshot_cache()
            point = self.bg_find_pic_by_cache(small_picture_path, x0, y0, x1, y1, similarity)
            if point is not None and point[0] != -1 and point[1] != -1:
                return point
            time.sleep(0.2)
        return -1, -1

    def bg_find_pic_by_config(self, image_match_config: ImageMatchConfig) -> tuple:
        for target_image_path in image_match_config.target_image_path_list:
            point = self.bg_find_pic_by_cache(target_image_path, image_match_config.x0,
                                     image_match_config.y0,
                                     image_match_config.x1, image_match_config.y1,
                                     image_match_config.similarity)
            if point is not None and point[0] != -1 and point[1] != -1:
                return point, target_image_path
        return (-1, -1), None
