"""战斗结束处理器"""
from src.handlers.base_handler import Handler
from src.state_machine import BattleState
from src.utils import random_sleep
from loguru import logger


class BattleEndHandler(Handler):
    """BATTLE_END 状态处理器"""

    def handle(self) -> bool:
        """处理战斗结束，点击再次切磋"""
        # 点击战斗结束按钮
        battle_end = self.ctrl.find_image_with_timeout(
            "battle/battle_end.png",
            timeout=self.ctrl.settings["timeouts"]["battle_end"],
            similarity=0.9
        )
        if battle_end is None:
            logger.warning("未检测到战斗结束标志")
            return False

        logger.info("战斗结束")
        self.ctrl.click_at(*battle_end)

        # 点击再次切磋
        if self.ctrl.find_and_click_with_timeout("battle/retry.png", timeout=3):
            random_sleep(10)

        # 检测对手是否不想再切磋
        if self.ctrl.find_image_with_timeout(
            "battle/opponent_dont_want_to_retry.png", timeout=10
        ) is not None:
            # 对手不想再切磋 → 点击退出
            self.ctrl.find_and_click_with_timeout("battle/quit.png", timeout=2)
            self.transition(BattleState.QUIT)
        else:
            # 可以继续 → 进入 RETRY 状态等待
            self.transition(BattleState.RETRY)

        return True
