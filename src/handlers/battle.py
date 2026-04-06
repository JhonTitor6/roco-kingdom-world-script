"""战斗处理器"""
from enum import Enum

from src.handlers.base_handler import Handler
from src.state_machine import BattleState
from src.utils import random_sleep
from loguru import logger


class FlowType(Enum):
    """流程类型"""
    FASTER = "faster"
    SLOWER = "slower"


# 区域定义
ALLY_REGION = (0, 0, 700, 320)   # 我方区域（左上）
ENEMY_REGION = (2000, 0, 2560, 320)  # 敌方区域（右上）


class BattleHandler(Handler):
    """BATTLE_START / SPEED_CHECK / SACRIFICE_PHASE / FINAL_PHASE 处理器"""

    def handle(self) -> bool:
        """根据当前状态分发处理"""
        state = self.dispatcher.state

        if state == BattleState.BATTLE_START:
            return self._handle_battle_start()
        elif state == BattleState.SPEED_CHECK:
            return self._handle_speed_check()
        elif state == BattleState.SACRIFICE_PHASE:
            return self._handle_sacrifice_phase()
        elif state == BattleState.FINAL_PHASE:
            return self._handle_final_phase()

        return True

    def _handle_battle_start(self) -> bool:
        """等待战斗开始（comet.png 出现）"""
        if self.ctrl.find_image_with_timeout(
            "skills/comet.png",
            timeout=self.ctrl.settings["timeouts"]["battle_start"],
            similarity=0.8
        ) is None:
            logger.error("等待战斗开始超时")
            return False

        logger.info("战斗已开始")
        self.transition(BattleState.SPEED_CHECK)
        return True

    def _handle_speed_check(self) -> bool:
        """检测速度优势"""
        # 释放彗星技能
        self.skill.cast_skill("comet")

        # 检测速度优势
        faster = self._detect_speed_advantage()

        # 设置流程类型到 dispatcher
        self.dispatcher._set_flow_type("faster" if faster else "slower")
        logger.info(f"速度检测结果: {'faster' if faster else 'slower'}")

        self.transition(BattleState.SACRIFICE_PHASE)
        return True

    def _detect_speed_advantage(self) -> bool:
        """检测速度优势（通过检测谁先出现 inactive dot）"""
        for i in range(20):
            random_sleep(1)
            ally_count = self._count_inactive(ALLY_REGION)
            enemy_count = self._count_inactive(ENEMY_REGION)

            if ally_count >= 1:
                logger.info(f"我方先送死，速度优势 (检测轮次: {i+1})")
                return True
            if enemy_count >= 1:
                logger.info(f"对方先送死，速度劣势 (检测轮次: {i+1})")
                return False

        logger.info("速度检测超时，默认我方先")
        return True

    def _count_inactive(self, region) -> int:
        """统计指定区域的 inactive dots 数量"""
        x0, y0, x1, y1 = region
        dots = self.ctrl.find_images_all(
            "dots/dot_inactive.png",
            similarity=0.8,
            x0=x0, y0=y0, x1=x1, y1=y1
        )
        return len(dots)

    def _handle_sacrifice_phase(self) -> bool:
        """送死阶段处理"""
        flow_type = self.dispatcher.flow_type
        if flow_type == FlowType.FASTER:
            return self._faster_loop()
        else:
            return self._slower_loop()

    def _faster_loop(self) -> bool:
        """faster 流程: 我方先手"""
        logger.info("=== faster 流程 ===")

        # 1. sacrifice 精灵送死
        for elf in self.elf_mgr.sacrifice_elves:
            if not self.skill.switch_to_elf(elf, switch_panel_timeout=30):
                return False
            logger.info(f"送死: {elf['name']}")
            if not self.skill.cast_skill("comet"):
                return False

        # 2. 轮询等待我方 dot_inactive = 3
        while self._count_inactive(ALLY_REGION) < 3:
            random_sleep(1)

        # 3. 切换 reserve
        logger.info("切换到 reserve 精灵")
        if not self.skill.switch_to_elf(self.elf_mgr.reserve_elf, switch_panel_timeout=30):
            return False

        # 4. 进入 FINAL_PHASE
        self.transition(BattleState.FINAL_PHASE)
        return True

    def _slower_loop(self) -> bool:
        """slower 流程: 对方先手

        注意: slower 流程中 final 精灵在场执行防御/聚能，
        同时轮询等待敌方 dot_inactive = 3（敌方送死时我方不需等待自己的 dot 变化）
        """
        logger.info("=== slower 流程 ===")

        # 1. final 防御循环，直到敌方 dot_inactive = 3
        logger.info("Final 精灵防御/聚能循环")
        while self._count_inactive(ENEMY_REGION) < 3:
            if self._is_skill_releasable():
                if not self.skill.cast_skill("defense", timeout=1):
                    self.skill.press_energy()
            random_sleep(1)

        # 2. 切换 reserve
        logger.info("切换到 reserve 精灵")
        if not self.skill.switch_to_elf(self.elf_mgr.reserve_elf, switch_panel_timeout=30):
            return False

        # 3. reserve 送死
        if not self.skill.cast_skill("comet", elf=self.elf_mgr.reserve_elf):
            return False

        # 4. sacrifice 精灵送死
        for elf in self.elf_mgr.sacrifice_elves:
            if not self.skill.switch_to_elf(elf, switch_panel_timeout=30):
                return False
            logger.info(f"送死: {elf['name']}")
            if not self.skill.cast_skill("comet", timeout=60):
                return False

        # 5. 切换 final 并送死
        if not self.skill.switch_to_elf(self.elf_mgr.final_elf, switch_panel_timeout=30):
            return False
        logger.info("Final 精灵送死")
        if not self.skill.cast_skill("comet"):
            return False

        # 6. 进入 FINAL_PHASE
        self.transition(BattleState.FINAL_PHASE)
        return True

    def _is_skill_releasable(self) -> bool:
        """检测是否有可释放技能（聚能图标出现）"""
        pos = self.ctrl.find_image("skills/energy.png", similarity=0.8)
        return pos != (-1, -1)

    def _handle_final_phase(self) -> bool:
        """FINAL_PHASE 处理: reserve 精灵已送死，final 精灵在场，循环防御/聚能"""
        logger.info("=== FINAL_PHASE ===")

        while True:
            # 检测战斗结束
            if self.ctrl.find_image("battle/battle_end.png", similarity=0.8) != (-1, -1):
                logger.info("战斗结束")
                self.transition(BattleState.BATTLE_END)
                return True

            # 可释放技能则释放
            if self._is_skill_releasable():
                if not self.skill.cast_skill("defense", timeout=1):
                    self.skill.press_energy()

            random_sleep(1)