import time
from typing import TYPE_CHECKING, Optional, Tuple

from win_util.image import ImageFinder, ImageMatchConfig
from win_util.keyboard import KeyboardController
from win_util.mouse import MouseController
from win_util.ocr import CommonOcr

if TYPE_CHECKING:
    # GameEnvironment 是可选的抽象接口，仅用于类型标注
    # 运行时如果未安装 tests 模块，使用字符串避免 ImportError
    try:
        from tests.common.environment.base import GameEnvironment
    except ImportError:
        GameEnvironment = None  # type: ignore


class WinController:
    """
    Windows 控制器，封装了图像、键盘、鼠标和OCR功能

    支持两种初始化模式：
    1. GameEnvironment 模式：传入 env 参数，使用环境抽象接口
    2. hwnd 模式（向后兼容）：传入 hwnd 参数，使用原生 win32 调用
    """

    def __init__(self, hwnd: Optional[int] = None, env: Optional['GameEnvironment'] = None):
        """
        初始化控制器

        :param hwnd: 窗口句柄（向后兼容）
        :param env: GameEnvironment 实例，用于抽象接口调用
        """
        self.hwnd = hwnd
        self._env = env

        # 优先使用 GameEnvironment，否则使用 hwnd
        # 注意：keyboard 暂不支持 GameEnvironment，仅传入 hwnd
        self.image_finder: ImageFinder = ImageFinder(env=env, hwnd=hwnd)
        self.keyboard: KeyboardController = KeyboardController(hwnd)
        self.mouse: MouseController = MouseController(env=env, hwnd=hwnd)
        self.ocr: CommonOcr = CommonOcr()

    # 前缀 -> 组件映射（按优先级排序）
    _PREFIX_MAP = [
        ('bg_find_', 'image_finder'),
        ('crop_', 'image_finder'),
        ('update_', 'image_finder'),
        ('bg_left', 'mouse'),
        ('bg_right', 'mouse'),
        ('bg_swipe', 'mouse'),
        ('key_', 'keyboard'),
        ('press_', 'keyboard'),
        ('ocr_', 'ocr'),
        ('find_text', 'ocr'),
        ('contains_text', 'ocr'),
    ]

    def __getattr__(self, name):
        for prefix, attr_name in self._PREFIX_MAP:
            if name.startswith(prefix):
                component = getattr(self, attr_name)
                if hasattr(component, name):
                    return getattr(component, name)
        raise AttributeError(name)


    # 图像相关方法
    def find_image(self, small_picture_path: str, x0=0, y0=0, x1=99999, y1=99999, similarity=0.8):
        """
        在指定区域内查找图片
        
        :param small_picture_path: 小图路径
        :param x0: 区域左上角x坐标
        :param y0: 区域左上角y坐标
        :param x1: 区域右下角x坐标
        :param y1: 区域右下角y坐标
        :param similarity: 相似度阈值
        :return: 找到的坐标点，如果未找到返回(-1, -1)
        """
        return self.image_finder.bg_find_pic_by_cache(small_picture_path, x0, y0, x1, y1, similarity)
    
    def find_images_all(self, small_picture_path: str, x0=0, y0=0, x1=99999, y1=99999, similarity=0.8):
        """
        在指定区域内查找所有匹配的图片

        :param small_picture_path: 小图路径
        :param x0: 区域左上角x坐标
        :param y0: 区域左上角y坐标
        :param x1: 区域右下角x坐标
        :param y1: 区域右下角y坐标
        :param similarity: 相似度阈值
        :return: 匹配的坐标点列表
        """
        return self.image_finder.bg_find_pic_all_by_cache(small_picture_path, x0, y0, x1, y1, similarity)
    
    def find_image_with_timeout(self, small_picture_path: str, timeout=3, x0=0, y0=0, x1=99999, y1=99999, similarity=0.8):
        """
        在指定时间内持续查找图片
        
        :param small_picture_path: 小图路径
        :param timeout: 超时时间（秒）
        :param x0: 区域左上角x坐标
        :param y0: 区域左上角y坐标
        :param x1: 区域右下角x坐标
        :param y1: 区域右下角y坐标
        :param similarity: 相似度阈值
        :return: 找到的坐标点，如果未找到返回(-1, -1)
        """
        return self.image_finder.bg_find_pic_with_timeout(small_picture_path, timeout, x0, y0, x1, y1, similarity)
    
    def update_screenshot_cache(self):
        """
        更新截图缓存
        """
        return self.image_finder.update_screenshot_cache()
    
    def find_image_by_config(self, image_match_config: ImageMatchConfig):
        """
        根据配置查找图片
        
        :param image_match_config: 图片匹配配置
        :return: 找到的坐标点和图片路径
        """
        return self.image_finder.bg_find_pic_by_config(image_match_config)

    # 键盘相关方法
    def press_key(self, key_code):
        """
        按下指定按键
        
        :param key_code: 按键码或按键名称
        """
        self.keyboard.bg_press_key(key_code)
    
    def key_down(self, key_code):
        """
        按下按键不释放
        
        :param key_code: 按键码或按键名称
        """
        self.keyboard.bg_key_down(key_code)
    
    def key_up(self, key_code):
        """
        释放按键
        
        :param key_code: 按键码或按键名称
        """
        self.keyboard.bg_key_up(key_code)
    
    # OCR相关方法
    def ocr_text(self, img):
        """
        识别图像中的文本
        
        :param img: 图像
        :return: OCR结果列表
        """
        return self.ocr.ocr(img)
    
    def contains_text(self, img, target_text, case_sensitive=False):
        """
        检查图像中是否包含指定文本
        
        :param img: 图像
        :param target_text: 目标文本
        :param case_sensitive: 是否区分大小写
        :return: 是否包含文本
        """
        return self.ocr.contains_text(img, target_text, case_sensitive)
    
    def find_text_position(self, img, target_text, similarity_threshold=0.3, case_sensitive=False):
        """
        查找文本在图像中的位置
        
        :param img: 图像
        :param target_text: 目标文本
        :param similarity_threshold: 相似度阈值
        :param case_sensitive: 是否区分大小写
        :return: 文本位置
        """
        return self.ocr.find_text_position(img, target_text, similarity_threshold, case_sensitive)
    
    def find_text_positions(self, img, target_text, similarity_threshold=0.3, case_sensitive=False):
        """
        查找所有匹配文本的位置
        
        :param img: 图像
        :param target_text: 目标文本
        :param similarity_threshold: 相似度阈值
        :param case_sensitive: 是否区分大小写
        :return: 所有匹配文本的位置列表
        """
        return self.ocr.find_text_positions(img, target_text, similarity_threshold, case_sensitive)
    
    # 便捷方法
    def find_and_click(self, image_path: str, x0=0, y0=0, x1=99999, y1=99999, similarity=0.8, 
                      x_range=20, y_range=20, timeout=None):
        """
        找图后点击的便捷方法
        
        :param image_path: 图片路径
        :param x0: 查找区域左上角x坐标
        :param y0: 查找区域左上角y坐标
        :param x1: 查找区域右下角x坐标
        :param y1: 查找区域右下角y坐标
        :param similarity: 相似度阈值
        :param x_range: 点击随机范围x轴
        :param y_range: 点击随机范围y轴
        :param timeout: 超时时间，None表示不设置超时
        :return: 点击是否成功
        """
        point = None
        if timeout is not None:
            point = self.find_image_with_timeout(image_path, timeout=timeout, x0=x0, y0=y0, x1=x1, y1=y1, similarity=similarity)
        else:
            point = self.find_image(image_path, x0=x0, y0=y0, x1=x1, y1=y1, similarity=similarity)
        
        if point and point != (-1, -1):
            return self.mouse.bg_left_click(point, x_range=x_range, y_range=y_range)
        return False
    
    def wait_for_image(self, image_path: str, timeout=10, x0=0, y0=0, x1=99999, y1=99999, similarity=0.8):
        """
        等待特定图像出现
        
        :param image_path: 图片路径
        :param timeout: 超时时间
        :param x0: 查找区域左上角x坐标
        :param y0: 查找区域左上角y坐标
        :param x1: 查找区域右下角x坐标
        :param y1: 查找区域右下角y坐标
        :param similarity: 相似度阈值
        :return: 图像出现的坐标，如果超时未出现返回None
        """
        return self.find_image_with_timeout(image_path, timeout=timeout, x0=x0, y0=y0, x1=x1, y1=y1, similarity=similarity)
    
    def find_multiple_and_click_first(self, image_paths, x0=0, y0=0, x1=99999, y1=99999, similarity=0.8, 
                                    x_range=20, y_range=20):
        """
        同时查找多个图像并点击第一个找到的
        
        :param image_paths: 图片路径列表
        :param x0: 查找区域左上角x坐标
        :param y0: 查找区域左上角y坐标
        :param x1: 查找区域右下角x坐标
        :param y1: 查找区域右下角y坐标
        :param similarity: 相似度阈值
        :param x_range: 点击随机范围x轴
        :param y_range: 点击随机范围y轴
        :return: 点击是否成功
        """
        for image_path in image_paths:
            point = self.find_image(image_path, x0=x0, y0=y0, x1=x1, y1=y1, similarity=similarity)
            if point and point != (-1, -1):
                return self.mouse.bg_left_click(point, x_range=x_range, y_range=y_range)
        return False

    def wait_for_image_disappear(self, image_path: str, timeout: float = 10,
                                   x0: int = 0, y0: int = 0, x1: int = 99999, y1: int = 99999,
                                   similarity: float = 0.8) -> bool:
        """等待图片消失"""
        start = time.time()
        while time.time() - start < timeout:
            self.update_screenshot_cache()
            pos = self.find_image(image_path, x0, y0, x1, y1, similarity)
            if pos == (-1, -1):
                return True
            time.sleep(0.5)
        return False

    def wait_for_text(self, text: str, timeout: float = 10,
                      case_sensitive: bool = False) -> Optional[Tuple[int, int]]:
        """等待文字出现"""
        start = time.time()
        while time.time() - start < timeout:
            self.update_screenshot_cache()
            result = self.find_text_position(self.image_finder.screenshot_cache, text,
                                             similarity_threshold=0.3,
                                             case_sensitive=case_sensitive)
            if result:
                return result
            time.sleep(0.5)
        return None

    def wait_for_text_disappear(self, text: str, timeout: float = 10,
                                 case_sensitive: bool = False) -> bool:
        """等待文字消失"""
        start = time.time()
        while time.time() - start < timeout:
            self.update_screenshot_cache()
            result = self.find_text_position(self.image_finder.screenshot_cache, text,
                                             similarity_threshold=0.3,
                                             case_sensitive=case_sensitive)
            if not result:
                return True
            time.sleep(0.5)
        return False

    def wait_for_image_and_click(self, image_path: str, timeout: float = 10,
                                  x0: int = 0, y0: int = 0, x1: int = 99999, y1: int = 99999,
                                  similarity: float = 0.8,
                                  x_range: int = 20, y_range: int = 20) -> bool:
        """等待图片出现并点击"""
        pos = self.wait_for_image(image_path, timeout, x0, y0, x1, y1, similarity)
        if pos and pos != (-1, -1):
            self.mouse.bg_left_click(pos, x_range=x_range, y_range=y_range)
            return True
        return False

    def wait_for_text_and_click(self, text: str, timeout: float = 10,
                                 x_range: int = 20, y_range: int = 20,
                                 case_sensitive: bool = False) -> bool:
        """等待文字出现并点击"""
        pos = self.wait_for_text(text, timeout, case_sensitive)
        if pos:
            self.mouse.bg_left_click(pos, x_range=x_range, y_range=y_range)
            return True
        return False