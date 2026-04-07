import random
import time
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Tuple, Optional

if TYPE_CHECKING:
    from src.event_dispatcher import EventDispatcher
    from src.context import GameContext


class Handler(ABC):
    """事件处理器基类

    所有事件处理器必须继承此类并实现 handle 方法。

    Args:
        dispatcher: EventDispatcher 引用，用于访问 controller 等依赖
    """

    def __init__(self, dispatcher: "EventDispatcher") -> None:
        self.dispatcher = dispatcher

    @property
    def ctrl(self):
        """获取 GameController"""
        return self.dispatcher.controller

    @property
    def elf_mgr(self):
        """获取 ElfManager"""
        return self.dispatcher.elf_manager

    @property
    def skill(self):
        """获取 SkillExecutor"""
        return self.dispatcher.skill_executor

    @abstractmethod
    def handle(self, ctx: "GameContext", position: Optional[Tuple[int, int]] = None) -> None:
        """处理事件

        Args:
            ctx: 游戏共享状态上下文
            position: 检测到的图像坐标（可选）
        """
        pass

    def random_sleep(self, min_val: float, max_val: float) -> None:
        """随机等待一段时间"""
        sleep_seconds = random.uniform(min_val, max_val)
        time.sleep(sleep_seconds)