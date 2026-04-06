"""错误处理器"""
import time

from src.handlers.base_handler import Handler
from src.state_machine import BattleState
from loguru import logger


class ErrorHandler(Handler):
    """ERROR 状态处理器"""

    def handle(self) -> bool:
        """处理错误：记录日志、保存截图、重置状态"""
        logger.error("进入 ERROR 状态")

        # 保存调试截图
        self.ctrl.save_debug_screenshot(f"error_{int(time.time())}")

        # 重置状态为 IDLE，准备重试
        self.transition(BattleState.IDLE)
        return True
