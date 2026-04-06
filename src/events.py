"""事件定义枚举"""
from enum import Enum, auto


class Event(Enum):
    """战斗相关事件"""
    START_CHALLENGE_DETECTED = auto()
    CONFIRM_LINEUPS_DETECTED = auto()
    CONFIRM_DETECTED = auto()
    COMET_DETECTED = auto()
    BATTLE_END_DETECTED = auto()
    RETRY_DETECTED = auto()
    OPPONENT_QUIT_DETECTED = auto()
    INSUFFICIENT_DETECTED = auto()
    SWITCH_PANEL_DETECTED = auto()
