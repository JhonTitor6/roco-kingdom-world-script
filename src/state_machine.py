"""战斗状态枚举"""
from enum import Enum, auto


class BattleState(Enum):
    """战斗状态枚举"""
    IDLE = "idle"                      # 等待开始
    START_CHALLENGE = "start_challenge"  # 已点击开始挑战
    SELECT_FIRST = "select_first"        # 选择首发精灵
    CONFIRM_FIRST = "confirm_first"     # 确认首发
    BATTLE_START = "battle_start"       # 等待战斗开始
    SPEED_CHECK = "speed_check"         # 检测速度优势
    SACRIFICE_PHASE = "sacrifice_phase"  # 送死阶段（faster/slower）
    FINAL_PHASE = "final_phase"         # 最终精灵阶段
    BATTLE_END = "battle_end"            # 战斗结束
    RETRY = "retry"                     # 再次切磋
    QUIT = "quit"                       # 退出（本轮结束）
    ERROR = "error"                     # 错误（异常时触发，重试本轮）


class SacrificeSubState(Enum):
    """SACRIFICE_PHASE 的子状态（供内部决策使用）"""
    FASTER = auto()                    # FASTER 流程（仅用于标记，不做状态机转换）
    SLOWER_DEFENSE = auto()            # SLOWER 防御期
    SLOWER_SAC = auto()                # SLOWER 送死期
    SLOWER_RESERVE = auto()            # SLOWER 切换 reserve
    SLOWER_FINAL = auto()              # SLOWER final 送死
