from unittest.mock import Mock


class MockGameContext:
    def __init__(self):
        self.my_inactive = 0
        self.enemy_inactive = 0
        self._slower = False

    def set_slower(self, value):
        self._slower = value

    def is_slower(self):
        return self._slower


class TestSpeedCheckHandler:
    def test_handle_sets_slower_when_enemy_faster(self):
        """验证敌方更快时设置 slower=True"""
        from src.handlers.speed_check import SpeedCheckHandler

        mock_dispatcher = Mock()
        mock_dispatcher.controller = Mock()
        mock_dispatcher.elf_manager = Mock()
        mock_dispatcher.skill_executor = Mock()

        handler = SpeedCheckHandler(mock_dispatcher)
        ctx = MockGameContext()
        ctx.my_inactive = 1
        ctx.enemy_inactive = 0

        handler.handle(ctx)

        assert ctx.is_slower() == True

    def test_handle_sets_faster_when_our_faster(self):
        """验证我方更快时设置 slower=False"""
        from src.handlers.speed_check import SpeedCheckHandler

        mock_dispatcher = Mock()
        mock_dispatcher.controller = Mock()
        mock_dispatcher.elf_manager = Mock()
        mock_dispatcher.skill_executor = Mock()

        handler = SpeedCheckHandler(mock_dispatcher)
        ctx = MockGameContext()
        ctx.my_inactive = 0
        ctx.enemy_inactive = 1

        handler.handle(ctx)

        assert ctx.is_slower() == False
