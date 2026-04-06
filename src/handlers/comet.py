"""彗星技能处理器"""
from src.handlers.base_handler import Handler
from src.context import GameContext
from src.events import Events
from src.registry import EventRegistry


class CometAppearedHandler(Handler):
    """彗星技能可用处理器"""

    def handle(self, ctx: GameContext, position=None) -> None:
        """处理彗星技能可用事件

        Args:
            ctx: 游戏共享状态上下文
            position: 检测到的图像坐标
        """
        # 根据 context 状态决定行为
        if ctx.is_slower() and ctx.my_inactive == 0 and ctx.enemy_inactive == 1:
            ctx.set_sacrifice(True)

        self.skill.cast_skill("comet")


# 注册到事件表
EventRegistry.register(
    event=Events.COMET_APPEARED,
    handler_cls=CometAppearedHandler,
    template="skills/comet.png",
    region=(0, 0, 2560, 1440),
    similarity=0.8
)