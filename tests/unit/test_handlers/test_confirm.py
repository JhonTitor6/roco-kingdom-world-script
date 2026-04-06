from unittest.mock import Mock


class MockGameContext:
    pass


class TestConfirmHandler:
    def test_handle_clicks_confirm(self):
        from src.handlers.confirm import ConfirmHandler

        mock_dispatcher = Mock()
        mock_dispatcher.controller = Mock()
        mock_dispatcher.controller.find_and_click = Mock()
        mock_dispatcher.elf_manager = Mock()
        mock_dispatcher.skill_executor = Mock()

        handler = ConfirmHandler(mock_dispatcher)
        ctx = MockGameContext()

        handler.handle(ctx)

        mock_dispatcher.controller.find_and_click.assert_called_once()
