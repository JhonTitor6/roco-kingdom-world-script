from src.handlers.base_handler import Handler
from src.context import GameContext
from src.events import Events
from src.registry import EventRegistry


class SwitchElfHandler(Handler):
    """切换精灵处理器"""
    CONFIRM_POS = 1543, 956
    ELF_REGION = (24, 327, 550, 1200)

    def _switch_to_elf(self, elf_template: str) -> bool:
        """切换到指定精灵

        Args:
            elf_template: 精灵模板路径

        Returns:
            是否切换成功
        """
        x0, y0, x1, y1 = self.ELF_REGION
        pos = self.ctrl.find_image_with_timeout(
            elf_template, timeout=1, x0=x0, y0=y0, x1=x1, y1=y1
        )
        if pos:
            self.ctrl.click_at(*pos)
            self.random_sleep(1, 2)
            self.ctrl.click_at(*self.CONFIRM_POS)
            return True
        return False

    def handle(self, ctx: GameContext, position=None) -> None:
        """处理切换精灵事件

        Args:
            ctx: 游戏共享状态上下文
            position: 检测到的图像坐标
        """
        # SLOWER
        if ctx.is_slower():
            if ctx.enemy_inactive < 3:
                return
            if self._switch_to_elf(self.elf_mgr.get_reserve_template()):
                return
            if self._switch_to_elf(self.elf_mgr.get_sacrifice_template()):
                return
        else:
            # FASTER
            if ctx.my_inactive < 3:
                self._switch_to_elf(self.elf_mgr.get_sacrifice_template())
                return
            if ctx.my_inactive >= 3:
                self._switch_to_elf(self.elf_mgr.get_reserve_template())
                return


EventRegistry.register(
    event=Events.SWITCH_ELF,
    handler_cls=SwitchElfHandler,
    template=["elves/tree3.png", "elves/otter2.png", "elves/pig3.png", "elves/scepter3.png"],
    region=(24, 327, 550, 1200),
    similarity=0.7
)
