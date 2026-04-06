"""Handler 基类"""
from abc import ABC, abstractmethod

from src.state_machine import BattleState


class Handler(ABC):
    """处理器基类

    每个 Handler 只处理特定状态，通过 EventDispatcher 按状态分发。
    """

    def __init__(self, dispatcher: "EventDispatcher"):
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
    def handle(self) -> bool:
        """处理当前状态的逻辑，返回是否继续循环

        Returns:
            True=继续循环，False=进入 ERROR 状态
        """
        pass

    def transition(self, new_state: BattleState) -> None:
        """切换状态"""
        self.dispatcher.state = new_state