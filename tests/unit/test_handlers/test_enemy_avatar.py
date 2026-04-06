from unittest.mock import Mock


class MockGameContext:
    pass


class TestEnemyAvatarHandler:
    def test_handle_does_nothing(self):
        """验证 EnemyAvatarHandler 正确初始化"""
        from src.handlers.enemy_avatar import EnemyAvatarHandler

        mock_dispatcher = Mock()
        mock_dispatcher.controller = Mock()
        mock_dispatcher.elf_manager = Mock()
        mock_dispatcher.skill_executor = Mock()

        handler = EnemyAvatarHandler(mock_dispatcher)
        ctx = MockGameContext()

        # 此 Handler 主要用于标记敌方精灵出现，不做实际操作
        handler.handle(ctx)