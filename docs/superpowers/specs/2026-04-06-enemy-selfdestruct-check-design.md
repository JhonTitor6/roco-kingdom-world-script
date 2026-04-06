# 敌方自爆流检测与退出设计

## 概述

在战斗开始后（BATTLE_START 状态），检测敌方精灵头像是否为自爆流。如果不是，则退出战斗。

## 功能需求

1. **敌方自爆流检测**：通过图像识别检测敌方头像是否匹配配置的自爆流模板
2. **退出战斗**：检测到非自爆流时，点击逃跑按钮并确认退出
3. **直接退出**：退出后跳过"再次切磋"，直接结束本轮

## 配置变更

### config/settings.json

新增 `enemy_region` 字段（敌方头像检测区域，与 `battle.py` 中的 `ENEMY_REGION` 不同用途）：

```json
{
  "enemy_region": [2090, 14, 2273, 181]
}
```

**注意**：`battle.py` 中的 `ENEMY_REGION = (2000, 0, 2560, 320)` 用于 dot 状态检测，而本字段用于敌方头像识别，两者用途和范围不同。

### config/elves.json

在 `ElfRole` 类中新增 `SELFDESTRUCT` 常量，并在 elves.json 中新增 `selfdestruct` 角色类型的精灵配置：

```json
{
  "elves": [
    {"name": "蝴蝶", "template": ["elves/butterfly_3.png", "elves/butterfly_other.png"], "role": "selfdestruct"},
    ...
  ]
}
```

## 代码变更

### src/elf_manager.py

修改 `ElfRole` 类添加常量：

```python
class ElfRole:
    """精灵角色常量"""
    SACRIFICE = "sacrifice"  # 送死精灵
    FINAL = "final"         # 最后送死
    RESERVE = "reserve"     # 备用
    SELFDESTRUCT = "selfdestruct"  # 自爆流敌方精灵（用于检测）
```

新增 `get_selfdestruct_templates()` 方法：

```python
def get_selfdestruct_templates(self) -> List[str]:
    """获取自爆流敌方精灵的头像模板列表"""
    templates = []
    for elf in self.elves:
        if elf.get("role") == ElfRole.SELFDESTRUCT:
            template = elf.get("template")
            if isinstance(template, str):
                templates.append(template)
            elif isinstance(template, list):
                templates.extend(template)
    return templates
```

### src/handlers/battle.py

新增 `_check_enemy_selfdestruct()` 方法：

```python
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
    enemy_region = self.ctrl.settings.get(
        "enemy_region",
        [2090, 14, 2273, 181]  # 默认值
    )
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
```

新增 `_escape_battle()` 方法：

```python
def _escape_battle(self) -> bool:
    """执行逃跑操作：点击 escape.png → confirm.png"""
    if not self.ctrl.find_and_click_with_timeout("skills/escape.png", timeout=5, similarity=0.8):
        return False
    random_sleep(0.5)
    if not self.ctrl.find_and_click_with_timeout("popup/confirm.png", timeout=5, similarity=0.8):
        return False
    return True
```

修改 `_handle_battle_start()` 方法：

```python
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
    # 新增：检测敌方是否为自爆流
    if not self._check_enemy_selfdestruct():
        return True  # 已触发退出（BATTLE_END 或 ERROR 状态）
    self.transition(BattleState.SPEED_CHECK)
    return True
```

### src/handlers/battle_end.py

修改 `BattleEndHandler.handle()` 方法，跳过再次切磋：

```python
class BattleEndHandler(Handler):
    def handle(self) -> bool:
        # 1. 点击战斗结束按钮 battle_end.png
        # 2. 检测是否需要直接退出（由 _check_enemy_selfdestruct 设置的 flag）
        if getattr(self.dispatcher, '_exit_directly', False):
            logger.info("直接退出，不进行再次切磋")
            self.transition(BattleState.QUIT)
            return True

        # 原有逻辑：点击再次切磋 retry.png
        ...
```

## 事件驱动设计

所有操作尽量原子化，采用事件驱动：

1. `_check_enemy_selfdestruct()` 是原子操作，一次性完成检测和退出
2. `_escape_battle()` 是原子操作，完成逃跑点击
3. 状态转换通过 `self.transition()` 触发，由 EventDispatcher 统一分发
4. `_exit_directly` flag（通过 `getattr(self.dispatcher, '_exit_directly', False)` 访问）传递信息给 BattleEndHandler，避免状态机复杂度增加

## 错误处理

| 场景 | 处理方式 |
|------|----------|
| escape.png 未找到 | 返回 False，进入 ERROR 状态 |
| confirm.png 未找到 | 返回 False，进入 ERROR 状态 |
| 未配置 selfdestruct 精灵 | 记录警告，继续战斗 |
| enemy_region 未在 settings.json 配置 | 使用默认值 [2090, 14, 2273, 181] |
