from src.handlers.base_handler import Handler
from src.context import GameContext
from src.events import Events
from src.registry import EventRegistry


class EnemySelfDestructHandler(Handler):
    """敌方自爆流处理器

    检测到敌方自爆流精灵时执行逃跑并停止主循环。
    """

    def handle(self, ctx: GameContext, position=None) -> None:
        """处理敌方自爆流事件

        Args:
            ctx: 游戏共享状态上下文
            position: 检测到的图像坐标
        """
        # self.skill.escape_battle()
        # self.dispatcher.stop()


# EventRegistry.register(
#     event=Events.ENEMY_SELF_DESTRUCT,
#     handler_cls=EnemySelfDestructHandler,
#     template=[],  # 动态从 elf_manager 获取
#     region=(2000, 0, 2560, 320),
#     similarity=0.7
# )
