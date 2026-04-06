"""程序入口"""
import json

from src.window import find_window
from src.controller import GameController
from src.elf_manager import ElfManager
from src.skill_executor import SkillExecutor
from src.event_dispatcher import EventDispatcher
from src.exceptions import GameWindowNotFoundError
from loguru import logger


def main():
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

    # 2. 创建事件分发器并运行
    dispatcher = EventDispatcher(controller, elf_manager, skill_executor, settings)
    try:
        dispatcher.run(loop_count=settings.get("loop_count", 10))
    except KeyboardInterrupt:
        logger.info("用户中断，程序退出")
    except GameWindowNotFoundError:
        logger.error("游戏窗口已关闭，程序退出")
    finally:
        logger.info("脚本已停止")

    logger.info("脚本执行完成")


if __name__ == "__main__":
    main()
