from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.event_dispatcher import EventDispatcher

@dataclass
class GameContext:
    """游戏共享状态上下文

    存储跨事件共享的数据，供各 Handler 读写。
    通过 EventDispatcher 注入依赖引用。

    Attributes:
        dispatcher: EventDispatcher 引用
        slower: SLOWER 流程标记
        sacrifice: SACRIFICE 阶段标记
        my_inactive: 我方 inactive dot 数量
        enemy_inactive: 敌方 inactive dot 数量
    """
    dispatcher: "EventDispatcher"
    slower: bool = False
    my_inactive: int = 0
    enemy_inactive: int = 0

    def set_slower(self, value: bool) -> None:
        """设置 SLOWER 流程标记"""
        self.slower = value

    def is_slower(self) -> bool:
        """获取 SLOWER 流程标记"""
        return self.slower

    def is_sacrifice(self) -> bool:
        """获取 SACRIFICE 阶段标记"""
        return self.sacrifice

    def update_inactive(self, my: int, enemy: int) -> None:
        """更新 inactive dot 数量"""
        self.my_inactive = my
        self.enemy_inactive = enemy

    @property
    def controller(self):
        """获取 controller 引用"""
        return self.dispatcher.controller

    @property
    def elf_manager(self):
        """获取 elf_manager 引用"""
        return self.dispatcher.elf_manager

    @property
    def skill_executor(self):
        """获取 skill_executor 引用"""
        return self.dispatcher.skill_executor