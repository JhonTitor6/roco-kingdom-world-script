from unittest.mock import Mock


class MockGameContext:
    pass


class TestEnemySelfDestructHandler:
    def test_handle_escapes_and_stops(self):
        """验证检测到自爆流后逃跑并停止"""
        from src.handlers.enemy_self_destruct import EnemySelfDestructHandler

        mock_dispatcher = Mock()
        mock_dispatcher.controller = Mock()
        mock_dispatcher.elf_manager = Mock()
        mock_dispatcher.skill_executor = Mock()
        mock_dispatcher.skill_executor.escape_battle = Mock()
        mock_dispatcher.running = True

        handler = EnemySelfDestructHandler(mock_dispatcher)
        ctx = MockGameContext()

        handler.handle(ctx)

        mock_dispatcher.skill_executor.escape_battle.assert_called_once()
        mock_dispatcher.stop.assert_called_once()
