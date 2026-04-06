from src.handlers.base_handler import Handler
from src.context import GameContext
from src.events import Events
from src.registry import EventRegistry


class DotsChangedHandler(Handler):
    """Dot 状态变化处理器

    检测到我方 active dot 和敌方 inactive dot 数量变化时更新 context。
    同时基于 inactive dot 数量判断速度优势，设置 ctx.slower 标志。
    """

    def handle(self, ctx: GameContext, position=None) -> None:
        """处理 dot 状态变化事件

        Args:
            ctx: 游戏共享状态上下文
            position: 检测到的图像坐标
        """
        # 统计我方 active dot
        my_active = self.ctrl.find_images_all(
            "dots/dot_active.png",
            x0=141, y0=132, x1=329, y1=166
        )
        # 统计敌方 inactive dot
        enemy_inactive = self.ctrl.find_images_all(
            "dots/dot_inactive.png",
            x0=2300, y0=132, x1=2490, y1=166
        )
        ctx.update_inactive(len(my_active), len(enemy_inactive))

        # 基于 inactive dot 数量判断速度优势
        # 如果我方已有 inactive 且敌方无 inactive，说明敌方更快
        if ctx.my_inactive > 0 and ctx.enemy_inactive == 0:
            ctx.set_slower(True)
        # 如果敌方已有 inactive 且我方无 inactive，说明我方更快
        elif ctx.enemy_inactive > 0 and ctx.my_inactive == 0:
            ctx.set_slower(False)


EventRegistry.register(
    event=Events.DOTS_CHANGED,
    handler_cls=DotsChangedHandler,
    template=["dots/dot_active.png", "dots/dot_inactive.png"],
    region=(140, 100, 2490, 170),
    similarity=0.8
)
