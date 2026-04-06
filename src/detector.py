from dataclasses import dataclass
from typing import Union, List, Dict, Optional, Tuple
from src.events import Events
from src.event_config import EventConfig


@dataclass
class DetectedEvent:
    """检测到的事件"""
    event: Events
    position: Tuple[int, int]  # 匹配到的坐标


class EventDetector:
    """图像检测引擎

    负责扫描所有事件配置，检测图像是否出现。
    """

    def __init__(self, controller, config: Dict[Events, EventConfig]):
        """初始化检测器

        Args:
            controller: GameController 实例（需包含 elf_manager 属性）
            config: 事件配置字典
        """
        self.ctrl = controller
        self.elf_manager = controller.elf_manager  # 从 controller 获取 elf_manager
        self.event_configs = config

    def scan_all(self) -> List[DetectedEvent]:
        """全量检测所有事件

        Returns:
            检测到的事件列表（包含坐标）
        """
        detected = []
        for event, cfg in self.event_configs.items():
            pos = self._match_image(event, cfg)
            if pos is not None and pos != (-1, -1):
                detected.append(DetectedEvent(event=event, position=pos))
        return detected

    def _match_image(self, event: Events, cfg: EventConfig) -> Optional[Tuple[int, int]]:
        """检测指定事件对应的图像是否出现

        Args:
            event: 事件
            cfg: 事件配置

        Returns:
            匹配坐标或 None
        """
        template = self._get_template_for_event(event, cfg)
        if not template:
            return None

        return self.ctrl.find_image(
            template=template,
            similarity=cfg.similarity,
            x0=cfg.region[0],
            y0=cfg.region[1],
            x1=cfg.region[2],
            y1=cfg.region[3],
            _capture=False  # 使用已缓存的截图
        )

    def _get_template_for_event(
        self, event: Events, cfg: EventConfig
    ) -> Union[str, List[str], None]:
        """获取事件的模板

        动态模板从 elf_manager 获取。

        Args:
            event: 事件
            cfg: 事件配置

        Returns:
            模板路径或 None
        """
        # 空列表表示动态模板（如 ENEMY_SELF_DESTRUCT）
        if isinstance(cfg.template, list) and len(cfg.template) == 0:
            if event == Events.ENEMY_SELF_DESTRUCT:
                return self.elf_manager.get_selfdestruct_templates()
            # ENEMY_AVATAR 使用空模板，handler 也是 pass，不需要检测
            return None
        return cfg.template
