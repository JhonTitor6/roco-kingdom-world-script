"""精灵管理器"""
from typing import List, Optional
from loguru import logger

from src.controller import GameController


class Elf:
    """精灵数据类"""
    name: str
    template: str
    role: str
    switch_sleep: Optional[int]
    _all_templates: List[str]

    def __init__(self, name: str, template: str | List[str], role: str, switch_sleep: Optional[int] = None):
        self.name = name
        self._all_templates = [template] if isinstance(template, str) else template
        self.template = self._all_templates[0]
        self.role = role
        self.switch_sleep = switch_sleep

    @property
    def templates(self) -> List[str]:
        """获取所有模板路径列表"""
        return self._all_templates


class ElfRole:
    """精灵角色常量"""
    SACRIFICE = "sacrifice"  # 送死精灵
    FINAL = "final"         # 最后送死
    RESERVE = "reserve"     # 备用


class ElfManager:
    """管理精灵配置和状态"""

    def __init__(self, config: dict, controller: GameController):
        self.config = config
        self.controller = controller
        self.elves: List[Elf] = [Elf(**e) for e in config["elves"]]

        # 按角色分类
        self._final_elf = self._get_elf_by_role(ElfRole.FINAL)
        self._reserve_elf = self._get_elf_by_role(ElfRole.RESERVE)
        self._sacrifice_elves = self._get_elves_by_role(ElfRole.SACRIFICE)

    def _get_elf_by_role(self, role: str) -> Optional[Elf]:
        """获取指定角色的第一个精灵"""
        for elf in self.elves:
            if elf.role == role:
                return elf
        return None

    def _get_elves_by_role(self, role: str) -> List[Elf]:
        """获取指定角色的所有精灵"""
        return [elf for elf in self.elves if elf.role == role]

    @property
    def final_elf(self) -> Elf:
        """获取 final 精灵"""
        if not self._final_elf:
            raise ValueError("配置中未找到 final 精灵")
        return self._final_elf

    @property
    def reserve_elf(self) -> Elf:
        """获取 reserve 精灵"""
        if not self._reserve_elf:
            raise ValueError("配置中未找到 reserve 精灵")
        return self._reserve_elf

    @property
    def sacrifice_elves(self) -> List[Elf]:
        """获取 sacrifice 精灵列表"""
        return self._sacrifice_elves

    def count_alive_elves(self) -> int:
        """统计我方存活精灵数（通过识别小圆点）"""
        # 识图查找亮着的小圆点数量
        # 小圆点排列区域需要通过截图确定具体位置
        # 这里先用固定区域，运行时可能需要调整
        active_dots = self.controller.find_images_all(
            "dots/dot_active.png",
            similarity=0.8
        )
        count = len(active_dots)
        logger.debug(f"检测到存活精灵数: {count}")
        return count

    def find_elf_position(self, elf: Elf) -> Optional[tuple]:
        """在切换精灵面板中查找精灵位置

        Args:
            elf: 精灵对象

        Returns:
            (x, y) 或 None
        """
        for template in elf.templates:
            pos = self.controller.find_image(template, similarity=0.8)
            if pos != (-1, -1):
                logger.debug(f"找到精灵: {elf.name} ({template}) @ {pos}")
                return pos

        logger.warning(f"未找到精灵: {elf.name} (尝试了 {elf.templates})")
        return None

    def get_sacrifice_order(self, faster: bool) -> List[Elf]:
        """获取送死顺序

        Args:
            faster: True=我方速度快，False=对方速度快

        Returns:
            按送死顺序排列的精灵列表
        """
        if faster:
            # 我方先手: final -> sacrifice -> sacrifice -> reserve
            order: List[Elf] = [self.final_elf] + self.sacrifice_elves + [self.reserve_elf]
        else:
            # 对方先手: reserve -> sacrifice -> sacrifice -> final
            order = [self.reserve_elf] + self.sacrifice_elves + [self.final_elf]
        return order

    def get_selfdestruct_templates(self) -> List[str]:
        """获取自爆流敌方精灵的头像模板列表"""
        return self.config.get("selfdestruct_enemies", [])

    def get_sacrifice_elves(self) -> List[Elf]:
        """获取所有送死精灵列表

        Returns:
            送死精灵列表
        """
        return self._sacrifice_elves

    def get_reserve_template(self) -> str:
        """获取备用精灵的模板路径

        Returns:
            备用精灵的模板路径
        """
        if not self._reserve_elf:
            raise ValueError("配置中未找到 reserve 精灵")
        return self._reserve_elf.template
