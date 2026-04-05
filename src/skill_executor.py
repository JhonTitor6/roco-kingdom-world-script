"""技能执行器"""
import time
from loguru import logger

from src.controller import GameController


class SkillExecutor:
    """执行技能和精灵切换"""

    def __init__(self, controller: GameController):
        self.ctrl = controller

    def cast_skill(self, skill_name: str, timeout: float = 10, elf=None) -> bool:
        """释放技能（通过识图点击技能栏）

        Args:
            skill_name: 技能名 (comet / defense)
            timeout: 查找技能图标的超时时间（秒）
            elf: 精灵配置 dict（可选，用于特殊精灵如权杖的延迟处理）

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

        # 先这样，懒得优化了
        # 权杖（reserve）等特殊精灵：技能出现后需等待一段时间才能点击，且位置会变化
        is_reserve = elf is not None and elf.get("role") == "reserve"
        if is_reserve:
            # 等待技能稳定可点击
            time.sleep(3)
            # 重试几次，每次重新查找位置（技能会换位置）
            for attempt in range(3):
                pos = self.ctrl.find_image_with_timeout(template, timeout=3, similarity=0.7)
                if pos is not None:
                    time.sleep(1)
                    self.ctrl.click_at(*pos)
                    logger.info(f"释放技能: {skill_name} (权杖第{attempt + 1}次尝试)")
                    wait_time = self.ctrl.settings.get("skill_wait_after_cast", 10)
                    time.sleep(wait_time)
                    return True
                time.sleep(1)
            logger.warning(f"权杖技能图标未找到: {skill_name}")
            return False

        pos = self.ctrl.find_image_with_timeout(template, timeout=timeout, similarity=0.7)
        if pos is None:
            logger.warning(f"技能图标未找到: {skill_name}")
            return False
        time.sleep(1)
        self.ctrl.click_at(*pos)
        logger.info(f"释放技能: {skill_name}")

        # 技能释放后等待（可配置）
        wait_time = self.ctrl.settings.get("skill_wait_after_cast", 10)
        time.sleep(wait_time)
        return True

    def press_energy(self) -> None:
        """聚能（识图点击 energy.png）"""
        pos = self.ctrl.find_image_with_timeout("skills/energy.png", timeout=5, similarity=0.8)
        if pos is not None:
            self.ctrl.click_at(*pos)
            logger.info("聚能")
            time.sleep(8)
        else:
            logger.warning("聚能图像未找到")

    def press_defense(self) -> None:
        """防御（识图点击）"""
        self.cast_skill("defense")

    def switch_to_elf(self, elf, switch_panel_timeout=8) -> bool:
        """切换到指定精灵

        Args:
            elf: 精灵配置 dict

        Returns:
            是否成功
        """
        if not self.wait_for_switch_panel(timeout=switch_panel_timeout):
            logger.warning("切换面板未出现")
            # 等待可释放技能（聚能图像出现）
            if not self.wait_for_releasable_skill(timeout=30):
                logger.warning("等待可释放技能超时")
                return False
            time.sleep(2)
            logger.info("打开精灵切换面板")
            # 识图点击 switch.png 打开切换面板
            pos = self.ctrl.find_image_with_timeout("skills/switch.png", timeout=5, similarity=0.8)
            if pos is not None:
                self.ctrl.click_at(*pos)
                logger.info("打开切换面板")
            else:
                logger.warning("切换面板图标未找到")
            time.sleep(2)


        # 识图查找目标精灵（限制区域）
        pos = self.ctrl.find_image_with_timeout(
            elf["template"], timeout=3, similarity=0.8, x0=251, y0=320, x1=554, y1=1113
        )
        if pos is None:
            logger.warning(f"切换精灵失败: {elf['name']}")
            return False

        self.ctrl.click_at(*pos)
        time.sleep(0.5)
        self.ctrl.press_key("space")
        logger.info(f"切换精灵: {elf['name']}")
        switch_sleep = elf.get("switch_sleep", 5)
        time.sleep(switch_sleep)
        return True

    def wait_for_releasable_skill(self, timeout: float = 10) -> bool:
        """等待可释放技能（聚能图像出现）

        Args:
            timeout: 超时时间（秒）

        Returns:
            是否检测到聚能图像
        """
        template = "skills/energy.png"
        start = time.time()
        while time.time() - start < timeout:
            self.ctrl.capture()
            pos = self.ctrl.find_image(template, similarity=0.8)
            if pos != (-1, -1):
                logger.debug(f"检测到可释放技能: {template} @ {pos}")
                return True
            time.sleep(0.3)
        logger.warning(f"等待可释放技能超时: {template}")
        return False

    def select_first_elf(self, elf) -> bool:
        """在选择首发精灵界面选择精灵

        Args:
            elf: 精灵配置 dict

        Returns:
            是否成功
        """
        pos = self.ctrl.find_image_with_timeout(elf["template"], timeout=60, similarity=0.8)
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
        """等待切换面板出现 - 通过检测精灵头像是否在左侧区域

        切换面板打开后，精灵头像会出现在屏幕左侧（x < 600）
        通过检测任意已知精灵头像是否出现在该区域来判断面板是否打开
        """
        elf_templates = [
            "elves/tree3.png",
            "elves/otter2.png",
            "elves/pig3.png",
            "elves/scepter3.png",
        ]
        start = time.time()
        while time.time() - start < timeout:
            self.ctrl.capture()
            for elf_template in elf_templates:
                pos = self.ctrl.find_image(elf_template, similarity=0.8)
                if pos != (-1, -1) and pos[0] < 600:  # 左侧区域
                    logger.debug(f"检测到切换面板: {elf_template} @ {pos}")
                    return True
            time.sleep(0.2)
        return False
