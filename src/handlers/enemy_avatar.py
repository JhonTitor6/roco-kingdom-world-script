from src.handlers.base_handler import Handler
from src.context import GameContext
from src.events import Events
from src.registry import EventRegistry


class EnemyAvatarHandler(Handler):
    """敌方精灵头像处理器

    用于检测敌方精灵头像出现，主要作为状态标记。
    实际自爆流检测由 EnemySelfDestructHandler 持续检测。
    """

    def handle(self, ctx: GameContext, position=None) -> None:
        """处理敌方精灵头像事件

        Args:
            ctx: 游戏共享状态上下文
            position: 检测到的图像坐标
        """
        # 此 Handler 主要用于触发 ENEMY_AVATAR 事件
        # 实际行为（如自爆流检测）在检测循环中持续进行
        pass


EventRegistry.register(
    event=Events.ENEMY_AVATAR,
    handler_cls=EnemyAvatarHandler,
    template=[],  # 动态从 elf_manager 获取
    region=(2000, 0, 2560, 320),
    similarity=0.7
)
