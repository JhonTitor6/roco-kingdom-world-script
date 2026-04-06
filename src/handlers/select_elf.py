"""选择精灵处理器"""
from src.handlers.base_handler import Handler
from src.state_machine import BattleState
from src.utils import random_sleep


class SelectElfHandler(Handler):
    """SELECT_FIRST 状态处理器"""

    def handle(self) -> bool:
        """选择首发精灵（final 精灵）"""
        # 等待选精灵界面
        if self.ctrl.find_image_with_timeout(
            "battle/confirm_lineups.png", timeout=60, similarity=0.8
        ) is None:
            return False  # 超时，进入 ERROR

        random_sleep(1)

        # 选择 final 精灵
        if not self.skill.select_first_elf(self.elf_mgr.final_elf):
            return False

        random_sleep(1)

        # 切换到 CONFIRM_FIRST 状态
        self.transition(BattleState.CONFIRM_FIRST)
        return True
