# 彗星技能与防御/聚能交替设计

**日期**: 2026-04-04
**状态**: Approved

---

## 1. 概述

本次设计解决两个需求：
1. 所有技能释放后统一等待 N 秒（可配置），因为技能动画和对方思考需要时间
2. 防御/聚能交替逻辑：实时检测防御技能图标状态，能释放则释放防御，不能则聚能

---

## 2. 配置修改

### config/settings.json

添加 `skill_wait_after_cast` 配置项：

```json
{
  "skill_wait_after_cast": 10,
  ...
}
```

---

## 3. 代码修改

### 3.1 SkillExecutor.cast_skill 增加 timeout 参数

**文件**: `src/skill_executor.py`

```python
def cast_skill(self, skill_name: str, timeout: float = 5) -> bool:
    """释放技能（通过识图点击技能栏）

    Args:
        skill_name: 技能名 (comet / defense)
        timeout: 查找技能图标的超时时间（秒）

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

    pos = self.ctrl.find_image_with_timeout(template, timeout=timeout, similarity=0.8)
    if pos is None:
        logger.warning(f"技能图标未找到: {skill_name}")
        return False

    self.ctrl.click_at(*pos)
    logger.info(f"释放技能: {skill_name}")

    # 技能释放后等待（可配置）
    wait_time = self.ctrl.settings.get("skill_wait_after_cast", 10)
    time.sleep(wait_time)
    return True
```

**关键点**:
- `timeout` 参数传递给 `find_image_with_timeout`，用于检测图标是否出现
- 技能释放后自动等待 `skill_wait_after_cast` 秒
- 默认 timeout=5 秒，默认等待 10 秒

### 3.2 ElfManager 删除 final_action 相关代码

**文件**: `src/elf_manager.py`

删除内容：
1. `__init__` 中的 `self.final_action = config.get("final_action", "energy")`
2. `get_final_action()` 方法

修改后 ElfManager 不再负责决策，只负责管理精灵配置和分类。

### 3.3 防御/聚能交替逻辑

在需要执行 final action 的地方，使用以下模式：

```python
# 尝试释放防御（图标亮=可释放），如果失败（冷却中）则聚能
if not self.skill.cast_skill("defense", timeout=1):
    self.skill.press_energy()
```

**timeout=1**：防御图标在冷却中时 1 秒内会返回失败，快速切换到聚能。

### 3.4 流程修改点

#### 3.4.1 faster_flow (我方速度快)

```python
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

    # 5. reserve 执行最终动作（交替：防御/聚能）
    logger.info("Reserve 精灵防御/聚能交替")
    if not self.skill.cast_skill("defense", timeout=1):
        self.skill.press_energy()
```

#### 3.4.2 slower_flow (我方速度慢)

```python
def slower_flow(self) -> None:
    """我方速度慢的流程"""
    logger.info("=== 速度劣势流程 ===")

    # 1. final 防御/聚能交替
    logger.info("Final 精灵防御/聚能交替")
    if not self.skill.cast_skill("defense", timeout=1):
        self.skill.press_energy()

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
```

#### 3.4.3 sacrifice_sequence

```python
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
            # 尝试释放防御，如果失败则聚能
            if not self.skill.cast_skill("defense", timeout=1):
                self.skill.press_energy()
```

---

## 4. 配置示例

### config/settings.json

```json
{
  "similarity": 0.8,
  "skill_wait_after_cast": 10,
  "timeouts": {
    "battle_start": 10,
    "skill_cast": 5,
    "switch_elf": 3,
    "battle_end": 10
  },
  "loop_count": 10,
  "screenshot_debug": "on_failure",
  "log_level": "DEBUG",
  "window": {
    "class_name": "UnrealWindow",
    "title": "洛克王国：世界"
  }
}
```

### config/elves.json

删除 `final_action` 字段：

```json
{
  "elves": [
    {"name": "精灵A", "template": "elves/elf_1.png", "role": "sacrifice"},
    {"name": "精灵B", "template": "elves/elf_2.png", "role": "sacrifice"},
    {"name": "精灵C", "template": "elves/elf_3.png", "role": "final"},
    {"name": "精灵D", "template": "elves/elf_4.png", "role": "reserve"}
  ]
}
```

---

## 5. 文件变更清单

| 文件 | 操作 |
|------|------|
| `src/skill_executor.py` | 修改：cast_skill 增加 timeout 参数，增加 skill_wait_after_cast 等待 |
| `src/elf_manager.py` | 修改：删除 final_action 属性和 get_final_action() 方法 |
| `src/battle_flow.py` | 修改：faster_flow, slower_flow, sacrifice_sequence 使用新的防御/聚能逻辑 |
| `config/settings.json` | 修改：增加 skill_wait_after_cast 配置项 |
| `config/elves.json` | 修改：删除 final_action 字段 |
