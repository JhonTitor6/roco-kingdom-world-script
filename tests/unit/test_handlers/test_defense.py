import pytest
from unittest.mock import Mock


class MockGameContext:
    """模拟 GameContext"""
    pass


class TestDefenseAppearedHandler:
    """DefenseAppearedHandler 测试"""

    def test_handle_calls_cast_defense(self):
        """验证调用 cast_defense"""
        from src.handlers.defense import DefenseAppearedHandler

        mock_dispatcher = Mock()
        mock_dispatcher.controller = Mock()
        mock_dispatcher.elf_manager = Mock()
        mock_dispatcher.skill_executor = Mock()
        mock_dispatcher.skill_executor.press_defense = Mock()

        handler = DefenseAppearedHandler(mock_dispatcher)
        ctx = MockGameContext()

        handler.handle(ctx)

        mock_dispatcher.skill_executor.press_defense.assert_called_once()