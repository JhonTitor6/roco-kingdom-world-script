import pytest
from unittest.mock import Mock, MagicMock


class TestEventDetector:
    """EventDetector 测试"""

    def test_scan_all_returns_detected_events_with_position(self):
        """验证 scan_all 返回触发的事件及坐标"""
        from src.detector import EventDetector, DetectedEvent
        from src.events import Events
        from src.event_config import EventConfig

        mock_controller = Mock()
        mock_controller.find_image = Mock(side_effect=[
            (100, 200),  # COMET_APPEARED 触发
            None,         # DEFENSE_APPEARED 不触发
        ])
        mock_controller.elf_manager = Mock()

        config = {
            Events.COMET_APPEARED: EventConfig("a.png", (0,0,1,1), 0.8),
            Events.DEFENSE_APPEARED: EventConfig("b.png", (0,0,1,1), 0.8),
        }

        detector = EventDetector(mock_controller, config)
        detected = detector.scan_all()

        assert len(detected) == 1
        assert detected[0].event == Events.COMET_APPEARED
        assert detected[0].position == (100, 200)
