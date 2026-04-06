import pytest
from unittest.mock import Mock


class TestEventDispatcher:
    """EventDispatcher 测试"""

    def test_register_handler(self):
        """验证注册处理器"""
        from src.event_dispatcher import EventDispatcher
        from src.events import Events

        mock_controller = Mock()
        mock_elf_manager = Mock()
        mock_skill_executor = Mock()

        dispatcher = EventDispatcher(
            mock_controller, mock_elf_manager, mock_skill_executor, {}
        )

        class MockHandler:
            def handle(self, ctx):
                pass

        dispatcher.register_handler(Events.COMET_APPEARED, MockHandler())

        assert Events.COMET_APPEARED in dispatcher.handlers

    def test_stop_sets_running_false(self):
        """验证 stop 方法"""
        from src.event_dispatcher import EventDispatcher

        dispatcher = EventDispatcher(Mock(), Mock(), Mock(), {})
        dispatcher.running = True

        dispatcher.stop()

        assert dispatcher.running == False