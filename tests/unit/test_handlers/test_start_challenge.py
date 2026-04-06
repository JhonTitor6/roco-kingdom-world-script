from unittest.mock import Mock


class MockGameContext:
    pass


class TestStartChallengeHandler:
    def test_handle_clicks_start_challenge(self):
        from src.handlers.start_challenge import StartChallengeHandler

        mock_dispatcher = Mock()
        mock_dispatcher.controller = Mock()
        mock_dispatcher.controller.find_and_click = Mock()
        mock_dispatcher.elf_manager = Mock()
        mock_dispatcher.skill_executor = Mock()

        handler = StartChallengeHandler(mock_dispatcher)
        ctx = MockGameContext()

        handler.handle(ctx)

        mock_dispatcher.controller.find_and_click.assert_called_once()
