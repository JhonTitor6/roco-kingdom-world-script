import random
import threading
import time
from abc import ABC
from typing import Callable, Optional

from loguru import logger

from win_util.image import ImageFinder, ImageMatchConfig
from win_util.ocr import CommonOcr


# ==================== 常量定义 ====================

# 事件触发后短暂延迟，避免频繁触发
EVENT_TRIGGER_DELAY = 0.1

# 主循环休眠范围
LOOP_SLEEP_MIN = 0.1
LOOP_SLEEP_MAX = 0.2

# 未知事件名称
UNKNOWN_EVENT_NAME = "unknown"


def random_sleep(min_val: float, max_val: float) -> None:
    """随机等待一段时间"""
    sleep_seconds = random.uniform(min_val, max_val)
    time.sleep(sleep_seconds)


class Event:
    """事件对象，用于事件分发系统"""

    def __init__(self, event_name: str):
        self.name = event_name

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Event):
            return NotImplemented
        return self.name == other.name

    def __hash__(self) -> int:
        return hash(self.name)

    def __str__(self) -> str:
        return self.name


class EventManager:
    """事件管理器，负责注册和触发事件"""

    def __init__(self):
        self._event_handler_map: dict[Event, Optional[Callable]] = {}

    def register_event_handler(self, event: Event, callback: Optional[Callable]) -> None:
        """注册事件处理器

        Args:
            event: 事件对象
            callback: 回调函数，如果为 None 则该事件不会有任何操作
        """
        self._event_handler_map[event] = callback

    def trigger_event(self, event: Event | str, data=None, debug_log: bool = True) -> bool:
        """触发事件，调用已注册的处理函数

        Args:
            event: 事件对象或事件名称字符串
            data: 传递给回调的数据
            debug_log: 是否记录调试日志

        Returns:
            bool: 事件是否被触发（存在对应处理器）
        """
        # 字符串自动转换为 Event 对象
        if isinstance(event, str):
            event = Event(event)

        if event not in self._event_handler_map:
            return False

        callback = self._event_handler_map[event]

        # 回调为空时的处理
        if callback is None:
            if debug_log:
                logger.debug(f"触发事件 [{event}] 但是回调为空")
            return True

        # 记录回调信息用于调试
        if debug_log:
            callback_name = self._get_callback_name(callback)
            logger.debug(f"触发事件 [{event}] 回调 [{callback_name}]")

        # 执行回调
        callback(data)
        return True

    @staticmethod
    def _get_callback_name(callback: Callable) -> str:
        """获取回调函数的名称"""
        # 处理 bound method
        if hasattr(callback, '__self__') and hasattr(callback, '__name__'):
            return f"{callback.__self__.__class__.__name__}.{callback.__name__}"
        # 处理普通函数或 callable 对象
        return getattr(callback, '__name__', str(callback))


class EventBaseScript(ABC):
    """
    基于事件驱动的脚本基类
    提供图像匹配事件注册、OCR 事件注册和脚本生命周期管理
    """

    def __init__(self, image_finder: Optional[ImageFinder] = None, ocr: Optional[CommonOcr] = None):
        super().__init__()
        self.image_finder = image_finder
        self.ocr = ocr

        self._event_manager = EventManager()

        # 已注册的图像匹配配置列表
        self._image_event_match_configs: list[ImageMatchConfig] = []
        # 已注册的 OCR 关键词列表
        self._ocr_event_keywords: list[str] = []

        # 脚本控制线程事件
        self._pause_threading_event = threading.Event()
        self._pause_threading_event.set()  # 初始状态为运行
        self._stop_threading_event = threading.Event()

        # 未知事件处理器（默认空实现，避免每次迭代都触发噪音日志）
        self._event_manager.register_event_handler(
            Event(UNKNOWN_EVENT_NAME),
            None
        )

    def _register_image_match_event(self, image_event_match_config: ImageMatchConfig, callback: Callable) -> None:
        """注册图像匹配事件

        Args:
            image_event_match_config: 图像匹配配置
            callback: 匹配成功时的回调函数，接收 (x, y) 坐标参数
        """
        # 避免重复注册相同配置
        if image_event_match_config in self._image_event_match_configs:
            self._image_event_match_configs.remove(image_event_match_config)

        self._image_event_match_configs.append(image_event_match_config)

        # 为每个目标图像路径注册事件
        for target_image_path in image_event_match_config.target_image_path_list:
            self._event_manager.register_event_handler(Event(target_image_path), callback)

    def _register_ocr_match_event(self, keyword: str, callback: Callable) -> None:
        """注册 OCR 文本匹配事件

        Args:
            keyword: 要匹配的文本关键词
            callback: 匹配成功时的回调函数

        Note:
            OCR 功能目前因性能原因暂时禁用，此方法保留用于未来扩展
        """
        if keyword in self._ocr_event_keywords:
            self._ocr_event_keywords.remove(keyword)

        self._ocr_event_keywords.append(keyword)
        self._event_manager.register_event_handler(Event(keyword), callback)

    def _trigger_event_from_screenshot_cache(self) -> Optional[str]:
        """从截图缓存中检测并触发图像匹配事件

        Returns:
            触发的事件对应的图像路径，如果没有匹配返回 None
        """
        if self.image_finder is None:
            return None

        # 遍历已注册的图像匹配配置
        for image_match_config in self._image_event_match_configs:
            res = self.image_finder.bg_find_pic_by_config(image_match_config)

            if res is None:
                continue

            point = res[0]
            if point is not None and point != (-1, -1):
                # 短暂延迟避免事件过于频繁
                time.sleep(EVENT_TRIGGER_DELAY)
                image_path = res[1]
                if self._event_manager.trigger_event(image_path, point):
                    return image_path

        # OCR 功能暂时禁用（性能问题）
        # 未来可通过以下方式启用：
        # ocr_results = self.ocr.find_all_text_positions(self.image_finder.screenshot_cache)
        # for keyword in self._ocr_event_keywords:
        #     for x, y, text, similarity in ocr_results:
        #         if keyword in text:
        #             if self._event_manager.trigger_event(keyword, (x, y, text, similarity)):
        #                 return keyword

        return None

    # ==================== 脚本控制方法 ====================

    def pause(self) -> None:
        """暂停脚本执行"""
        self._pause_threading_event.clear()

    def resume(self) -> None:
        """恢复脚本执行"""
        self._pause_threading_event.set()

    def stop(self) -> None:
        """停止脚本执行"""
        logger.info("停止脚本")
        self._stop_threading_event.set()

    def pause_point(self) -> None:
        """等待暂停事件（阻塞直到被 resume）"""
        self._pause_threading_event.wait()

    def run(self) -> None:
        """主循环：执行初始化后持续运行直到被 stop"""
        self.on_run()

        while not self._stop_threading_event.is_set():
            self.pause_point()
            self.before_iteration()

            # 更新截图缓存（如有）
            if self.image_finder is not None:
                self.image_finder.update_screenshot_cache()

            # 触发图像匹配事件
            self._trigger_event_from_screenshot_cache()

            # 随机休眠，避免 CPU 占用过高
            random_sleep(LOOP_SLEEP_MIN, LOOP_SLEEP_MAX)

            # 每轮循环结束调用扩展钩子
            self.after_iteration()

        self._stop_threading_event.clear()

    # ==================== 扩展钩子方法 ====================

    def on_run(self) -> None:
        """钩子：脚本启动时调用一次，子类可覆盖"""
        pass

    def before_iteration(self) -> None:
        """钩子：每轮循环开始前调用，子类可覆盖"""
        pass

    def after_iteration(self) -> None:
        """钩子：每轮循环结束后调用，子类可覆盖"""
        pass
