import pytest
from dataclasses import dataclass
from typing import Optional

@dataclass
class MockDispatcher:
    """模拟 EventDispatcher 用于测试"""
    controller = None
    elf_manager = None
    skill_executor = None

class TestGameContext:
    """GameContext 单元测试"""

    def test_set_slower_and_is_slower(self):
        """验证 slower 状态设置和获取"""
        from src.context import GameContext

        ctx = GameContext(dispatcher=MockDispatcher())
        assert ctx.slower == False

        ctx.set_slower(True)
        assert ctx.slower == True
        assert ctx.is_slower() == True

        ctx.set_slower(False)
        assert ctx.slower == False

    def test_set_sacrifice_and_is_sacrifice(self):
        """验证 sacrifice 状态设置和获取"""
        from src.context import GameContext

        ctx = GameContext(dispatcher=MockDispatcher())
        assert ctx.sacrifice == False

        ctx.set_sacrifice(True)
        assert ctx.sacrifice == True
        assert ctx.is_sacrifice() == True

    def test_update_inactive(self):
        """验证 inactive 数量更新"""
        from src.context import GameContext

        ctx = GameContext(dispatcher=MockDispatcher())
        ctx.update_inactive(my=2, enemy=1)

        assert ctx.my_inactive == 2
        assert ctx.enemy_inactive == 1

    def test_default_values(self):
        """验证默认值"""
        from src.context import GameContext

        ctx = GameContext(dispatcher=MockDispatcher())

        assert ctx.slower == False
        assert ctx.sacrifice == False
        assert ctx.my_inactive == 0
        assert ctx.enemy_inactive == 0