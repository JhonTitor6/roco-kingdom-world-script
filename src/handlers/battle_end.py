from src.handlers.base_handler import Handler
from src.context import GameContext
from src.events import Events
from src.registry import EventRegistry


class BattleEndHandler(Handler):
    """战斗结束处理器"""

    def handle(self, ctx: GameContext, position=None) -> None:
        """处理战斗结束事件

        Args:
            ctx: 游戏共享状态上下文
            position: 检测到的图像坐标
        """
        self.ctrl.find_and_click("battle/battle_end.png")


EventRegistry.register(
    event=Events.BATTLE_END,
    handler_cls=BattleEndHandler,
    template="battle/battle_end.png",
    region=(0, 0, 2560, 1440),
    similarity=0.8
)
