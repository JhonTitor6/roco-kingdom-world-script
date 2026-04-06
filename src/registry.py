from typing import Union, List, Dict, Type
from src.events import Events
from src.event_config import EventConfig

class EventRegistry:
    """事件注册表

    负责管理事件与处理器、配置的映射关系。
    使用类方法进行全局注册。
    """
    _handlers: Dict[Events, Type["Handler"]] = {}
    _configs: Dict[Events, EventConfig] = {}

    @classmethod
    def register(
        cls,
        event: Events,
        handler_cls: Type["Handler"],
        template: Union[str, List[str]],
        region: tuple[int, int, int, int],
        similarity: float = 0.8
    ) -> None:
        """注册事件处理器和配置"""
        cls._handlers[event] = handler_cls
        cls._configs[event] = EventConfig(template, region, similarity)

    @classmethod
    def get_handlers(cls) -> Dict[Events, Type["Handler"]]:
        """获取所有已注册处理器"""
        return cls._handlers.copy()

    @classmethod
    def get_configs(cls) -> Dict[Events, EventConfig]:
        """获取所有已注册配置"""
        return cls._configs.copy()

    @classmethod
    def clear(cls) -> None:
        """清空注册表（用于测试）"""
        cls._handlers.clear()
        cls._configs.clear()
