"""通用工具模块"""
import time
import random


def random_sleep(base: float) -> None:
    """随机休眠，基于中心值 ±0.5s 浮动，最小 0.05s

    用于防止游戏检测自动化脚本的固定延迟模式。

    Args:
        base: 中心延迟时间（秒）
    """
    offset = random.uniform(-0.5, 0.5)
    sleep_time = max(0.05, base + offset)
    time.sleep(sleep_time)
