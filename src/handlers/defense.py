"""防御技能处理器"""
import time
from src.handlers.base_handler import Handler
from src.context import GameContext
from src.events import Events
from src.registry import EventRegistry


class DefenseAppearedHandler(Handler):
    """防御技能可用处理器"""

    def handle(self, ctx: GameContext, position=None) -> None:
        """处理防御技能可用事件

        Args:
            ctx: 游戏共享状态上下文
            position: 检测到的图像坐标
        """
        if ctx.is_slower() and ctx.enemy_inactive >= 3:
            return
        if not ctx.is_slower() and ctx.my_inactive < 3:
            return
        self.ctrl.click_at(*position)
        time.sleep(7)


# 注册到事件表
EventRegistry.register(
    event=Events.DEFENSE_APPEARED,
    handler_cls=DefenseAppearedHandler,
    template="skills/defense.png",
    region=(0, 0, 2560, 1440),
    similarity=0.8
)