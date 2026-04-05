"""战斗流程"""
import time
from loguru import logger

from src.controller import GameController
from src.elf_manager import ElfManager, ElfRole
from src.skill_executor import SkillExecutor
from src.exceptions import ImageNotFoundError, BattleTimeoutError


class BattleFlow:
    """战斗流程控制"""

    # 敌方精灵状态区域（右上）
    ENEMY_REGION = (2000, 0, 2560, 320)

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
        time.sleep(1)
        insufficient_pos = self.ctrl.find_image_with_timeout("popup/insufficient.png", timeout=3, similarity=0.8)
        if insufficient_pos is not None:
            logger.info("检测到精灵数不足弹窗，点击确认按钮")
            self.ctrl.find_and_click_with_timeout("popup/confirm.png", timeout=3)
        # 等待匹配
        time.sleep(5)

        # 3. 选择首发精灵（final 精灵）- select_first_elf 已内置 timeout
        if not self.skill.select_first_elf(self.elf_mgr.final_elf):
            logger.error("选择首发精灵失败")
            return False

        time.sleep(1)

        # 4. 确认首发 - confirm_selection 已内置 timeout
        if not self.skill.confirm_selection():
            logger.error("确认首发失败")
            return False

        time.sleep(10)

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
        """检测速度优势（通过检测谁先出现inactive dot）

        我方区域：左上 (x<700, y<320)
        敌方区域：右上 (x>2000, y<320)

        Returns:
            True=我方先送死（速度优势），False=对方先送死（速度劣势）
        """
        # 区域坐标
        ally_region = (0, 0, 700, 320)   # 左上：我方
        enemy_region = self.ENEMY_REGION

        # 轮询检测谁先出现新的inactive dot
        for i in range(20):
            time.sleep(1)
            current_ally = self.count_inactive_in_region(ally_region)
            current_enemy = self.count_inactive_in_region(enemy_region)

            if current_ally == 1:
                logger.info(f"我方先送死，速度优势 (检测轮次: {i+1})")
                return True
            if current_enemy == 1:
                logger.info(f"对方先送死，速度劣势 (检测轮次: {i+1})")
                return False

        # 超时：默认我方先（保守判断）
        logger.info("速度检测超时，默认我方先")
        return True

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
        enemy_region = self.ENEMY_REGION

        for _ in range(30):
            time.sleep(1)
            inactive_count = self.count_inactive_in_region(enemy_region)

            if inactive_count == 3:
                logger.info(f"敌方已送死 {target} 只，当前剩余 {inactive_count}")
                return True

        logger.warning(f"等待对方送死超时（等待 {target} 只）")
        return False

    def count_inactive_in_region(self, region) -> int:
        """统计指定区域的inactive dots数量"""
        x0, y0, x1, y1 = region
        dots = self.ctrl.find_images_all(
            "dots/dot_inactive.png",
            similarity=0.8,
            x0=x0, y0=y0, x1=x1, y1=y1
        )
        return len(dots)

    def is_skill_releasable(self) -> bool:
        """检测是否有可释放技能（聚能图标出现）"""
        pos = self.ctrl.find_image("skills/energy.png", similarity=0.8)
        return pos != (-1, -1)

    def faster_flow(self) -> None:
        """我方速度快的流程"""
        logger.info("=== 速度优势流程 ===")
        time.sleep(3)

        # 1. sacrifice 精灵送死
        for elf in self.elf_mgr.sacrifice_elves:
            self.skill.switch_to_elf(elf)
            logger.info(f"送死: {elf['name']}")
            self.skill.cast_skill("comet")

        # 2. 切换到 reserve
        logger.info("切换到 reserve 精灵")
        self.skill.switch_to_elf(self.elf_mgr.reserve_elf)

        # 3. reserve 执行最终动作（循环直到战斗结束）
        logger.info("Reserve 精灵防御/聚能循环")
        while True:
            # 检测是否有可释放技能（聚能图标）
            if self.is_skill_releasable():
                # 尝试释放防御，如果失败（冷却中）则聚能
                if not self.skill.cast_skill("defense", timeout=1):
                    self.skill.press_energy()
                time.sleep(5)

            # 检测战斗是否结束
            if self.ctrl.find_image("battle/battle_end.png", similarity=0.8) != (-1, -1):
                logger.info("战斗结束")
                break

            time.sleep(1)

    def slower_flow(self) -> None:
        """我方速度慢的流程"""
        logger.info("=== 速度劣势流程 ===")

        enemy_region = self.ENEMY_REGION

        # 1. final 防御/聚能循环，直到敌方出现3个inactive
        logger.info("Final 精灵防御/聚能循环")
        while True:
            if self.is_skill_releasable():
                if not self.skill.cast_skill("defense", timeout=1):
                    self.skill.press_energy()
                    time.sleep(5)
            else:
                time.sleep(0.3)

            # 检测敌方 inactive 数量
            inactive_count = self.count_inactive_in_region(enemy_region)
            if inactive_count >= 3:
                logger.info(f"敌方已送死达到 {inactive_count} 只，退出循环")
                break

            time.sleep(0.5)

        time.sleep(5)
        # 2. 切换到 reserve
        logger.info("切换到 reserve 精灵")
        self.skill.switch_to_elf(self.elf_mgr.reserve_elf)

        # 3. reserve 送死
        self.skill.cast_skill("comet")

        # 4. sacrifice 精灵送死
        for elf in self.elf_mgr.sacrifice_elves:
            self.skill.switch_to_elf(elf)
            logger.info(f"送死: {elf['name']}")
            self.skill.cast_skill("comet", timeout=60)

        # 5. final 送死
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
        self.ctrl.click_at(*battle_end)

        # 点击再次切磋，等待下一画面出现
        if self.ctrl.find_and_click_with_timeout("battle/retry.png", timeout=3):
            time.sleep(10)
            self.ctrl.find_and_click_with_timeout("battle/quit.png", timeout=2)
            return True

        return False
