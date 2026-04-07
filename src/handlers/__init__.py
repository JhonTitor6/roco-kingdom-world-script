"""事件处理器包"""
from src.handlers.base_handler import Handler
from src.handlers.comet import CometAppearedHandler
from src.handlers.defense import DefenseAppearedHandler
from src.handlers.battle_end import BattleEndHandler
from src.handlers.start_challenge import StartChallengeHandler
from src.handlers.confirm import ConfirmHandler
from src.handlers.retry import RetryHandler
from src.handlers.switch_elf import SwitchElfHandler
from src.handlers.dots_changed import DotsChangedHandler
from src.handlers.enemy_self_destruct import EnemySelfDestructHandler
from src.handlers.enemy_avatar import EnemyAvatarHandler

__all__ = [
    "Handler",
    "CometAppearedHandler",
    "DefenseAppearedHandler",
    "BattleEndHandler",
    "StartChallengeHandler",
    "ConfirmHandler",
    "RetryHandler",
    "SwitchElfHandler",
    "DotsChangedHandler",
    "EnemySelfDestructHandler",
    "EnemyAvatarHandler",
]
