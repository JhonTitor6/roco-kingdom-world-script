import pytest
from unittest.mock import Mock, MagicMock


class MockGameContext:
    """模拟 GameContext"""
    def __init__(self):
        self.slower = False
        self.sacrifice = False
        self.my_inactive = 0
        self.enemy_inactive = 0

    def set_slower(self, value):
        self.slower = value

    def is_slower(self):
        return self.slower

    def set_sacrifice(self, value):
        self.sacrifice = value

    def is_sacrifice(self):
        return self.sacrifice

    def update_inactive(self, my, enemy):
        self.my_inactive = my
        self.enemy_inactive = enemy


class TestCometAppearedHandler:
    """CometAppearedHandler 测试"""

    def test_handle_sets_sacrifice_when_slower_and_specific_inactive(self):
        """验证 slower 且特定 inactive 条件时设置 sacrifice"""
        from src.handlers.comet import CometAppearedHandler

        mock_dispatcher = Mock()
        mock_dispatcher.controller = Mock()
        mock_dispatcher.elf_manager = Mock()
        mock_dispatcher.skill_executor = Mock()
        mock_dispatcher.skill_executor.cast_skill = Mock()

        handler = CometAppearedHandler(mock_dispatcher)
        ctx = MockGameContext()
        ctx.slower = True
        ctx.my_inactive = 0
        ctx.enemy_inactive = 1

        handler.handle(ctx)

        assert ctx.sacrifice == True
        mock_dispatcher.skill_executor.cast_skill.assert_called_once_with("comet")

    def test_handle_calls_cast_comet(self):
        """验证调用 cast_comet"""
        from src.handlers.comet import CometAppearedHandler

        mock_dispatcher = Mock()
        mock_dispatcher.controller = Mock()
        mock_dispatcher.elf_manager = Mock()
        mock_dispatcher.skill_executor = Mock()
        mock_dispatcher.skill_executor.cast_skill = Mock()

        handler = CometAppearedHandler(mock_dispatcher)
        ctx = MockGameContext()

        handler.handle(ctx)

        mock_dispatcher.skill_executor.cast_skill.assert_called_once_with("comet")