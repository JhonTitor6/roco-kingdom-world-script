"""技能执行器"""
import time
from loguru import logger

from src.utils import random_sleep

from src.controller import GameController


class SkillExecutor:
    """执行技能和精灵切换"""

    def __init__(self, controller: GameController):
        self.ctrl = controller

    def escape_battle(self) -> bool:
        """执行逃跑操作：点击 escape.png → confirm.png

        Returns:
            是否成功
        """
        if not self.ctrl.find_and_click_with_timeout("skills/escape.png", timeout=2, similarity=0.8):
            logger.warning("逃跑图标未找到，点击固定坐标")
            self.ctrl.click_at(2046, 1320)

        random_sleep(1)
        if not self.ctrl.find_and_click_with_timeout("popup/yes.png", timeout=2, similarity=0.8):
            logger.warning("逃跑确认按钮未找到")
            self.ctrl.click_at(1486, 1185)
        logger.info("执行逃跑")
        return True
