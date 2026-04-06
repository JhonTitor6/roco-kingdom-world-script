"""精灵管理器"""
from typing import List, Dict, Optional
from loguru import logger

from src.controller import GameController
from src.exceptions import ElfNotFoundError


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
        self.elves: List[Dict] = config["elves"]

        # 按角色分类
        self._final_elf = self._get_elf_by_role(ElfRole.FINAL)
        self._reserve_elf = self._get_elf_by_role(ElfRole.RESERVE)
        self._sacrifice_elves = self._get_elves_by_role(ElfRole.SACRIFICE)

    def _get_elf_by_role(self, role: str) -> Optional[Dict]:
        """获取指定角色的第一个精灵"""
        for elf in self.elves:
            if elf.get("role") == role:
                return elf
        return None

    def _get_elves_by_role(self, role: str) -> List[Dict]:
        """获取指定角色的所有精灵"""
        return [elf for elf in self.elves if elf.get("role") == role]

    @property
    def final_elf(self) -> Dict:
        """获取 final 精灵"""
        if not self._final_elf:
            raise ValueError("配置中未找到 final 精灵")
        return self._final_elf

    @property
    def reserve_elf(self) -> Dict:
        """获取 reserve 精灵"""
        if not self._reserve_elf:
            raise ValueError("配置中未找到 reserve 精灵")
        return self._reserve_elf

    @property
    def sacrifice_elves(self) -> List[Dict]:
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

    def find_elf_position(self, elf: Dict) -> Optional[tuple]:
        """在切换精灵面板中查找精灵位置

        Args:
            elf: 精灵配置 dict，template 支持单字符串或字符串数组

        Returns:
            (x, y) 或 None
        """
        templates = elf["template"]
        # 兼容单字符串和数组两种配置方式
        if isinstance(templates, str):
            templates = [templates]

        for template in templates:
            pos = self.controller.find_image(template, similarity=0.8)
            if pos != (-1, -1):
                logger.debug(f"找到精灵: {elf['name']} ({template}) @ {pos}")
                return pos

        logger.warning(f"未找到精灵: {elf['name']} (尝试了 {templates})")
        return None

    def get_sacrifice_order(self, faster: bool) -> List[Dict]:
        """获取送死顺序

        Args:
            faster: True=我方速度快，False=对方速度快

        Returns:
            按送死顺序排列的精灵列表
        """
        if faster:
            # 我方先手: final -> sacrifice -> sacrifice -> reserve
            order = [self.final_elf] + self.sacrifice_elves + [self.reserve_elf]
        else:
            # 对方先手: reserve -> sacrifice -> sacrifice -> final
            order = [self.reserve_elf] + self.sacrifice_elves + [self.final_elf]
        return order

    def get_selfdestruct_templates(self) -> List[str]:
        """获取自爆流敌方精灵的头像模板列表"""
        return self.config.get("selfdestruct_enemies", [])

    def get_sacrifice_template(self) -> str:
        """获取送死精灵的模板路径

        Returns:
            送死精灵的模板路径（第一个 sacrifice 精灵）
        """
        if not self._sacrifice_elves:
            raise ValueError("配置中未找到 sacrifice 精灵")
        return self._sacrifice_elves[0]["template"]

    def get_reserve_template(self) -> str:
        """获取备用精灵的模板路径

        Returns:
            备用精灵的模板路径
        """
        if not self._reserve_elf:
            raise ValueError("配置中未找到 reserve 精灵")
        return self._reserve_elf["template"]
