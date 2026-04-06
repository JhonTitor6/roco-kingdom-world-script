"""Events 枚举测试"""
import pytest
from src.events import Events


class TestEvents:
    """验证 Events 枚举的所有值"""

    def test_comet_appeared(self):
        assert Events.COMET_APPEARED.value == "comet_appeared"

    def test_defense_appeared(self):
        assert Events.DEFENSE_APPEARED.value == "defense_appeared"

    def test_battle_end(self):
        assert Events.BATTLE_END.value == "battle_end"

    def test_start_challenge(self):
        assert Events.START_CHALLENGE.value == "start_challenge"

    def test_retry(self):
        assert Events.RETRY.value == "retry"

    def test_confirm(self):
        assert Events.CONFIRM.value == "confirm"

    def test_enemy_avatar(self):
        assert Events.ENEMY_AVATAR.value == "enemy_avatar"

    def test_ally_avatar(self):
        assert Events.ALLY_AVATAR.value == "ally_avatar"

    def test_switch_elf(self):
        assert Events.SWITCH_ELF.value == "switch_elf"

    def test_enemy_self_destruct(self):
        assert Events.ENEMY_SELF_DESTRUCT.value == "enemy_self_destruct"

    def test_dots_changed(self):
        assert Events.DOTS_CHANGED.value == "dots_changed"

    def test_speed_check(self):
        assert Events.SPEED_CHECK.value == "speed_check"

    def test_total_events_count(self):
        """验证总共有 12 个事件"""
        assert len(Events) == 12