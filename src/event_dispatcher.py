"""事件分发器"""
from src.state_machine import BattleState
from src.handlers import (
    StartChallengeHandler,
    SelectElfHandler,
    ConfirmHandler,
    BattleHandler,
    BattleEndHandler,
    RetryHandler,
    ErrorHandler,
)


# 状态到处理器的映射
HANDLERS = {
    BattleState.START_CHALLENGE: StartChallengeHandler,
    BattleState.SELECT_FIRST: SelectElfHandler,
    BattleState.CONFIRM_FIRST: ConfirmHandler,
    BattleState.BATTLE_START: BattleHandler,
    BattleState.SPEED_CHECK: BattleHandler,
    BattleState.SACRIFICE_PHASE: BattleHandler,
    BattleState.FINAL_PHASE: BattleHandler,
    BattleState.BATTLE_END: BattleEndHandler,
    BattleState.RETRY: RetryHandler,
    BattleState.QUIT: RetryHandler,
    BattleState.ERROR: ErrorHandler,
}


class EventDispatcher:
    """事件分发器: 主循环 + 图像检测 + 处理器调用"""

    # 区域定义
    ALLY_REGION = (0, 0, 700, 320)
    ENEMY_REGION = (2000, 0, 2560, 320)

    def __init__(
        self,
        controller,
        elf_manager,
        skill_executor,
        settings: dict
    ):
        self.controller = controller
        self.elf_manager = elf_manager
        self.skill_executor = skill_executor
        self.settings = settings
        self.state = BattleState.IDLE

    def run(self, loop_count: int) -> None:
        """运行主循环"""
        for i in range(loop_count):
            # 重置 flow_type（每轮重新检测速度）
            self._flow_type = None

            # 1. 自启动检测（仅第一次）
            if i == 0:
                self.state = self._auto_detect_initial_state()
            else:
                self.state = BattleState.IDLE

            # 2. 主循环
            while not self._is_terminal_state():
                # 捕获画面
                self.controller.capture()

                # 获取当前状态的处理器并执行
                handler_class = HANDLERS.get(self.state)
                if handler_class:
                    handler = handler_class(self)
                    if not handler.handle():
                        # Handler 返回 False 进入 ERROR 状态
                        self.state = BattleState.ERROR
                        break

                # 短暂休眠
                self._sleep(0.3)

    def _is_terminal_state(self) -> bool:
        """判断是否为终止状态"""
        return self.state == BattleState.QUIT

    def _sleep(self, seconds: float) -> None:
        """休眠（复用现有 random_sleep）"""
        from src.utils import random_sleep
        random_sleep(seconds)

    def _auto_detect_initial_state(self) -> BattleState:
        """自启动检测当前游戏画面状态"""
        self.controller.capture()

        # 按优先级检测
        if self.controller.find_image("battle/battle_end.png", similarity=0.9) != (-1, -1):
            return BattleState.BATTLE_END
        if self.controller.find_image("battle/retry.png", similarity=0.8) != (-1, -1):
            return BattleState.RETRY
        if self.controller.find_image("battle/opponent_dont_want_to_retry.png", similarity=0.8) != (-1, -1):
            return BattleState.QUIT
        if self.controller.find_image("battle/start_challenge.png", similarity=0.8) != (-1, -1):
            return BattleState.START_CHALLENGE
        if self.controller.find_image("battle/confirm_lineups.png", similarity=0.8) != (-1, -1):
            return BattleState.SELECT_FIRST

        # comet.png 存在 → 战斗中，根据 dot 推断
        if self.controller.find_image("skills/comet.png", similarity=0.8) != (-1, -1):
            ally = self._count_inactive_ally()
            enemy = self._count_inactive_enemy()
            if ally == 0 and enemy == 0:
                return BattleState.SPEED_CHECK
            if ally >= 1:
                # faster 流程（我方已送死 >= 1）
                self._set_flow_type("faster")
                return BattleState.SACRIFICE_PHASE
            if ally == 0 and enemy >= 1:
                # slower 流程中途
                self._set_flow_type("slower")
                return BattleState.SACRIFICE_PHASE
            if ally == 0 and enemy >= 3:
                # 敌方已送死3只，我方未动 → FINAL_PHASE
                return BattleState.FINAL_PHASE

        return BattleState.IDLE

    def _count_inactive_ally(self) -> int:
        """统计我方 inactive dots"""
        dots = self.controller.find_images_all(
            "dots/dot_inactive.png",
            similarity=0.8,
            x0=self.ALLY_REGION[0], y0=self.ALLY_REGION[1],
            x1=self.ALLY_REGION[2], y1=self.ALLY_REGION[3]
        )
        return len(dots)

    def _count_inactive_enemy(self) -> int:
        """统计敌方 inactive dots"""
        dots = self.controller.find_images_all(
            "dots/dot_inactive.png",
            similarity=0.8,
            x0=self.ENEMY_REGION[0], y0=self.ENEMY_REGION[1],
            x1=self.ENEMY_REGION[2], y1=self.ENEMY_REGION[3]
        )
        return len(dots)

    @property
    def flow_type(self):
        """获取流程类型"""
        return self._flow_type

    def _set_flow_type(self, flow_type: str) -> None:
        """设置流程类型（供中途启动时使用）"""
        # FlowType 枚举需要从 battle handler 导入
        from src.handlers.battle import FlowType
        self._flow_type = FlowType.FASTER if flow_type == "faster" else FlowType.SLOWER
