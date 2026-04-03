"""战斗流程"""
import time
from loguru import logger

from src.controller import GameController
from src.elf_manager import ElfManager, ElfRole
from src.skill_executor import SkillExecutor
from src.exceptions import ImageNotFoundError, BattleTimeoutError


class BattleFlow:
    """战斗流程控制"""

    def __init__(
        self,
        controller: GameController,
        elf_manager: ElfManager,
        skill_executor: SkillExecutor,
        settings: dict
    ):
        self.ctrl = controller
        self.elf_mgr = elf_manager
        self.skill = skill_executor
        self.settings = settings

    def run_entry_flow(self) -> bool:
        """进入战斗的流程

        Returns:
            是否成功进入战斗
        """
        timeouts = self.settings["timeouts"]

        # 1. 点击开始挑战，等待下一画面出现
        if not self.ctrl.find_and_click_with_timeout("battle/start_challenge.png", timeout=5):
            logger.warning("未找到「开始挑战」按钮")
            return False

        # 2. 检查精灵数不足弹窗
        insufficient_pos = self.ctrl.find_image_with_timeout("popup/insufficient.png", timeout=3, similarity=0.8)
        if insufficient_pos is not None:
            logger.info("检测到精灵数不足弹窗，点击确认按钮")
            self.ctrl.find_and_click_with_timeout("popup/confirm.png", timeout=3)
            time.sleep(0.3)

        # 3. 选择首发精灵（final 精灵）- select_first_elf 已内置 timeout
        if not self.skill.select_first_elf(self.elf_mgr.final_elf):
            logger.error("选择首发精灵失败")
            return False

        # 4. 确认首发 - confirm_selection 已内置 timeout
        if not self.skill.confirm_selection():
            logger.error("确认首发失败")
            return False

        # 5. 等待战斗开始
        battle_start = self.ctrl.find_image_with_timeout(
            "skills/comet.png",
            timeout=timeouts["battle_start"],
            similarity=0.8
        )
        if battle_start is None:
            logger.error("等待战斗开始超时")
            return False

        logger.info("战斗已开始")
        return True

    def detect_speed_advantage(self) -> bool:
        """检测速度优势（通过判断我方是否先送死）

        Returns:
            True=我方速度快，False=对方速度快
        """
        # 等待一轮行动，看我方精灵是否先减少
        initial_count = self.elf_mgr.count_alive_elves()
        logger.debug(f"初始精灵数: {initial_count}")

        # 等待约 2 秒检测变化
        for _ in range(10):
            time.sleep(0.3)
            current_count = self.elf_mgr.count_alive_elves()
            if current_count < initial_count:
                logger.info(f"我方先送死，速度优势")
                return True

        logger.info(f"对方先送死，速度劣势")
        return False

    def wait_for_enemy_sacrifice(self, target: int = 3) -> bool:
        """等待对方送死指定数量

        Args:
            target: 目标送死数量

        Returns:
            是否等到

        Note:
            敌方小圆点区域在屏幕右上区域（相对于游戏窗口），
            具体坐标需要根据实际截图确定。当前使用固定区域搜索。
            闪耀大赛固定 4v4，敌方初始4只。
        """
        initial_enemy_count = 4  # 闪耀大赛固定 4v4

        for _ in range(30):  # 最多等 30 * 0.5 = 15 秒
            time.sleep(0.5)

            # 识图查找敌方小圆点（右上区域）
            # TODO: 替换为实际测量的区域坐标
            # enemy_dots = self.ctrl.find_images_all(
            #     "dots/dot_active.png",
            #     x0=窗口宽度//2, y0=0, x1=窗口宽度, y1=窗口高度//2,
            #     similarity=0.8
            # )
            # enemy_count = len(enemy_dots)
            #
            # if enemy_count <= initial_enemy_count - target:
            #     logger.info(f"敌方已送死 {target} 只，当前剩余 {enemy_count}")
            #     return True

            pass  # TODO: 根据实际截图确定区域后实现

        logger.warning(f"等待对方送死超时（等待 {target} 只）")
        return False

    def sacrifice_sequence(self, order: list) -> None:
        """执行送死序列

        Args:
            order: 送死顺序的精灵列表
        """
        for i, elf in enumerate(order):
            logger.info(f"送死 #{i+1}: {elf['name']}")
            # 释放彗星
            if not self.skill.cast_skill("comet"):
                logger.warning(f"释放彗星失败: {elf['name']}")
            time.sleep(1)

            # 如果是最后一只，执行最终动作
            if i == len(order) - 1:
                action = self.elf_mgr.get_final_action()
                if action == "energy":
                    self.skill.press_energy()
                else:
                    self.skill.cast_skill("defense")

    def faster_flow(self) -> None:
        """我方速度快的流程"""
        logger.info("=== 速度优势流程 ===")

        # 1. final 先送死
        logger.info("Final 精灵送死")
        self.skill.cast_skill("comet")
        time.sleep(1)

        # 2. sacrifice 精灵送死
        for elf in self.elf_mgr.sacrifice_elves:
            logger.info(f"送死: {elf['name']}")
            self.skill.cast_skill("comet")
            time.sleep(1)

        # 3. 等待对方送死 3 只
        logger.info("等待对方送死 3 只...")
        self.wait_for_enemy_sacrifice(3)

        # 4. 切换到 reserve
        logger.info("切换到 reserve 精灵")
        self.skill.switch_to_elf(self.elf_mgr.reserve_elf)

        # 5. reserve 执行最终动作
        action = self.elf_mgr.get_final_action()
        if action == "energy":
            self.skill.press_energy()
        else:
            self.skill.cast_skill("defense")

    def slower_flow(self) -> None:
        """我方速度慢的流程"""
        logger.info("=== 速度劣势流程 ===")

        # 1. final 防御/聚能
        logger.info("Final 精灵防御/聚能")
        action = self.elf_mgr.get_final_action()
        if action == "energy":
            self.skill.press_energy()
        else:
            self.skill.cast_skill("defense")

        # 2. 等待对方送死 3 只
        logger.info("等待对方送死 3 只...")
        self.wait_for_enemy_sacrifice(3)

        # 3. 切换到 reserve
        logger.info("切换到 reserve 精灵")
        self.skill.switch_to_elf(self.elf_mgr.reserve_elf)

        # 4. reserve 送死
        self.skill.cast_skill("comet")
        time.sleep(1)

        # 5. sacrifice 精灵送死
        for elf in self.elf_mgr.sacrifice_elves:
            logger.info(f"送死: {elf['name']}")
            self.skill.cast_skill("comet")
            time.sleep(1)

        # 6. final 送死
        logger.info("Final 精灵送死")
        self.skill.cast_skill("comet")

    def handle_battle_end(self) -> bool:
        """处理战斗结束

        Returns:
            是否应该继续下一轮
        """
        # 检测战斗结束图标
        battle_end = self.ctrl.find_image_with_timeout(
            "battle/battle_end.png",
            timeout=self.settings["timeouts"]["battle_end"],
            similarity=0.8
        )
        if battle_end is None:
            logger.warning("未检测到战斗结束标志")
            return False

        logger.info("战斗结束")

        # 点击再次切磋，等待下一画面出现
        if self.ctrl.find_and_click_with_timeout("battle/retry.png", timeout=3):
            time.sleep(0.5)
            # 检测对方不想切磋
            quit_pos = self.ctrl.find_image_with_timeout("battle/quit.png", timeout=2, similarity=0.8)
            if quit_pos is not None:
                logger.info("对方不想切磋，点击退出")
                self.ctrl.find_and_click_with_timeout("battle/quit.png", timeout=2)
                time.sleep(0.5)
            return True

        return False
