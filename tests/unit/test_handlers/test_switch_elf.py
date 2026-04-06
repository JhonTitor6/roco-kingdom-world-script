import pytest
from unittest.mock import Mock

class MockGameContext:
    """模拟 GameContext"""
    def __init__(self):
        self.slower = False
        self.sacrifice = False
        self.my_inactive = 0
        self.enemy_inactive = 0

    def is_slower(self):
        return self.slower

    def is_sacrifice(self):
        return self.sacrifice

class TestSwitchElfHandler:
    """SwitchElfHandler 测试"""

    def test_handle_sacrifice_clicks_sacrifice_elf(self):
        """验证 sacrifice 状态点击送死精灵"""
        from src.handlers.switch_elf import SwitchElfHandler

        mock_dispatcher = Mock()
        mock_dispatcher.controller = Mock()
        mock_dispatcher.controller.find_and_click = Mock()
        mock_dispatcher.elf_manager = Mock()
        mock_dispatcher.elf_manager.get_sacrifice_template = Mock(return_value="elves/pig3.png")
        mock_dispatcher.skill_executor = Mock()

        handler = SwitchElfHandler(mock_dispatcher)
        ctx = MockGameContext()
        ctx.sacrifice = True

        handler.handle(ctx)

        mock_dispatcher.elf_manager.get_sacrifice_template.assert_called_once()
        mock_dispatcher.controller.find_and_click.assert_called_once()

    def test_handle_slower_clicks_reserve_elf(self):
        """验证 slower 状态点击 reserve 精灵"""
        from src.handlers.switch_elf import SwitchElfHandler

        mock_dispatcher = Mock()
        mock_dispatcher.controller = Mock()
        mock_dispatcher.controller.find_and_click = Mock()
        mock_dispatcher.elf_manager = Mock()
        mock_dispatcher.elf_manager.get_reserve_template = Mock(return_value="elves/scepter3.png")
        mock_dispatcher.skill_executor = Mock()

        handler = SwitchElfHandler(mock_dispatcher)
        ctx = MockGameContext()
        ctx.slower = True
        ctx.my_inactive = 0

        handler.handle(ctx)

        mock_dispatcher.elf_manager.get_reserve_template.assert_called_once()
        mock_dispatcher.controller.find_and_click.assert_called_once()
