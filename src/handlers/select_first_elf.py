"""选择精灵处理器"""
from src.context import GameContext
from src.events import Events
from src.handlers.base_handler import Handler
from src.registry import EventRegistry
from src.utils import random_sleep
from loguru import logger


class SelectFirstElfHandler(Handler):
    """SELECT_FIRST 状态处理器"""

    def handle(self, ctx: GameContext, position=None) -> bool:
        """选择首发精灵（final 精灵）"""
        # 选择 final 精灵
        # FIXME: 没生效
        pos = self.ctrl.find_image_with_timeout(
            self.elf_mgr.final_elf.template,
            timeout=3,
            x0=140, y0=280, x1=560, y1=1150
        )
        if pos:
            logger.info(f"选择{self.elf_mgr.final_elf.name}")
            self.ctrl.click_at(*pos)

        self.ctrl.click_at(*position)
        random_sleep(5)

        # 检测敌方是否是自爆流


        return True


EventRegistry.register(
    event=Events.CONFIRM_LINEUPS,
    handler_cls=SelectFirstElfHandler,
    template="battle/confirm_lineups.png",
    region=(1118, 1215, 1461, 1356),
    similarity=0.7
)
