"""技能释放处理器"""
import time

from loguru import logger

from src.handlers.base_handler import Handler
from src.context import GameContext
from src.events import Events
from src.registry import EventRegistry


class SkillCastableHandler(Handler):
    """技能可释放处理器

    根据游戏状态决定释放彗星还是防御技能：
    - 防御技能有冷却期，如果应该释放防御但识图失败，则尝试释放聚能
    """

    CASTABLE_REGION = (0, 1000, 318, 1440)
    SELF_DESTRUCT_CHECK_DURATION = 5  # 自爆流检测持续时间（秒）
    # 敌方头像区域 - 覆盖右上角敌方状态栏
    ENEMY_AVATAR_REGION = (2090, 14, 2273, 181)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._selfdestruct_checked = False  # 是否已检测过自爆流

    def reset(self) -> None:
        """重置状态（每场新战斗开始时调用）"""
        self._selfdestruct_checked = False

    def handle(self, ctx: GameContext, position=None) -> None:
        """处理技能可释放事件

        Args:
            ctx: 游戏共享状态上下文
            position: energy
        """
        # 第一次可释放技能时，检测敌方是否是自爆流
        if not self._selfdestruct_checked:
            self._selfdestruct_checked = True
            if self._check_enemy_selfdestruct(ctx):
                ctx.enemy_self_destruct = True
                logger.info("敌方是自爆流，继续战斗")
            else:
                logger.info("敌方不是自爆流，执行逃跑")
                ctx.skill_executor.escape_battle()
                return

        # 决定应该释放什么技能
        should_cast_defense = self._should_cast_defense(ctx)

        if should_cast_defense:
            # 尝试释放防御
            if self._try_cast_defense():
                return
            # 防御识图失败（可能在冷却），释放聚能
            logger.info("防御冷却中，释放聚能技能")
            self.ctrl.click_at(*position)
            time.sleep(1)
        else:
            # 释放彗星技能
            if self.ctrl.find_and_click_with_timeout("skills/comet.png", timeout=3):
                logger.info("释放彗星")
                time.sleep(1)
            else:
                logger.warning("彗星技能位置未找到")

    def _should_cast_defense(self, ctx: GameContext) -> bool:
        """判断是否应该释放防御技能

        Args:
            ctx: 游戏上下文

        Returns:
            是否应该释放防御
        """
        if ctx.my_inactive == 0 and ctx.enemy_inactive == 0:
            return False
        if ctx.is_slower():
            return ctx.enemy_inactive < 3
        else:
            return ctx.my_inactive >= 3

    def _try_cast_defense(self) -> bool:
        if self.ctrl.find_and_click_with_timeout("skills/defense.png", timeout=3):
            logger.info("释放防御")
            time.sleep(1)
            return True
        logger.debug("防御技能图标未找到（可能在冷却中）")
        return False

    def _check_enemy_selfdestruct(self, ctx: GameContext) -> bool:
        """检测敌方是否是自爆流

        Args:
            ctx: 游戏上下文

        Returns:
            True=敌方是自爆流，False=不是自爆流
        """
        selfdestruct_templates = ctx.elf_manager.get_selfdestruct_templates()
        if not selfdestruct_templates:
            logger.warning("未配置 selfdestruct_enemies 列表，假设是自爆流")
            return True

        start_time = time.time()
        logger.info(f"开始检测敌方是否是自爆流，模板列表: {selfdestruct_templates}")

        x0, y0, x1, y1 = self.ENEMY_AVATAR_REGION
        while time.time() - start_time < self.SELF_DESTRUCT_CHECK_DURATION:
            # 遍历所有自爆流敌方模板检测
            for template in selfdestruct_templates:
                pos = self.ctrl.find_image(template, similarity=0.75, x0=x0, y0=y0, x1=x1, y1=y1)
                if pos != (-1, -1):
                    logger.info(f"检测到自爆流敌方: {template} @ {pos}")
                    return True
            time.sleep(0.5)

        logger.info("连续5秒未检测到自爆流敌方头像，判断不是自爆流")
        return False



EventRegistry.register(
    event=Events.SKILL_CASTABLE,
    handler_cls=SkillCastableHandler,
    template="skills/energy.png",
    region=SkillCastableHandler.CASTABLE_REGION,
    similarity=0.7
)
