from enum import Enum
from typing import Union, List

class Events(Enum):
    """事件枚举"""
    # 技能相关
    COMET_APPEARED = "comet_appeared"
    DEFENSE_APPEARED = "defense_appeared"

    # 战斗流程
    BATTLE_END = "battle_end"
    START_CHALLENGE = "start_challenge"
    RETRY = "retry"
    CONFIRM = "confirm"

    # 精灵相关
    ENEMY_AVATAR = "enemy_avatar"
    ALLY_AVATAR = "ally_avatar"
    SWITCH_ELF = "switch_elf"

    # 状态检测
    ENEMY_SELF_DESTRUCT = "enemy_self_destruct"
    DOTS_CHANGED = "dots_changed"
