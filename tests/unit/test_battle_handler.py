import unittest
from unittest.mock import MagicMock, patch


class TestFasterDecisionTable(unittest.TestCase):
    """测试 FASTER 流程决策表"""

    def setUp(self):
        from src.handlers.battle import BattleHandler, FlowType
        from src.event_dispatcher import EventDispatcher

        self.mock_dispatcher = MagicMock(spec=EventDispatcher)
        self.mock_dispatcher.flow_type = FlowType.FASTER
        self.mock_dispatcher.controller = MagicMock()
        self.mock_dispatcher.elf_manager = MagicMock()
        self.mock_dispatcher.skill_executor = MagicMock()

        # 设置 sacrifice_elves 和 reserve_elf
        self.mock_dispatcher.elf_manager.sacrifice_elves = [
            {"name": "sac1", "template": "tree3.png"},
            {"name": "sac2", "template": "otter2.png"},
            {"name": "sac3", "template": "pig3.png"},
        ]
        self.mock_dispatcher.elf_manager.reserve_elf = {"name": "reserve", "template": "scepter3.png"}

        self.handler = BattleHandler(self.mock_dispatcher)

    def test_ally_dots_0_returns_switch_and_cast_first_sacrifice(self):
        from src.handlers.battle import Action
        action, elf = self.handler._faster_decide(0)
        self.assertEqual(action, Action.SWITCH_AND_CAST)
        self.assertEqual(elf["name"], "sac1")

    def test_ally_dots_1_returns_switch_and_cast_second_sacrifice(self):
        from src.handlers.battle import Action
        action, elf = self.handler._faster_decide(1)
        self.assertEqual(action, Action.SWITCH_AND_CAST)
        self.assertEqual(elf["name"], "sac2")

    def test_ally_dots_2_returns_switch_and_cast_third_sacrifice(self):
        from src.handlers.battle import Action
        action, elf = self.handler._faster_decide(2)
        self.assertEqual(action, Action.SWITCH_AND_CAST)
        self.assertEqual(elf["name"], "sac3")

    def test_ally_dots_3_returns_switch_reserve(self):
        from src.handlers.battle import Action
        action, elf = self.handler._faster_decide(3)
        self.assertEqual(action, Action.SWITCH)
        self.assertEqual(elf["name"], "reserve")

    def test_ally_dots_4_returns_wait(self):
        from src.handlers.battle import Action
        action, elf = self.handler._faster_decide(4)
        self.assertEqual(action, Action.WAIT)
        self.assertIsNone(elf)


if __name__ == "__main__":
    unittest.main()
