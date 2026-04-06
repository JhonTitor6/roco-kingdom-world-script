# 事件驱动战斗架构实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将战斗流程从「顺序流程驱动」重构为「事件驱动+状态机」架构，支持中途启动。

**Architecture:**
- `EventDispatcher` 为主循环，按状态分发给对应 Handler
- 每个 Handler 只处理特定状态，实现 `handle()` 方法
- `BattleState` 枚举定义所有状态，Handler 通过 `transition()` 切换状态
- 自启动时通过 `auto_detect_initial_state()` 检测当前画面并进入对应状态

**Tech Stack:** Python, win_util (图像识别/键鼠控制), loguru (日志)

---

## 文件结构

```
src/
├── event_dispatcher.py    # 新增: 事件分发器主类
├── events.py             # 新增: 事件枚举
├── handlers/            # 新增: 处理器包
│   ├── __init__.py
│   ├── base_handler.py
│   ├── start_challenge.py
│   ├── select_elf.py
│   ├── confirm.py
│   ├── battle.py
│   ├── battle_end.py
│   ├── retry.py
│   └── error.py
├── state_machine.py      # 重构: 仅保留 BattleState 枚举
├── battle_flow.py        # 重构: 保留工具方法，移除流程控制
├── elf_manager.py        # 保持不变
├── skill_executor.py     # 保持不变
└── controller.py         # 保持不变
```

---

## Task 1: 创建 events.py 事件枚举

**Files:**
- Create: `src/events.py`

> **Note**: `Event` 枚举用于文档化所有可能的图像事件，实际运行时通过状态分发处理，不直接使用此枚举。

- [ ] **Step 1: 创建 events.py**

```python
"""事件定义枚举"""
from enum import Enum, auto


class Event(Enum):
    """战斗相关事件"""
    START_CHALLENGE_DETECTED = auto()
    CONFIRM_LINEUPS_DETECTED = auto()
    CONFIRM_DETECTED = auto()
    COMET_DETECTED = auto()
    BATTLE_END_DETECTED = auto()
    RETRY_DETECTED = auto()
    OPPONENT_QUIT_DETECTED = auto()
    INSUFFICIENT_DETECTED = auto()
    SWITCH_PANEL_DETECTED = auto()
```

- [ ] **Step 2: Commit**

```bash
git add src/events.py
git commit -m "feat: 添加事件枚举定义"
```

---

## Task 2: 创建 handlers 包和 base_handler.py

**Files:**
- Create: `src/handlers/__init__.py`
- Create: `src/handlers/base_handler.py`

- [ ] **Step 1: 创建 handlers/__init__.py**

```python
"""事件处理器包"""
from src.handlers.base_handler import Handler
from src.handlers.start_challenge import StartChallengeHandler
from src.handlers.select_elf import SelectElfHandler
from src.handlers.confirm import ConfirmHandler
from src.handlers.battle import BattleHandler
from src.handlers.battle_end import BattleEndHandler
from src.handlers.retry import RetryHandler
from src.handlers.error import ErrorHandler

__all__ = [
    "Handler",
    "StartChallengeHandler",
    "SelectElfHandler",
    "ConfirmHandler",
    "BattleHandler",
    "BattleEndHandler",
    "RetryHandler",
    "ErrorHandler",
]
```

- [ ] **Step 2: 创建 base_handler.py**

```python
"""Handler 基类"""
from abc import ABC, abstractmethod

from src.state_machine import BattleState


class Handler(ABC):
    """处理器基类

    每个 Handler 只处理特定状态，通过 EventDispatcher 按状态分发。
    """

    def __init__(self, dispatcher: "EventDispatcher"):
        self.dispatcher = dispatcher

    @property
    def ctrl(self):
        """获取 GameController"""
        return self.dispatcher.controller

    @property
    def elf_mgr(self):
        """获取 ElfManager"""
        return self.dispatcher.elf_manager

    @property
    def skill(self):
        """获取 SkillExecutor"""
        return self.dispatcher.skill_executor

    @abstractmethod
    def handle(self) -> bool:
        """处理当前状态的逻辑，返回是否继续循环

        Returns:
            True=继续循环，False=进入 ERROR 状态
        """
        pass

    def transition(self, new_state: BattleState) -> None:
        """切换状态"""
        self.dispatcher.state = new_state
```

- [ ] **Step 3: Commit**

```bash
git add src/handlers/__init__.py src/handlers/base_handler.py
git commit -m "feat: 创建 handlers 包和 Handler 基类"
```

---

## Task 3: 创建 StartChallengeHandler

**Files:**
- Create: `src/handlers/start_challenge.py`

- [ ] **Step 1: 创建 StartChallengeHandler**

```python
"""开始挑战处理器"""
from src.handlers.base_handler import Handler
from src.state_machine import BattleState
from src.utils import random_sleep


class StartChallengeHandler(Handler):
    """START_CHALLENGE 状态处理器"""

    def handle(self) -> bool:
        """点击开始挑战，等待进入选精灵界面"""
        # 点击开始挑战
        if not self.ctrl.find_and_click_with_timeout(
            "battle/start_challenge.png", timeout=5
        ):
            # 按钮不存在，可能已处于其他状态
            return True  # 继续循环检测

        random_sleep(1)

        # 检查精灵数不足弹窗
        insufficient_pos = self.ctrl.find_image_with_timeout(
            "popup/insufficient.png", timeout=3, similarity=0.8
        )
        if insufficient_pos is not None:
            self.ctrl.find_and_click_with_timeout("popup/confirm.png", timeout=3)

        # 等待匹配画面出现
        random_sleep(5)

        # 切换到 SELECT_FIRST 状态
        self.transition(BattleState.SELECT_FIRST)
        return True
```

- [ ] **Step 2: Commit**

```bash
git add src/handlers/start_challenge.py
git commit -m "feat: 添加 StartChallengeHandler"
```

---

## Task 4: 创建 SelectElfHandler

**Files:**
- Create: `src/handlers/select_elf.py`

- [ ] **Step 1: 创建 SelectElfHandler**

```python
"""选择精灵处理器"""
from src.handlers.base_handler import Handler
from src.state_machine import BattleState
from src.utils import random_sleep


class SelectElfHandler(Handler):
    """SELECT_FIRST 状态处理器"""

    def handle(self) -> bool:
        """选择首发精灵（final 精灵）"""
        # 等待选精灵界面
        if self.ctrl.find_image_with_timeout(
            "popup/confirm_lineups.png", timeout=60, similarity=0.8
        ) is None:
            return False  # 超时，进入 ERROR

        random_sleep(1)

        # 选择 final 精灵
        if not self.skill.select_first_elf(self.elf_mgr.final_elf):
            return False

        random_sleep(1)

        # 切换到 CONFIRM_FIRST 状态
        self.transition(BattleState.CONFIRM_FIRST)
        return True
```

- [ ] **Step 2: Commit**

```bash
git add src/handlers/select_elf.py
git commit -m "feat: 添加 SelectElfHandler"
```

---

## Task 5: 创建 ConfirmHandler

**Files:**
- Create: `src/handlers/confirm.py`

- [ ] **Step 1: 创建 ConfirmHandler**

```python
"""确认处理器"""
from src.handlers.base_handler import Handler
from src.state_machine import BattleState
from src.utils import random_sleep


class ConfirmHandler(Handler):
    """CONFIRM_FIRST 状态处理器"""

    def handle(self) -> bool:
        """确认首发选择"""
        # 点击确认按钮
        if not self.skill.confirm_selection():
            return False

        random_sleep(10)  # 等待战斗开始

        # 切换到 BATTLE_START 状态
        self.transition(BattleState.BATTLE_START)
        return True
```

- [ ] **Step 2: Commit**

```bash
git add src/handlers/confirm.py
git commit -m "feat: 添加 ConfirmHandler"
```

---

## Task 6: 创建 BattleHandler (核心)

**Files:**
- Create: `src/handlers/battle.py`

- [ ] **Step 1: 创建 battle.py - 状态和常量定义**

```python
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
```

- [ ] **Step 2: 创建 battle.py - BattleHandler 类**

```python
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
```

- [ ] **Step 3: 添加 _handle_sacrifice_phase 和 faster/slower 流程**

```python
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
```

- [ ] **Step 4: 添加 _handle_final_phase**

```python
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
```

- [ ] **Step 5: Commit**

```bash
git add src/handlers/battle.py
git commit -m "feat: 添加 BattleHandler（核心战斗处理器）"
```

---

## Task 7: 创建 BattleEndHandler

**Files:**
- Create: `src/handlers/battle_end.py`

- [ ] **Step 1: 创建 BattleEndHandler**

```python
"""战斗结束处理器"""
from src.handlers.base_handler import Handler
from src.state_machine import BattleState
from src.utils import random_sleep
from loguru import logger


class BattleEndHandler(Handler):
    """BATTLE_END 状态处理器"""

    def handle(self) -> bool:
        """处理战斗结束，点击再次切磋"""
        # 点击战斗结束按钮
        battle_end = self.ctrl.find_image_with_timeout(
            "battle/battle_end.png",
            timeout=self.ctrl.settings["timeouts"]["battle_end"],
            similarity=0.9
        )
        if battle_end is None:
            logger.warning("未检测到战斗结束标志")
            return False

        logger.info("战斗结束")
        self.ctrl.click_at(*battle_end)

        # 点击再次切磋
        if self.ctrl.find_and_click_with_timeout("battle/retry.png", timeout=3):
            random_sleep(10)

        # 检测对手是否不想再切磋
        if self.ctrl.find_image_with_timeout(
            "battle/opponent_dont_want_to_retry.png", timeout=10
        ) != (-1, -1):
            # 对手不想再切磋 → 点击退出
            self.ctrl.find_and_click_with_timeout("battle/quit.png", timeout=2)
            self.transition(BattleState.QUIT)
        else:
            # 可以继续 → 进入 RETRY 状态等待
            self.transition(BattleState.RETRY)

        return True
```

- [ ] **Step 2: Commit**

```bash
git add src/handlers/battle_end.py
git commit -m "feat: 添加 BattleEndHandler"
```

---

## Task 8: 创建 RetryHandler

**Files:**
- Create: `src/handlers/retry.py`

- [ ] **Step 1: 创建 RetryHandler**

```python
"""重试处理器"""
from src.handlers.base_handler import Handler
from src.state_machine import BattleState
from src.utils import random_sleep
from loguru import logger


class RetryHandler(Handler):
    """RETRY / QUIT 状态处理器"""

    def handle(self) -> bool:
        """处理再次切磋或退出"""
        state = self.dispatcher.state

        if state == BattleState.RETRY:
            logger.info("等待再次切磋")
            # 等待 start_challenge.png 出现
            if self.ctrl.find_image_with_timeout(
                "battle/start_challenge.png", timeout=60
            ):
                self.transition(BattleState.START_CHALLENGE)
            else:
                return False

        elif state == BattleState.QUIT:
            logger.info("本轮结束")
            # 点击退出
            self.ctrl.find_and_click_with_timeout("battle/quit.png", timeout=2)
            random_sleep(2)
            # 重置状态，退出本轮循环

        return True
```

- [ ] **Step 2: Commit**

```bash
git add src/handlers/retry.py
git commit -m "feat: 添加 RetryHandler"
```

---

## Task 9: 创建 ErrorHandler

**Files:**
- Create: `src/handlers/error.py`

- [ ] **Step 1: 创建 ErrorHandler**

```python
"""错误处理器"""
import time

from src.handlers.base_handler import Handler
from src.state_machine import BattleState
from loguru import logger


class ErrorHandler(Handler):
    """ERROR 状态处理器"""

    def handle(self) -> bool:
        """处理错误：记录日志、保存截图、重置状态"""
        logger.error("进入 ERROR 状态")

        # 保存调试截图
        self.ctrl.save_debug_screenshot(f"error_{int(time.time())}")

        # 重置状态为 IDLE，准备重试
        self.transition(BattleState.IDLE)
        return True
```

- [ ] **Step 2: Commit**

```bash
git add src/handlers/error.py
git commit -m "feat: 添加 ErrorHandler"
```

---

## Task 10: 创建 EventDispatcher

**Files:**
- Create: `src/event_dispatcher.py`

- [ ] **Step 1: 创建 event_dispatcher.py - 导入和常量定义**

```python
"""事件分发器"""
from src.state_machine import BattleState
from src.handlers import (
    StartChallengeHandler,
    SelectElfHandler,
    ConfirmHandler,
    BattleHandler,
    BattleEndHandler,
    RetryHandler,
    ErrorHandler,
)


# 状态到处理器的映射
HANDLERS = {
    BattleState.START_CHALLENGE: StartChallengeHandler,
    BattleState.SELECT_FIRST: SelectElfHandler,
    BattleState.CONFIRM_FIRST: ConfirmHandler,
    BattleState.BATTLE_START: BattleHandler,
    BattleState.SPEED_CHECK: BattleHandler,
    BattleState.SACRIFICE_PHASE: BattleHandler,
    BattleState.FINAL_PHASE: BattleHandler,
    BattleState.BATTLE_END: BattleEndHandler,
    BattleState.RETRY: RetryHandler,
    BattleState.QUIT: RetryHandler,
    BattleState.ERROR: ErrorHandler,
}
```

- [ ] **Step 2: 创建 EventDispatcher 类**

```python
class EventDispatcher:
    """事件分发器: 主循环 + 图像检测 + 处理器调用"""

    # 区域定义
    ALLY_REGION = (0, 0, 700, 320)
    ENEMY_REGION = (2000, 0, 2560, 320)

    def __init__(
        self,
        controller,
        elf_manager,
        skill_executor,
        settings: dict
    ):
        self.controller = controller
        self.elf_manager = elf_manager
        self.skill_executor = skill_executor
        self.settings = settings
        self.state = BattleState.IDLE

    def run(self, loop_count: int) -> None:
        """运行主循环"""
        for i in range(loop_count):
            # 重置 flow_type（每轮重新检测速度）
            self._flow_type = None

            # 1. 自启动检测（仅第一次）
            if i == 0:
                self.state = self._auto_detect_initial_state()
            else:
                self.state = BattleState.IDLE

            # 2. 主循环
            while not self._is_terminal_state():
                # 捕获画面
                self.controller.capture()

                # 获取当前状态的处理器并执行
                handler_class = HANDLERS.get(self.state)
                if handler_class:
                    handler = handler_class(self)
                    if not handler.handle():
                        # Handler 返回 False 进入 ERROR 状态
                        self.state = BattleState.ERROR
                        break

                # 短暂休眠
                self._sleep(0.3)

    def _is_terminal_state(self) -> bool:
        """判断是否为终止状态"""
        return self.state == BattleState.QUIT

    def _sleep(self, seconds: float) -> None:
        """休眠（复用现有 random_sleep）"""
        from src.utils import random_sleep
        random_sleep(seconds)

    def _auto_detect_initial_state(self) -> BattleState:
        """自启动检测当前游戏画面状态"""
        self.controller.capture()

        # 按优先级检测
        if self.controller.find_image("battle/battle_end.png", similarity=0.9) != (-1, -1):
            return BattleState.BATTLE_END
        if self.controller.find_image("battle/retry.png", similarity=0.8) != (-1, -1):
            return BattleState.RETRY
        if self.controller.find_image("battle/opponent_dont_want_to_retry.png", similarity=0.8) != (-1, -1):
            return BattleState.QUIT
        if self.controller.find_image("battle/start_challenge.png", similarity=0.8) != (-1, -1):
            return BattleState.START_CHALLENGE
        if self.controller.find_image("popup/confirm_lineups.png", similarity=0.8) != (-1, -1):
            return BattleState.SELECT_FIRST

        # comet.png 存在 → 战斗中，根据 dot 推断
        if self.controller.find_image("skills/comet.png", similarity=0.8) != (-1, -1):
            ally = self._count_inactive_ally()
            enemy = self._count_inactive_enemy()
            if ally == 0 and enemy == 0:
                return BattleState.SPEED_CHECK
            if ally >= 1:
                # faster 流程（我方已送死 >= 1）
                self._set_flow_type("faster")
                return BattleState.SACRIFICE_PHASE
            if ally == 0 and enemy >= 1:
                # slower 流程中途
                self._set_flow_type("slower")
                return BattleState.SACRIFICE_PHASE
            if ally == 0 and enemy >= 3:
                # 敌方已送死3只，我方未动 → FINAL_PHASE
                return BattleState.FINAL_PHASE

        return BattleState.IDLE

    def _count_inactive_ally(self) -> int:
        """统计我方 inactive dots"""
        dots = self.controller.find_images_all(
            "dots/dot_inactive.png",
            similarity=0.8,
            x0=self.ALLY_REGION[0], y0=self.ALLY_REGION[1],
            x1=self.ALLY_REGION[2], y1=self.ALLY_REGION[3]
        )
        return len(dots)

    def _count_inactive_enemy(self) -> int:
        """统计敌方 inactive dots"""
        dots = self.controller.find_images_all(
            "dots/dot_inactive.png",
            similarity=0.8,
            x0=self.ENEMY_REGION[0], y0=self.ENEMY_REGION[1],
            x1=self.ENEMY_REGION[2], y1=self.ENEMY_REGION[3]
        )
        return len(dots)

    @property
    def flow_type(self):
        """获取流程类型"""
        return self._flow_type

    def _set_flow_type(self, flow_type: str) -> None:
        """设置流程类型（供中途启动时使用）"""
        # FlowType 枚举需要从 battle handler 导入
        from src.handlers.battle import FlowType
        self._flow_type = FlowType.FASTER if flow_type == "faster" else FlowType.SLOWER
```

- [ ] **Step 3: Commit**

```bash
git add src/event_dispatcher.py
git commit -m "feat: 添加 EventDispatcher 事件分发器"
```

---

## Task 11: 重构 state_machine.py

**Files:**
- Modify: `src/state_machine.py`

- [ ] **Step 1: 简化 state_machine.py 为仅保留 BattleState 枚举**

```python
"""战斗状态枚举"""
from enum import Enum


class BattleState(Enum):
    """战斗状态枚举"""
    IDLE = "idle"                      # 等待开始
    START_CHALLENGE = "start_challenge"  # 已点击开始挑战
    SELECT_FIRST = "select_first"        # 选择首发精灵
    CONFIRM_FIRST = "confirm_first"     # 确认首发
    BATTLE_START = "battle_start"       # 等待战斗开始
    SPEED_CHECK = "speed_check"         # 检测速度优势
    SACRIFICE_PHASE = "sacrifice_phase"  # 送死阶段（faster/slower）
    FINAL_PHASE = "final_phase"         # 最终精灵阶段
    BATTLE_END = "battle_end"            # 战斗结束
    RETRY = "retry"                     # 再次切磋
    QUIT = "quit"                       # 退出（本轮结束）
    ERROR = "error"                     # 错误（异常时触发，重试本轮）
```

- [ ] **Step 2: Commit**

```bash
git add src/state_machine.py
git commit -m "refactor: 简化 state_machine.py 为仅保留 BattleState 枚举"
```

---

## Task 12: 重构 battle_flow.py

**Files:**
- Modify: `src/battle_flow.py`

- [ ] **Step 1: 移除流程控制代码，保留工具方法**

`battle_flow.py` 中的 `BattleFlow` 类将被拆分：
- 工具方法（`count_inactive_in_region`, `is_skill_releasable` 等）保留，但移入 EventDispatcher 或 BattleHandler
- 流程控制方法（`run_entry_flow`, `faster_flow`, `slower_flow` 等）已由 Handler 实现，删除

由于 BattleHandler 已经实现了这些方法，可以选择：
- 删除 `BattleFlow` 类
- 或者保留空的 `BattleFlow` 类作为向后兼容

建议保留 `BattleFlow` 作为兼容层，但清空其方法体，仅保留导入。

- [ ] **Step 2: Commit**

```bash
git add src/battle_flow.py
git commit -m "refactor: 重构 battle_flow.py，移除流程控制代码"
```

---

## Task 13: 更新 main.py 使用 EventDispatcher

**Files:**
- Modify: `main.py`

- [ ] **Step 1: 查看现有 main.py**

```bash
cat main.py
```

- [ ] **Step 2: 更新 main.py 使用 EventDispatcher**

```python
"""程序入口"""
import json

from src.window import find_window
from src.controller import GameController
from src.elf_manager import ElfManager
from src.skill_executor import SkillExecutor
from src.event_dispatcher import EventDispatcher
from loguru import logger


def main():
    # 1. 初始化组件
    hwnd = find_window("洛克王国：世界")
    with open("config/settings.json", "r", encoding="utf-8") as f:
        settings = json.load(f)
    elf_config = json.load(open("config/elves.json", "r", encoding="utf-8"))

    controller = GameController(hwnd, settings)
    elf_manager = ElfManager(elf_config, controller)
    skill_executor = SkillExecutor(controller)

    # 2. 创建事件分发器并运行
    dispatcher = EventDispatcher(controller, elf_manager, skill_executor, settings)
    dispatcher.run(loop_count=settings.get("loop_count", 10))

    logger.info("脚本执行完成")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Commit**

```bash
git add main.py
git commit -m "feat: 使用 EventDispatcher 替换原有状态机"
```

---

## Task 14: 运行测试验证

**Files:**
- Run: `pytest tests/ -v`

- [ ] **Step 1: 运行测试**

```bash
pytest tests/ -v --tb=short
```

- [ ] **Step 2: 如有测试失败，修复问题**

- [ ] **Step 3: Commit 测试修复**

---

## 验证清单

- [ ] `src/events.py` 存在且定义正确
- [ ] `src/handlers/` 包完整，包含所有 Handler
- [ ] `src/state_machine.py` 仅包含 BattleState 枚举
- [ ] `src/event_dispatcher.py` 主循环正常
- [ ] `main.py` 使用 EventDispatcher
- [ ] 所有测试通过
