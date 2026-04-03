"""技能执行器"""
import time
from loguru import logger

from src.controller import GameController


class SkillExecutor:
    """执行技能和精灵切换"""

    def __init__(self, controller: GameController):
        self.ctrl = controller

    def cast_skill(self, skill_name: str) -> bool:
        """释放技能（通过识图点击技能栏）

        Args:
            skill_name: 技能名 (comet / defense)

        Returns:
            是否成功
        """
        template_map = {
            "comet": "skills/comet.png",
            "defense": "skills/defense.png",
        }
        template = template_map.get(skill_name)
        if not template:
            logger.error(f"未知技能: {skill_name}")
            return False

        pos = self.ctrl.find_image(template, similarity=0.8)
        if pos == (-1, -1):
            logger.warning(f"技能图标未找到: {skill_name}")
            return False

        self.ctrl.click_at(*pos)
        logger.info(f"释放技能: {skill_name}")
        return True

    def press_energy(self) -> None:
        """聚能（按 X 键）"""
        self.ctrl.press_key('X')
        logger.info("聚能 (X)")

    def press_defense(self) -> None:
        """防御（按 4 键，识图点击）"""
        self.cast_skill("defense")

    def switch_to_elf(self, elf) -> bool:
        """切换到指定精灵

        Args:
            elf: 精灵配置 dict

        Returns:
            是否成功
        """
        # 按 E 打开切换面板，等待面板出现
        self.ctrl.press_key('E')
        if not self.wait_for_switch_panel(timeout=3):
            logger.warning("切换面板未出现")
            return False

        # 识图查找目标精灵
        pos = self.ctrl.find_image_with_timeout(elf["template"], timeout=3, similarity=0.8)
        if pos is None:
            logger.warning(f"切换精灵失败: {elf['name']}")
            self.ctrl.press_key('E')  # 关闭面板
            return False

        self.ctrl.click_at(*pos)
        logger.info(f"切换精灵: {elf['name']}")
        return True

    def select_first_elf(self, elf) -> bool:
        """在选择首发精灵界面选择精灵

        Args:
            elf: 精灵配置 dict

        Returns:
            是否成功
        """
        pos = self.ctrl.find_image_with_timeout(elf["template"], timeout=5, similarity=0.8)
        if pos is None:
            logger.warning(f"选择首发精灵失败: {elf['name']}")
            return False

        self.ctrl.click_at(*pos)
        logger.info(f"选择首发精灵: {elf['name']}")
        return True

    def confirm_selection(self) -> bool:
        """确认选择"""
        return self.ctrl.find_and_click_with_timeout("popup/confirm.png", timeout=5)

    def wait_for_switch_panel(self, timeout: float = 3) -> bool:
        """等待切换面板出现"""
        pos = self.ctrl.find_image_with_timeout("popup/switch_panel.png", timeout=timeout)
        return pos is not None
