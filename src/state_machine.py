"""状态机"""
import time
from enum import Enum
from loguru import logger

from src.battle_flow import BattleFlow
from src.exceptions import GameWindowNotFoundError


class BattleState(Enum):
    """战斗状态枚举"""
    IDLE = "idle"
    START_CHALLENGE = "start_challenge"
    CHECK_INSUFFICIENT = "check_insufficient"
    SELECT_FIRST = "select_first"
    CONFIRM_FIRST = "confirm_first"
    BATTLE_START = "battle_start"
    SPEED_CHECK = "speed_check"
    SACRIFICE_PHASE = "sacrifice_phase"
    FINAL_PHASE = "final_phase"
    SWITCH_ELF = "switch_elf"
    BATTLE_END = "battle_end"
    RETRY = "retry"
    QUIT = "quit"
    ERROR = "error"


class BattleStateMachine:
    """战斗状态机"""

    def __init__(self, battle_flow: BattleFlow):
        self.state = BattleState.IDLE
        self.flow = battle_flow
        self.error_count = 0
        self.max_errors = 3

    def transition(self, new_state: BattleState) -> None:
        """状态切换"""
        logger.debug(f"状态: {self.state.value} -> {new_state.value}")
        self.state = new_state

    def run(self, loop_count: int) -> None:
        """运行主循环"""
        for i in range(loop_count):
            logger.info(f"========== 第 {i+1}/{loop_count} 轮 ==========")
            success = self._run_one_round()
            if not success:
                self.error_count += 1
                logger.warning(f"第 {i+1} 轮执行失败 (error_count={self.error_count})")
                if self.error_count >= self.max_errors:
                    logger.error("连续错误过多，停止脚本")
                    break
                time.sleep(2)  # 出错后等待
            else:
                self.error_count = 0  # 成功后重置计数

        logger.info(f"完成 {loop_count} 轮")

    def _run_one_round(self) -> bool:
        """执行一轮战斗"""
        try:
            self.transition(BattleState.START_CHALLENGE)

            # 进入战斗流程
            if not self.flow.run_entry_flow():
                logger.error("进入战斗失败")
                return False

            self.transition(BattleState.SPEED_CHECK)

            # 释放彗星技能（等待时间由 skill_wait_after_cast 配置）
            self.flow.skill.cast_skill("comet")

            # 检测速度优势
            faster = self.flow.detect_speed_advantage()

            self.transition(BattleState.SACRIFICE_PHASE)

            # 执行对应流程
            if faster:
                self.flow.faster_flow()
            else:
                self.flow.slower_flow()

            self.transition(BattleState.BATTLE_END)

            # 处理战斗结束
            return self.flow.handle_battle_end()

        except GameWindowNotFoundError:
            logger.error("游戏窗口已关闭")
            raise
        except Exception as e:
            logger.exception(f"执行异常: {e}")
            self.transition(BattleState.ERROR)

            # 保存调试截图
            self.flow.ctrl.save_debug_screenshot(f"error_{int(time.time())}")

            return False
