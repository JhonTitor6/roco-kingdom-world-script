import pytest
from src.events import Events
from src.event_config import EventConfig

class MockHandler:
    """模拟 Handler 用于测试"""
    pass

def test_registry_register():
    """验证事件注册"""
    from src.registry import EventRegistry

    EventRegistry._handlers.clear()
    EventRegistry._configs.clear()

    EventRegistry.register(
        event=Events.COMET_APPEARED,
        handler_cls=MockHandler,
        template="skills/comet.png",
        region=(0, 0, 2560, 1440),
        similarity=0.8
    )

    assert Events.COMET_APPEARED in EventRegistry._handlers
    assert Events.COMET_APPEARED in EventRegistry._configs
    assert EventRegistry._handlers[Events.COMET_APPEARED] == MockHandler

def test_registry_get_handlers():
    """验证获取所有处理器"""
    from src.registry import EventRegistry

    EventRegistry._handlers.clear()
    EventRegistry._configs.clear()

    EventRegistry.register(Events.COMET_APPEARED, MockHandler, "a.png", (0,0,1,1), 0.8)
    EventRegistry.register(Events.DEFENSE_APPEARED, MockHandler, "b.png", (0,0,1,1), 0.8)

    handlers = EventRegistry.get_handlers()
    assert len(handlers) == 2
    assert Events.COMET_APPEARED in handlers
    assert Events.DEFENSE_APPEARED in handlers

def test_registry_get_configs():
    """验证获取所有配置"""
    from src.registry import EventRegistry

    EventRegistry._handlers.clear()
    EventRegistry._configs.clear()

    EventRegistry.register(Events.COMET_APPEARED, MockHandler, "a.png", (0,0,1,1), 0.8)

    configs = EventRegistry.get_configs()
    assert Events.COMET_APPEARED in configs
    assert isinstance(configs[Events.COMET_APPEARED], EventConfig)