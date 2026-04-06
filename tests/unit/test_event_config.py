import pytest
from dataclasses import dataclass
from typing import Union, List
from src.event_config import EventConfig

def test_event_config_creation():
    """验证 EventConfig 创建"""
    config = EventConfig(
        template="skills/comet.png",
        region=(0, 0, 2560, 1440),
        similarity=0.8
    )
    assert config.template == "skills/comet.png"
    assert config.region == (0, 0, 2560, 1440)
    assert config.similarity == 0.8

def test_event_config_list_template():
    """验证 EventConfig 支持列表模板"""
    config = EventConfig(
        template=["elves/tree3.png", "elves/otter2.png"],
        region=(0, 0, 700, 320),
        similarity=0.7
    )
    assert isinstance(config.template, list)
    assert len(config.template) == 2