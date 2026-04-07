from src.handlers.base_handler import Handler
from src.context import GameContext
from src.events import Events
from src.registry import EventRegistry


class StartChallengeHandler(Handler):
    """开始挑战处理器"""

    def handle(self, ctx: GameContext, position=None) -> None:
        """处理开始挑战事件

        Args:
            ctx: 游戏共享状态上下文
            position: 检测到的图像坐标
        """
        self.ctrl.click_at(*position)


EventRegistry.register(
    event=Events.START_CHALLENGE,
    handler_cls=StartChallengeHandler,
    template="battle/start_challenge.png",
    region=(0, 0, 2560, 1440),
    similarity=0.8
)
