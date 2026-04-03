"""窗口查找模块"""
import win32gui
from loguru import logger
from src.exceptions import GameWindowNotFoundError


def find_window(class_name: str = "UnrealWindow", title: str = "洛克王国：世界") -> int:
    """查找游戏窗口

    Args:
        class_name: 窗口类名
        title: 窗口标题（部分匹配）

    Returns:
        窗口句柄 (hwnd)

    Raises:
        GameWindowNotFoundError: 未找到窗口
    """
    # 先尝试精确标题匹配
    hwnd = win32gui.FindWindow(class_name, title)
    if hwnd:
        logger.info(f"找到游戏窗口: hwnd={hwnd}, title='{title}'")
        return hwnd

    # 尝试部分匹配（枚举所有窗口）
    result = []

    def enum_callback(hwnd, extra):
        window_title = win32gui.GetWindowText(hwnd)
        if title in window_title:
            result.append(hwnd)

    win32gui.EnumWindows(enum_callback, None)

    if result:
        hwnd = result[0]
        logger.info(f"通过部分匹配找到窗口: hwnd={hwnd}, title='{win32gui.GetWindowText(hwnd)}'")
        return hwnd

    raise GameWindowNotFoundError(f"未找到游戏窗口: class_name={class_name}, title={title}")


def is_window_valid(hwnd: int) -> bool:
    """检查窗口是否有效"""
    try:
        return win32gui.IsWindow(hwnd) and win32gui.IsWindowVisible(hwnd)
    except Exception:
        return False


def get_window_rect(hwnd: int) -> tuple:
    """获取窗口客户区矩形 (left, top, right, bottom)"""
    return win32gui.GetClientRect(hwnd)
