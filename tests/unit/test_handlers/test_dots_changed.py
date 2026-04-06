from unittest.mock import Mock


class MockGameContext:
    def __init__(self):
        self.my_inactive = 0
        self.enemy_inactive = 0

    def update_inactive(self, my, enemy):
        self.my_inactive = my
        self.enemy_inactive = enemy


class TestDotsChangedHandler:
    def test_handle_updates_inactive_counts(self):
        """验证更新 inactive dot 数量"""
        from src.handlers.dots_changed import DotsChangedHandler

        mock_dispatcher = Mock()
        mock_dispatcher.controller = Mock()
        mock_dispatcher.controller.find_images_all = Mock(side_effect=[
            [1, 2, 3],  # my_active
            [4, 5],     # enemy_inactive
        ])
        mock_dispatcher.elf_manager = Mock()
        mock_dispatcher.skill_executor = Mock()

        handler = DotsChangedHandler(mock_dispatcher)
        ctx = MockGameContext()

        handler.handle(ctx)

        assert ctx.my_inactive == 3
        assert ctx.enemy_inactive == 2
