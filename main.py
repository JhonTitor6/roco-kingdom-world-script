"""程序入口"""
import json

from src.logger import setup_logger
from src.window import find_window
from src.controller import GameController
from src.elf_manager import ElfManager
from src.skill_executor import SkillExecutor
from src.event_dispatcher import EventDispatcher
from src.registry import EventRegistry
from src.exceptions import GameWindowNotFoundError
from loguru import logger


def main():
    # 0. 配置日志
    setup_logger()

    # 1. 初始化组件
    try:
        hwnd = find_window(title="洛克王国：世界")
    except GameWindowNotFoundError as e:
        logger.error(str(e))
        return

    with open("config/settings.json", "r", encoding="utf-8") as f:
        settings = json.load(f)
    with open("config/elves.json", "r", encoding="utf-8") as f:
        elf_config = json.load(f)

    controller = GameController(hwnd, settings)
    elf_manager = ElfManager(elf_config, controller)
    skill_executor = SkillExecutor(controller)

    # 将 elf_manager 附加到 controller（EventDetector 期望从 controller 获取）
    controller.elf_manager = elf_manager

    # 2. 导入所有处理器（触发 self-register）
    from src.handlers import (  # noqa: F401
        CometAppearedHandler,
        DefenseAppearedHandler,
        BattleEndHandler,
        StartChallengeHandler,
        ConfirmHandler,
        RetryHandler,
        SwitchElfHandler,
        DotsChangedHandler,
        EnemySelfDestructHandler,
    )
    from src.handlers.enemy_avatar import EnemyAvatarHandler  # noqa: F401

    # 3. 创建事件分发器
    configs = EventRegistry.get_configs()
    dispatcher = EventDispatcher(controller, elf_manager, skill_executor, configs)

    # 4. 注册处理器实例
    for event, handler_cls in EventRegistry.get_handlers().items():
        dispatcher.register_handler(event, handler_cls(dispatcher))

    # 5. 运行主循环
    try:
        dispatcher.run()
    except KeyboardInterrupt:
        logger.info("用户中断，程序退出")
    except GameWindowNotFoundError:
        logger.error("游戏窗口已关闭，程序退出")
    finally:
        logger.info("脚本已停止")

    logger.info("脚本执行完成")


if __name__ == "__main__":
    main()
