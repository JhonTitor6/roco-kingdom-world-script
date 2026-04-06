"""确认处理器"""
from src.handlers.base_handler import Handler
from src.state_machine import BattleState
from src.utils import random_sleep


class ConfirmHandler(Handler):
    """CONFIRM_FIRST 状态处理器"""

    def handle(self) -> bool:
        """确认首发选择"""
        # 点击确认按钮
        if not self.skill.confirm_selection():
            return False

        random_sleep(10)  # 等待战斗开始

        # 切换到 BATTLE_START 状态
        self.transition(BattleState.BATTLE_START)
        return True
