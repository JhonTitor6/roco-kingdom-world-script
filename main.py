"""程序入口"""
import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.logger import setup_logger
from src.window import find_window
from src.controller import GameController
from src.elf_manager import ElfManager
from src.skill_executor import SkillExecutor
from src.battle_flow import BattleFlow
from src.state_machine import BattleStateMachine
from src.exceptions import GameWindowNotFoundError
import json


def load_settings() -> dict:
    settings_path = Path(__file__).parent / "config" / "settings.json"
    with open(settings_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_elves_config() -> dict:
    elves_path = Path(__file__).parent / "config" / "elves.json"
    with open(elves_path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    settings = load_settings()
    logger = setup_logger(settings["log_level"])

    logger.info("=" * 50)
    logger.info("洛克王国闪耀大赛自动化脚本启动")
    logger.info("=" * 50)

    # 查找游戏窗口
    try:
        hwnd = find_window(
            class_name=settings["window"]["class_name"],
            title=settings["window"]["title"]
        )
    except GameWindowNotFoundError as e:
        logger.error(str(e))
        return

    # 初始化组件
    controller = GameController(hwnd=hwnd, settings=settings)
    elf_manager = ElfManager(config=load_elves_config(), controller=controller)
    skill_executor = SkillExecutor(controller=controller)
    battle_flow = BattleFlow(
        controller=controller,
        elf_manager=elf_manager,
        skill_executor=skill_executor,
        settings=settings
    )
    state_machine = BattleStateMachine(battle_flow=battle_flow)

    # 运行主循环
    logger.info(f"开始执行 {settings['loop_count']} 轮战斗")
    try:
        state_machine.run(loop_count=settings["loop_count"])
    except KeyboardInterrupt:
        logger.info("用户中断，程序退出")
    except GameWindowNotFoundError:
        logger.error("游戏窗口已关闭，程序退出")
    finally:
        logger.info("脚本已停止")


if __name__ == "__main__":
    main()