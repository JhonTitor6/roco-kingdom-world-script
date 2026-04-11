"""选择精灵处理器"""
from src.context import GameContext
from src.events import Events
from src.handlers.base_handler import Handler
from src.registry import EventRegistry
from src.state_machine import BattleState
from src.utils import random_sleep


class SelectFirstElfHandler(Handler):
    """SELECT_FIRST 状态处理器"""

    def handle(self, ctx: GameContext, position=None) -> bool:
        """选择首发精灵（final 精灵）"""
        # 等待选精灵界面
        self.ctrl.click_at(*position)

        random_sleep(1)

        # 选择 final 精灵
        if not self.skill.select_first_elf(self.elf_mgr.final_elf):
            return False

        random_sleep(1)

        # 切换到 CONFIRM_FIRST 状态
        self.transition(BattleState.CONFIRM_FIRST)
        return True


EventRegistry.register(
    event=Events.CONFIRM_LINEUPS,
    handler_cls=SelectFirstElfHandler,
    template="battle/confirm_lineups.png",
    region=(0, 0, 2560, 1440),
    similarity=0.8
)
