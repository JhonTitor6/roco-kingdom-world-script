# 战斗处理器事件驱动重构实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 `battle.py` 中的固化流程改为事件驱动 + 状态机混合架构，FASTER 分支用决策表，SLOWER 分支用子状态机。

**Architecture:**
- `BattleHandler._faster_loop()` 和 `_slower_loop()` 的 `while` 循环 → 事件驱动，每帧检测切换面板和 dot 数量，决策执行
- FASTER 分支：`SacrificeSubState` 决策表驱动
- SLOWER 分支：`SacrificeSubState` 子状态机管理

**Tech Stack:** Python, unittest, loguru, PIL, cv2

---

## 文件变更概览

| 文件 | 变更 |
|------|------|
| `src/state_machine.py` | 新增 `SacrificeSubState` 枚举 |
| `src/handlers/battle.py` | 重构核心逻辑，新增决策表和子状态机 |
| `src/event_dispatcher.py` | 新增 `_slower_sub_state` 和 `_slower_step` 属性 |
| `tests/unit/test_battle_handler.py` | 新增单元测试 |

---

## Task 1: 新增 SacrificeSubState 枚举

**Files:**
- Modify: `src/state_machine.py`

- [ ] **Step 1: 在 state_machine.py 添加子状态枚举**

在 `BattleState` 枚举后添加：

```python
class SacrificeSubState(Enum):
    """SACRIFICE_PHASE 的子状态（供内部决策使用）"""
    FASTER = auto()                    # FASTER 流程（仅用于标记，不做状态机转换）
    SLOWER_DEFENSE = auto()            # SLOWER 防御期
    SLOWER_SAC = auto()                # SLOWER 送死期
    SLOWER_RESERVE = auto()            # SLOWER 切换 reserve
    SLOWER_FINAL = auto()              # SLOWER final 送死
```

- [ ] **Step 2: 提交**

```bash
git add src/state_machine.py
git commit -m "feat: 添加 SacrificeSubState 枚举"
```

---

## Task 2: 新增 Action 枚举和决策表结构

**Files:**
- Modify: `src/handlers/battle.py`

- [ ] **Step 1: 在 battle.py 顶部添加 Action 枚举**

```python
class Action(Enum):
    """操作枚举"""
    WAIT = auto()                    # 等待，什么都不做
    SWITCH_AND_CAST = auto()         # 切换精灵 + 释放 comet
    SWITCH = auto()                  # 仅切换精灵
    CAST_DEFENSE = auto()            # 释放防御
    PRESS_ENERGY = auto()            # 聚能
```

- [ ] **Step 2: 在 FlowType 枚举后添加辅助方法 `_faster_decide()`**

```python
def _faster_decide(self, ally_dots: int) -> tuple:
    """FASTER 流程决策表

    Returns:
        (action: Action, elf: dict or None)
    """
    if ally_dots < len(self.elf_mgr.sacrifice_elves):
        elf = self.elf_mgr.sacrifice_elves[ally_dots]
        return (Action.SWITCH_AND_CAST, elf)
    elif ally_dots == len(self.elf_mgr.sacrifice_elves):
        return (Action.SWITCH, self.elf_mgr.reserve_elf)
    return (Action.WAIT, None)
```

- [ ] **Step 3: 提交**

```bash
git add src/handlers/battle.py
git commit -m "feat(battle): 添加 Action 枚举和 _faster_decide 决策表"
```

---

## Task 3: 重构 `_handle_sacrifice_phase()` 为事件驱动

**Files:**
- Modify: `src/handlers/battle.py`

- [ ] **Step 1: 重写 `_handle_sacrifice_phase()` 方法**

替换原有的：
```python
def _handle_sacrifice_phase(self) -> bool:
    """送死阶段处理"""
    flow_type = self.dispatcher.flow_type
    if flow_type == FlowType.FASTER:
        return self._faster_loop()
    else:
        return self._slower_loop()
```

改为：
```python
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
```

- [ ] **Step 2: 提交**

```bash
git add src/handlers/battle.py
git commit -m "refactor(battle): 重构 _handle_sacrifice_phase 为事件驱动入口"
```

---

## Task 4: 实现 FASTER 流程事件驱动 `_handle_faster_phase()`

**Files:**
- Modify: `src/handlers/battle.py`

- [ ] **Step 1: 实现 `_handle_faster_phase()` 方法**

```python
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
```

- [ ] **Step 2: 添加辅助方法 `_is_switch_panel_open()`**

```python
def _is_switch_panel_open(self) -> bool:
    """检测精灵切换面板是否打开（头像在 x<600 区域）"""
    elf_templates = ["tree3", "otter2", "pig3", "scepter3"]
    for template in elf_templates:
        pos = self.ctrl.find_image(f"elves/{template}.png", similarity=0.8)
        if pos != (-1, -1) and pos[0] < 600:
            return True
    return False
```

- [ ] **Step 3: 提交**

```bash
git add src/handlers/battle.py
git commit -m "feat(battle): 实现 FASTER 流程事件驱动 _handle_faster_phase"
```

---

## Task 5: 实现 SLOWER 流程子状态机

**Files:**
- Modify: `src/handlers/battle.py`

- [ ] **Step 1: 在 EventDispatcher 中添加 `_slower_sub_state` 属性**

修改 `EventDispatcher.__init__()` 或在 `BattleHandler` 中通过 dispatcher 访问：

```python
# 在 event_dispatcher.py 的 EventDispatcher.__init__ 中添加：
self._slower_sub_state = SacrificeSubState.SLOWER_DEFENSE
self._slower_step = 0  # 送死序列步进
```

- [ ] **Step 2: 实现 `_handle_slower_phase()` 方法**

```python
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
```

- [ ] **Step 3: 实现 `_slower_defense()` 方法**

```python
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
```

- [ ] **Step 4: 实现 `_slower_sac()` 方法**

```python
def _slower_sac(self) -> bool:
    """SLOWER 送死序列：按顺序送死 sacrifice 和 final"""
    step = self.dispatcher._slower_step

    # 检测切换面板是否打开
    if not self._is_switch_panel_open():
        return True

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
        # 切换 final
        if not self.skill.switch_to_elf(self.elf_mgr.final_elf, switch_panel_timeout=30):
            return False
        logger.info("Final 精灵送死")
        if not self.skill.cast_skill("comet"):
            return False
        self.dispatcher._slower_sub_state = SacrificeSubState.SLOWER_RESERVE
    return True
```

- [ ] **Step 5: 实现 `_slower_reserve()` 和 `_slower_final()` 方法**

```python
def _slower_reserve(self) -> bool:
    """SLOWER 切换 reserve"""
    if not self._is_switch_panel_open():
        return True
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
```

- [ ] **Step 6: 提交**

```bash
git add src/handlers/battle.py src/event_dispatcher.py
git commit -m "feat(battle): 实现 SLOWER 流程子状态机"
```

---

## Task 6: 添加单元测试

**Files:**
- Create: `tests/unit/test_battle_handler.py`

- [ ] **Step 1: 编写决策表测试**

```python
import unittest
from unittest.mock import MagicMock, patch


class TestFasterDecisionTable(unittest.TestCase):
    """测试 FASTER 流程决策表"""

    def setUp(self):
        from src.handlers.battle import BattleHandler, FlowType
        from src.event_dispatcher import EventDispatcher

        self.mock_dispatcher = MagicMock(spec=EventDispatcher)
        self.mock_dispatcher.flow_type = FlowType.FASTER
        self.mock_dispatcher.controller = MagicMock()
        self.mock_dispatcher.elf_manager = MagicMock()
        self.mock_dispatcher.skill_executor = MagicMock()

        # 设置 sacrifice_elves 和 reserve_elf
        self.mock_dispatcher.elf_manager.sacrifice_elves = [
            {"name": "sac1", "template": "tree3.png"},
            {"name": "sac2", "template": "otter2.png"},
            {"name": "sac3", "template": "pig3.png"},
        ]
        self.mock_dispatcher.elf_manager.reserve_elf = {"name": "reserve", "template": "scepter3.png"}

        self.handler = BattleHandler(self.mock_dispatcher)

    def test_ally_dots_0_returns_switch_and_cast_first_sacrifice(self):
        from src.handlers.battle import Action
        action, elf = self.handler._faster_decide(0)
        self.assertEqual(action, Action.SWITCH_AND_CAST)
        self.assertEqual(elf["name"], "sac1")

    def test_ally_dots_1_returns_switch_and_cast_second_sacrifice(self):
        from src.handlers.battle import Action
        action, elf = self.handler._faster_decide(1)
        self.assertEqual(action, Action.SWITCH_AND_CAST)
        self.assertEqual(elf["name"], "sac2")

    def test_ally_dots_2_returns_switch_and_cast_third_sacrifice(self):
        from src.handlers.battle import Action
        action, elf = self.handler._faster_decide(2)
        self.assertEqual(action, Action.SWITCH_AND_CAST)
        self.assertEqual(elf["name"], "sac3")

    def test_ally_dots_3_returns_switch_reserve(self):
        from src.handlers.battle import Action
        action, elf = self.handler._faster_decide(3)
        self.assertEqual(action, Action.SWITCH)
        self.assertEqual(elf["name"], "reserve")

    def test_ally_dots_4_returns_wait(self):
        from src.handlers.battle import Action
        action, elf = self.handler._faster_decide(4)
        self.assertEqual(action, Action.WAIT)
        self.assertIsNone(elf)
```

- [ ] **Step 2: 运行测试验证**

```bash
pytest tests/unit/test_battle_handler.py -v
```

预期：测试通过

- [ ] **Step 3: 提交**

```bash
git add tests/unit/test_battle_handler.py
git commit -m "test: 添加 battle handler 决策表单元测试"
```

---

## Task 7: 删除废弃的固化流程代码

**Files:**
- Modify: `src/handlers/battle.py`

- [ ] **Step 1: 删除原有的 `_faster_loop()` 和 `_slower_loop()` 方法**

删除以下方法：
- `_faster_loop()`
- `_slower_loop()`

这些方法已被事件驱动版本替代。

- [ ] **Step 2: 提交**

```bash
git add src/handlers/battle.py
git commit -m "refactor(battle): 删除废弃的 _faster_loop 和 _slower_loop"
```

---

## Task 8: 确保中途启动逻辑正确

**Files:**
- Modify: `src/event_dispatcher.py`

- [ ] **Step 1: 验证 `_auto_detect_initial_state()` 中的中途启动逻辑**

检查以下代码是否正确设置 `_slower_sub_state`：

```python
if ally >= 1:
    # faster 流程（我方已送死 >= 1）
    self._set_flow_type("faster")
    return BattleState.SACRIFICE_PHASE
if ally == 0 and enemy >= 1:
    # slower 流程中途
    self._set_flow_type("slower")
    # 需要设置子状态
    self._slower_sub_state = SacrificeSubState.SLOWER_DEFENSE
    return BattleState.SACRIFICE_PHASE
```

- [ ] **Step 2: 如需要，更新 `_auto_detect_initial_state()` 逻辑**

- [ ] **Step 3: 提交**

```bash
git add src/event_dispatcher.py
git commit -m "fix(dispatcher): 修复中途启动时 slower 子状态初始化"
```

---

## 执行选项

**1. Subagent-Driven (recommended)** - 每个 Task 由独立 subagent 执行，Task 间有检查点

**2. Inline Execution** - 在当前 session 执行，带检查点的批量执行

选择哪种方式？
