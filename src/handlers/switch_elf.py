from loguru import logger

from src.handlers.base_handler import Handler
from src.context import GameContext
from src.events import Events
from src.registry import EventRegistry


class SwitchElfHandler(Handler):
    """切换精灵处理器"""
    CONFIRM_POS = 1543, 956
    ELF_REGION = (250, 327, 550, 1200)

    def __init__(self, dispatcher):
        super().__init__(dispatcher)
        self._sacrifice_index = 0
        self._switched_elves = set()  # 已成功切换过的精灵模板集合

    def reset(self) -> None:
        """重置状态（每场新战斗开始时调用）"""
        self._sacrifice_index = 0
        self._switched_elves.clear()

    def handle(self, ctx: GameContext, position=None) -> None:
        """处理切换精灵事件

        Args:
            ctx: 游戏共享状态上下文
            position: 检测到的图像坐标
        """
        if ctx.is_slower():
            if ctx.enemy_inactive < 3:
                return
            reserve_template = self.elf_mgr.get_reserve_template()
            if reserve_template not in self._switched_elves:
                if self._try_switch_elf(reserve_template):
                    self._switched_elves.add(reserve_template)
                    return
                # Reserve切换失败（死亡），回落尝试sacrifice
            self._try_switch_sacrifice()
        else:
            # FASTER
            if ctx.my_inactive < 3:
                self._try_switch_sacrifice()
                return
            # my_inactive >= 3，优先尝试reserve
            reserve_template = self.elf_mgr.get_reserve_template()
            if reserve_template not in self._switched_elves:
                if self._try_switch_elf(reserve_template):
                    self._switched_elves.add(reserve_template)
                    return
                # Reserve失败，回落尝试sacrifice
            self._try_switch_sacrifice()

    def _try_switch_elf(self, template) -> bool:
        """获取精灵模板、记录日志并尝试切换

        Args:
            elf_getter: 获取精灵模板路径的函数

        Returns:
            是否切换成功
        """
        logger.info(f"尝试切换精灵: {template}")
        return self._switch_to_elf(template)

    def _try_switch_sacrifice(self) -> bool:
        """尝试切换送死精灵，切换成功后推进索引

        Returns:
            是否切换成功
        """
        elves = self.elf_mgr.get_sacrifice_elves()
        if not elves:
            logger.warning("没有可用的送死精灵")
            return False

        for _ in range(len(elves)):
            elf = elves[self._sacrifice_index % len(elves)]
            logger.info(f"尝试切换精灵: {elf.template}")
            if self._switch_to_elf(elf.template):
                # 切换成功，推进索引
                self._sacrifice_index = (self._sacrifice_index + 1) % len(elves)
                return True

            # 切换失败，推进索引尝试下一个
            self._sacrifice_index = (self._sacrifice_index + 1) % len(elves)

        return False

    def _switch_to_elf(self, elf_template: str) -> bool:
        """切换到指定精灵

        Args:
            elf_template: 精灵模板路径

        Returns:
            是否切换成功
        """
        x0, y0, x1, y1 = self.ELF_REGION
        pos = self.ctrl.find_image_with_timeout(
            elf_template, timeout=1, x0=x0, y0=y0, x1=x1, y1=y1
        )
        if not pos:
            return False

        self.ctrl.click_at(*pos)
        self.random_sleep(1, 2)
        self.ctrl.click_at(*self.CONFIRM_POS)
        return True

    def _positions_similar(self, pos1, pos2, threshold=10) -> bool:
        """判断两个位置是否在阈值内相近"""
        if pos1 is None or pos2 is None:
            return False
        return abs(pos1[0] - pos2[0]) <= threshold and abs(pos1[1] - pos2[1]) <= threshold


EventRegistry.register(
    event=Events.SWITCH_ELF,
    handler_cls=SwitchElfHandler,
    template=["elves/tree3.png", "elves/otter2.png", "elves/pig3.png", "elves/scepter3.png"],
    region=SwitchElfHandler.ELF_REGION,
    similarity=0.8
)
