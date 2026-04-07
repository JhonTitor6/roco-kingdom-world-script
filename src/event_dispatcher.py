from typing import Dict
from loguru import logger

from src.context import GameContext
from src.controller import GameController
from src.detector import EventDetector
from src.elf_manager import ElfManager
from src.events import Events
from src.handlers.base_handler import Handler


class EventDispatcher:
    """事件分发器（主循环）

    协调 EventDetector、Handler 和 GameContext。
    """

    def __init__(
        self,
        controller,
        elf_manager,
        skill_executor,
        config: dict
    ):
        self.controller: GameController = controller
        self.elf_manager: ElfManager = elf_manager
        self.skill_executor = skill_executor
        self.context = GameContext(dispatcher=self)
        self.detector = EventDetector(controller, config)
        self.handlers: Dict[Events, Handler] = {}
        self.running = False
        logger.info("EventDispatcher 初始化完成")

    def register_handler(self, event: Events, handler: Handler) -> None:
        """注册事件处理器

        Args:
            event: 事件
            handler: 处理器实例
        """
        self.handlers[event] = handler
        logger.debug(f"注册处理器: {event.value} -> {handler.__class__.__name__}")

    def run(self) -> None:
        """运行主循环

        持续检测事件并处理，直到 stop() 被调用。
        """
        logger.info("EventDispatcher 主循环开始")
        self.running = True
        while self.running:
            # 每轮只截一次图，所有事件检测复用同一张截图
            self.controller.capture()
            detected = self.detector.scan_all()
            for detected_event in detected:
                handler = self.handlers.get(detected_event.event)
                if handler:
                    logger.debug(f"触发事件: {detected_event.event.value} @ {detected_event.position} -> {handler.__class__.__name__}")
                    handler.handle(self.context, detected_event.position)
        logger.info("EventDispatcher 主循环结束")

    def stop(self) -> None:
        """停止主循环"""
        logger.info("收到停止信号")
        self.running = False
