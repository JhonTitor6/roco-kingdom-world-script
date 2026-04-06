"""开始挑战处理器"""
from src.handlers.base_handler import Handler
from src.state_machine import BattleState
from src.utils import random_sleep


class StartChallengeHandler(Handler):
    """START_CHALLENGE 状态处理器"""

    def handle(self) -> bool:
        """点击开始挑战，等待进入选精灵界面"""
        # 点击开始挑战
        if not self.ctrl.find_and_click_with_timeout(
            "battle/start_challenge.png", timeout=5
        ):
            # 按钮不存在，可能已处于其他状态
            return True  # 继续循环检测

        random_sleep(1)

        # 检查精灵数不足弹窗
        insufficient_pos = self.ctrl.find_image_with_timeout(
            "popup/insufficient.png", timeout=3, similarity=0.8
        )
        if insufficient_pos is not None:
            self.ctrl.find_and_click_with_timeout("popup/confirm.png", timeout=3)

        # 等待匹配画面出现
        random_sleep(5)

        # 切换到 SELECT_FIRST 状态
        self.transition(BattleState.SELECT_FIRST)
        return True
