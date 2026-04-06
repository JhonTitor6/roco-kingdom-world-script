"""战斗处理器"""
from enum import Enum, auto

from src.handlers.base_handler import Handler
from src.state_machine import BattleState, SacrificeSubState
from src.utils import random_sleep
from loguru import logger


class FlowType(Enum):
    """流程类型"""
    FASTER = "faster"
    SLOWER = "slower"


class Action(Enum):
    """操作枚举"""
    WAIT = auto()                    # 等待，什么都不做
    SWITCH_AND_CAST = auto()         # 切换精灵 + 释放 comet
    SWITCH = auto()                  # 仅切换精灵
    CAST_DEFENSE = auto()            # 释放防御
    PRESS_ENERGY = auto()            # 聚能


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
        # 检测敌方是否为自爆流
        if not self._check_enemy_selfdestruct():
            return True  # 已触发退出（BATTLE_END 或 ERROR 状态）
        self.transition(BattleState.SPEED_CHECK)
        return True

    def _escape_battle(self) -> bool:
        """执行逃跑操作：点击 escape.png → confirm.png"""
        if not self.ctrl.find_and_click_with_timeout("skills/escape.png", timeout=5, similarity=0.8):
            return False
        random_sleep(0.5)
        if not self.ctrl.find_and_click_with_timeout("popup/yes.png", timeout=5, similarity=0.8):
            return False
        return True

    def _check_enemy_selfdestruct(self) -> bool:
        """检测敌方是否为自爆流，不是则退出战斗

        Returns:
            True: 敌方是自爆流，继续战斗流程
            False: 敌方不是自爆流，已触发退出（BATTLE_END 或 ERROR）
        """
        # 1. 获取 selfdestruct 角色的敌方头像模板列表
        selfdestruct_templates = self.elf_mgr.get_selfdestruct_templates()
        if not selfdestruct_templates:
            logger.warning("未配置自爆流敌方精灵，继续战斗")
            return True

        # 2. 在 enemy_region 区域查找敌方头像
        enemy_region = self.ctrl.settings.get("enemy_region", ENEMY_REGION)
        for template in selfdestruct_templates:
            pos = self.ctrl.find_image(
                template,
                similarity=self.ctrl.settings.get("similarity", 0.6),
                x0=enemy_region[0], y0=enemy_region[1],
                x1=enemy_region[2], y1=enemy_region[3]
            )
            if pos != (-1, -1):
                logger.info(f"检测到敌方自爆流精灵: {template}")
                return True

        # 3. 未匹配到自爆流，执行退出
        logger.info("敌方不是自爆流，执行退出")
        self.dispatcher._exit_directly = True  # 设置直接退出标记

        if not self._escape_battle():
            logger.error("逃跑失败，进入 ERROR 状态")
            self.transition(BattleState.ERROR)
            return False

        self.transition(BattleState.BATTLE_END)
        return False

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

    def _faster_decide(self, ally_dots: int) -> tuple:
        """FASTER 流程决策表

        Returns:
            (action: Action, elf: dict or None)
        """
        if ally_dots < 3:
            elf = self.elf_mgr.sacrifice_elves[ally_dots]
            return (Action.SWITCH_AND_CAST, elf)
        elif ally_dots == 3:
            return (Action.SWITCH, self.elf_mgr.reserve_elf)
        return (Action.WAIT, None)

    def _is_switch_panel_open(self) -> bool:
        """检测精灵切换面板是否打开（头像在 x<600 区域）"""
        elf_templates = ["tree3", "otter2", "pig3", "scepter3"]
        for template in elf_templates:
            pos = self.ctrl.find_image(f"elves/{template}.png", similarity=0.8)
            if pos != (-1, -1) and pos[0] < 600:
                return True
        return False

    def _handle_faster_phase(self) -> bool:
        """FASTER 流程事件驱动处理

        每帧检测切换面板状态，根据 ally_dot_count 决策：
        - dot < 3: 切换对应 sacrifice 精灵，释放 comet
        - dot = 3: 切换 reserve 精灵，进入 FINAL_PHASE
        - dot 异常: 等待
        """
        ally_dots = self._count_inactive(ALLY_REGION)

        # 检测切换面板是否打开
        if not self._is_switch_panel_open():
            # 面板未打开，等待（继续循环）
            return True

        # 面板已打开，根据 dot 数量决策
        action, elf = self._faster_decide(ally_dots)

        if action == Action.WAIT:
            return True

        if action == Action.SWITCH_AND_CAST:
            if not self.skill.switch_to_elf(elf, switch_panel_timeout=30):
                return False
            logger.info(f"送死: {elf['name']}")
            if not self.skill.cast_skill("comet"):
                return False

        if action == Action.SWITCH:
            if not self.skill.switch_to_elf(elf, switch_panel_timeout=30):
                return False
            logger.info("切换到 reserve 精灵")
            self.transition(BattleState.FINAL_PHASE)

        return True

    def _handle_slower_phase(self) -> bool:
        """SLOWER 流程事件驱动处理

        子状态机管理：
        - SLOWER_DEFENSE: 防御期，等待 enemy_dots >= 3
        - SLOWER_SAC: 送死序列（step 0-2 sacrifice, step 3 final）
        - SLOWER_RESERVE: 切换 reserve
        - SLOWER_FINAL: final 送死
        """
        sub_state = self.dispatcher._slower_sub_state

        if sub_state == SacrificeSubState.SLOWER_DEFENSE:
            return self._slower_defense()
        elif sub_state == SacrificeSubState.SLOWER_SAC:
            return self._slower_sac()
        elif sub_state == SacrificeSubState.SLOWER_RESERVE:
            return self._slower_reserve()
        elif sub_state == SacrificeSubState.SLOWER_FINAL:
            return self._slower_final()
        return True

    def _slower_defense(self) -> bool:
        """SLOWER 防御期：轮询等待 enemy_dots >= 3"""
        enemy_dots = self._count_inactive(ENEMY_REGION)

        if enemy_dots >= 3:
            # 进入送死期
            self.dispatcher._slower_sub_state = SacrificeSubState.SLOWER_SAC
            self.dispatcher._slower_step = 0
            logger.info("SLOWER 流程进入送死期")
            return True

        # 可释放技能则释放
        if self._is_skill_releasable():
            if not self.skill.cast_skill("defense", timeout=1):
                self.skill.press_energy()
        return True

    def _slower_sac(self) -> bool:
        """SLOWER 送死序列：按顺序送死 sacrifice 和 final"""
        step = self.dispatcher._slower_step

        if step < len(self.elf_mgr.sacrifice_elves):
            # 送死 sacrifice 精灵
            elf = self.elf_mgr.sacrifice_elves[step]
            if not self.skill.switch_to_elf(elf, switch_panel_timeout=30):
                return False
            logger.info(f"送死: {elf['name']}")
            if not self.skill.cast_skill("comet", timeout=60):
                return False
            self.dispatcher._slower_step = step + 1
        elif step == len(self.elf_mgr.sacrifice_elves):
            # 切换 final，不用先检测switch_panel，直接点击切换按钮
            if not self.skill.switch_to_elf(self.elf_mgr.final_elf, switch_panel_timeout=1):
                return False
            logger.info("Final 精灵送死")
            if not self.skill.cast_skill("comet"):
                return False
            self.dispatcher._slower_sub_state = SacrificeSubState.SLOWER_RESERVE
        return True

    def _slower_reserve(self) -> bool:
        """SLOWER 切换 reserve"""
        if not self.skill.switch_to_elf(self.elf_mgr.reserve_elf, switch_panel_timeout=30):
            return False
        logger.info("切换到 reserve 精灵")
        if not self.skill.cast_skill("comet", elf=self.elf_mgr.reserve_elf):
            return False
        self.dispatcher._slower_sub_state = SacrificeSubState.SLOWER_FINAL
        return True

    def _slower_final(self) -> bool:
        """SLOWER final 送死后进入 FINAL_PHASE"""
        self.transition(BattleState.FINAL_PHASE)
        return True

    def _handle_sacrifice_phase(self) -> bool:
        """送死阶段处理（事件驱动）

        每帧根据 flow_type 和 dot 数量决策下一步操作，
        替代原有的 while 循环轮询。
        """
        flow_type = self.dispatcher.flow_type
        if flow_type == FlowType.FASTER:
            return self._handle_faster_phase()
        else:
            return self._handle_slower_phase()

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