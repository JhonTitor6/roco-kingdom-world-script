from src.handlers.base_handler import Handler
from src.context import GameContext
from src.events import Events
from src.registry import EventRegistry


class RetryHandler(Handler):
    """再次切磋处理器"""

    def handle(self, ctx: GameContext, position=None) -> None:
        """处理再次切磋事件

        Args:
            ctx: 游戏共享状态上下文
            position: 检测到的图像坐标
        """
        self.ctrl.find_and_click("battle/retry.png")


EventRegistry.register(
    event=Events.RETRY,
    handler_cls=RetryHandler,
    template="battle/retry.png",
    region=(0, 0, 2560, 1440),
    similarity=0.8
)
