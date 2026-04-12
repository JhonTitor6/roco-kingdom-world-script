from src.handlers.base_handler import Handler
from src.context import GameContext
from src.events import Events
from src.registry import EventRegistry


class QuitHandler(Handler):
    """退出战斗处理器"""

    def handle(self, ctx: GameContext, position=None) -> None:
        """处理退出战斗事件

        Args:
            ctx: 游戏共享状态上下文
            position: 检测到的图像坐标
        """
        # 非自爆流才点击 quit，自爆流由 retry_handler 处理 retry
        # if not ctx.enemy_self_destruct:
        #     self.ctrl.click_at(*position)

        self.ctrl.click_at(*position)
        self.random_sleep(1, 2)


EventRegistry.register(
    event=Events.QUIT,
    handler_cls=QuitHandler,
    template="battle/quit.png",
    region=(0, 0, 2560, 1440),
    similarity=0.8,
    priority=10
)
