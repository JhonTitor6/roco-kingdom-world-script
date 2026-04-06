"""重试处理器"""
from src.handlers.base_handler import Handler
from src.state_machine import BattleState
from src.utils import random_sleep
from loguru import logger


class RetryHandler(Handler):
    """RETRY / QUIT 状态处理器"""

    def handle(self) -> bool:
        """处理再次切磋或退出"""
        state = self.dispatcher.state

        if state == BattleState.RETRY:
            logger.info("等待再次切磋")
            # 等待 start_challenge.png 出现
            if self.ctrl.find_image_with_timeout(
                "battle/start_challenge.png", timeout=60
            ):
                self.transition(BattleState.START_CHALLENGE)
            else:
                return False

        elif state == BattleState.QUIT:
            logger.info("本轮结束")
            # 点击退出
            self.ctrl.find_and_click_with_timeout("battle/quit.png", timeout=2)
            random_sleep(2)
            # 重置状态，退出本轮循环

        return True
