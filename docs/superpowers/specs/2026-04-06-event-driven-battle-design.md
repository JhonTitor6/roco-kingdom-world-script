# 事件驱动战斗架构设计

## 1. 概述

将现有洛克王国自动化脚本从「顺序流程驱动」重构为「事件驱动+状态机」架构，支持中途启动（任意画面切入可自动介入）。

## 2. 核心目标

1. **事件驱动**：图像出现触发处理器，而非轮询检查
2. **状态相关优先**：每个状态只处理该状态关心的事件
3. **中途自启动**：脚本启动时检测当前画面，自动进入对应状态
4. **保留核心逻辑**：dot 计数、速度检测、送死顺序等核心逻辑不变

## 3. 架构组件

```
EventDispatcher           # 事件分发器：主循环 + 图像检测 + 处理器调用
├── GameController        # 图像识别（现有）
├── BattleStateMachine    # 状态机：状态定义 + 转换 + 上下文
├── handlers/             # 事件处理器包
│   ├── __init__.py
│   ├── base_handler.py       # 基类 Handler
│   ├── start_challenge.py    # START_CHALLENGE 处理器
│   ├── select_elf.py         # SELECT_FIRST 处理器
│   ├── confirm.py             # CONFIRM_FIRST 处理器
│   ├── battle.py              # BATTLE_START / SPEED_CHECK / SACRIFICE_PHASE / FINAL_PHASE
│   ├── battle_end.py         # BATTLE_END 处理器
│   └── retry.py               # RETRY / QUIT 处理器
└── events.py             # 事件定义枚举
```

## 4. 状态定义

```python
class BattleState(Enum):
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

**ERROR 状态触发条件**：
- 图像识别超时（等待某图像出现但超时）
- 游戏窗口未找到（`GameWindowNotFoundError`）
- Handler 处理返回 `False` 时进入
- 其他未捕获异常

**ERROR 状态处理**：记录日志、保存调试截图、重置状态为 IDLE，准备重试当前轮

## 5. 事件定义

| 事件 | 触发图像 | 说明 |
|------|----------|------|
| START_CHALLENGE_DETECTED | start_challenge.png | 开始挑战按钮出现 |
| CONFIRM_LINEUPS_DETECTED | confirm_lineups.png | 确认阵容界面 |
| CONFIRM_DETECTED | confirm.png | 确认按钮 |
| COMET_DETECTED | comet.png | 彗星技能图标（战斗进行中） |
| BATTLE_END_DETECTED | battle_end.png | 战斗结束 |
| RETRY_DETECTED | retry.png | 再次切磋 |
| OPPONENT_QUIT_DETECTED | opponent_dont_want_to_retry.png | 对手不想再切磋 |
| INSUFFICIENT_DETECTED | insufficient.png | 精灵不足弹窗 |
| SWITCH_PANEL_DETECTED | 精灵头像 x<600 | 切换面板已打开 |

## 6. 自启动检测

### 6.1 检测优先级

脚本启动时，按以下优先级检测当前画面：

1. `battle_end.png` → BATTLE_END
2. `retry.png` → RETRY
3. `opponent_dont_want_to_retry.png` → QUIT
4. `start_challenge.png` → START_CHALLENGE（点击后进入 SELECT_FIRST）
5. `confirm_lineups.png` → SELECT_FIRST（直接选精灵，无需等待）
6. `comet.png`（战斗中）→ 根据 dot 数量推断进度

**进入 SELECT_FIRST 后的选精灵逻辑**：
- 复用 `SkillExecutor.select_first_elf()` 方法
- 使用 `ElfManager.final_elf` 配置

### 6.2 dot 数量进度推断

在战斗画面（检测到 comet.png）时，根据 dot 数量推断当前进度：

**区域定义**（复用现有 `battle_flow.py` 的定义）：
- 我方区域：`ally_region = (0, 0, 700, 320)`（左上）
- 敌方区域：`enemy_region = (2000, 0, 2560, 320)`（右上）

**进度推断表**：

| 我方 dot | 敌方 dot | 推断状态 | 继续动作 |
|----------|----------|----------|----------|
| 0 | 0 | SPEED_CHECK | 释放 comet，检测速度 |
| 1 | 0 | SACRIFICE_PHASE (faster) | 继续 faster 流程 |
| 0 | 1 | SACRIFICE_PHASE (slower) | 继续 slower 流程 |
| ≥2 | 任意 | SACRIFICE_PHASE | 继续送死（sacrifice 未完成） |
| 0 | ≥3 | FINAL_PHASE | reserve 送死后 final 送死 |

**判断条件**：
- 我方 dot = `len(find_images_all("dots/dot_inactive.png", region=ally_region))`
- 敌方 dot = `len(find_images_all("dots/dot_inactive.png", region=enemy_region))`

## 7. 状态相关优先

每个状态只处理自己关心的事件，忽略其他：

```python
# SACRIFICE_PHASE 状态下的事件处理
if state == SACRIFICE_PHASE:
    if comet := find_image("comet.png"):
        cast_skill("comet")  # 处理
    if battle_end := find_image("battle_end.png"):
        pass  # 忽略，BATTLE_END 是另一个状态的事
    if insufficient := find_image("insufficient.png"):
        pass  # 忽略，进入战斗后不会有这个弹窗
```

## 8. 事件处理器接口

```python
class Handler(ABC):
    """处理器基类

    每个 Handler 只处理特定状态，通过 EventDispatcher 按状态分发。
    """

    def __init__(self, dispatcher: 'EventDispatcher'):
        self.dispatcher = dispatcher

    @abstractmethod
    def handle(self) -> bool:
        """处理当前状态的逻辑，返回是否继续循环"""
        pass

    def transition(self, new_state: BattleState) -> None:
        """切换状态"""
        self.dispatcher.state = new_state
```

## 9. 主循环流程

```python
class EventDispatcher:
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

    def run(self, loop_count: int):
        for i in range(loop_count):
            # 1. 自启动检测（仅第一次）
            if i == 0:
                self.state = self.auto_detect_initial_state()
            else:
                self.state = BattleState.IDLE

            # 2. 主循环
            while not self.is_terminal_state(self.state):
                # 捕获画面
                self.ctrl.capture()

                # 获取当前状态的处理器并执行
                handler_class = self.HANDLERS.get(self.state)
                if handler_class:
                    handler = handler_class(self)
                    if not handler.handle():
                        # Handler 返回 False 进入 ERROR 状态
                        self.transition(BattleState.ERROR)
                        break

                # 短暂休眠
                random_sleep(0.3)

    def is_terminal_state(self, state) -> bool:
        """判断是否为终止状态（需要退出主循环）

        - QUIT: 正常结束，退出本轮
        - ERROR: 异常，Handler 会重置为 IDLE 重试
        """
        return state == BattleState.QUIT
```

**说明**：
- `EventDispatcher` 按状态分发给对应 Handler，不使用 `can_handle` 筛选
- `can_handle` 被移除，简化设计
- Handler 通过 `self.dispatcher.state = new_state` 切换状态

### 9.1 auto_detect_initial_state 实现

```python
def auto_detect_initial_state(self) -> BattleState:
    """自启动检测当前游戏画面状态"""
    self.ctrl.capture()

    # 按优先级检测（见 Section 6.1）
    if self.find_image("battle/battle_end.png"):
        return BattleState.BATTLE_END
    if self.find_image("battle/retry.png"):
        return BattleState.RETRY
    if self.find_image("battle/opponent_dont_want_to_retry.png"):
        return BattleState.QUIT
    if self.find_image("battle/start_challenge.png"):
        return BattleState.START_CHALLENGE
    if self.find_image("popup/confirm_lineups.png"):
        return BattleState.SELECT_FIRST

    # comet.png 存在 → 战斗中，根据 dot 推断
    if self.find_image("skills/comet.png"):
        ally = self.count_inactive_ally()
        enemy = self.count_inactive_enemy()
        if ally == 0 and enemy == 0:
            return BattleState.SPEED_CHECK
        if ally >= 1 and enemy == 0:
            # faster 流程中途：我方已开始送死
            self.flow_type = FASTER
            return BattleState.SACRIFICE_PHASE
        if ally == 0 and enemy >= 1:
            # slower 流程中途：敌方已开始送死
            self.flow_type = SLOWER
            return BattleState.SACRIFICE_PHASE
        if ally >= 2 or enemy >= 3:
            # 送死阶段继续
            return BattleState.SACRIFICE_PHASE

    return BattleState.IDLE
```

## 10. faster/slower 流程保留

战斗阶段的 faster/slower 流程保持现有逻辑，嵌入到 `BattleHandler` 中：

```python
class BattleHandler:
    def handle_sacrifice_phase(self, events):
        # 检测速度优势
        if self.state == SPEED_CHECK:
            cast_skill("comet")
            faster = detect_speed_advantage()
            if faster:
                self.flow_type = FASTER
                self.transition(SACRIFICE_PHASE)
            else:
                self.flow_type = SLOWER
                self.transition(SACRIFICE_PHASE)

        # SACRIFICE_PHASE - 状态+时间驱动
        if self.state == SACRIFICE_PHASE:
            if self.flow_type == FASTER:
                # sacrifice 送死 → 轮询等待我方 dot=3 → 切换 reserve
                self._faster_loop()
            else:
                # final 防御循环 → 轮询等待敌方 dot=3 → reserve 送死
                self._slower_loop()

    def _faster_loop(self) -> bool:
        """faster 流程轮询

        Returns:
            True=流程正常完成，False=异常/超时时进入 ERROR
        """
        # 1. sacrifice 精灵送死
        for elf in self.sacrifice_elves:
            if not self.switch_to_elf(elf):
                return False
            if not self.cast_skill("comet"):
                return False

        # 2. 轮询等待我方 dot_inactive = 3
        while self.count_inactive_ally() < 3:
            random_sleep(1)

        # 3. 切换 reserve
        if not self.switch_to_elf(self.reserve_elf):
            return False

        # 4. 进入 FINAL_PHASE
        self.transition(BattleState.FINAL_PHASE)
        return True

    def _slower_loop(self) -> bool:
        """slower 流程轮询

        Returns:
            True=流程正常完成，False=异常/超时时进入 ERROR
        """
        # 1. final 防御循环，直到敌方 dot_inactive = 3
        while self.count_inactive_enemy() < 3:
            if self.is_skill_releasable():
                self.cast_skill("defense") or self.press_energy()
            random_sleep(1)

        # 2. 切换 reserve
        if not self.switch_to_elf(self.reserve_elf):
            return False

        # 3. reserve 送死
        if not self.cast_skill("comet", elf=self.reserve_elf):
            return False

        # 4. sacrifice 精灵送死
        for elf in self.sacrifice_elves:
            if not self.switch_to_elf(elf):
                return False
            if not self.cast_skill("comet"):
                return False

        # 5. 切换 final 并送死
        if not self.switch_to_elf(self.final_elf):
            return False
        if not self.cast_skill("comet"):
            return False

        # 6. 进入 FINAL_PHASE
        self.transition(BattleState.FINAL_PHASE)
        return True

    def handle_final_phase(self) -> bool:
        """FINAL_PHASE 处理

        reserve 精灵已送死，final 精灵在场。
        循环执行：防御/聚能，直到战斗结束。
        """
        while True:
            # 检测战斗结束
            if self.find_image("battle/battle_end.png"):
                self.transition(BattleState.BATTLE_END)
                return True

            # 可释放技能则释放
            if self.is_skill_releasable():
                self.cast_skill("defense") or self.press_energy()

            random_sleep(1)
```

## 11. 文件变更

| 文件 | 操作 | 说明 |
|------|------|------|
| `src/event_dispatcher.py` | 新增 | 事件分发器主类 |
| `src/handlers/__init__.py` | 新增 | 处理器包初始化 |
| `src/handlers/base_handler.py` | 新增 | Handler 基类 |
| `src/handlers/start_challenge.py` | 新增 | 开始挑战处理器 |
| `src/handlers/select_elf.py` | 新增 | 选择精灵处理器 |
| `src/handlers/confirm.py` | 新增 | 确认处理器 |
| `src/handlers/battle.py` | 新增 | 战斗处理器（核心） |
| `src/handlers/battle_end.py` | 新增 | 战斗结束处理器 |
| `src/handlers/retry.py` | 新增 | 重试处理器 |
| `src/handlers/error.py` | 新增 | ERROR 状态处理器（保存截图、重置状态） |
| `src/events.py` | 新增 | 事件枚举定义 |
| `src/state_machine.py` | 重构 | 简化为状态枚举（事件处理器接管逻辑） |
| `src/battle_flow.py` | 重构 | 保留 dot 计数等工具方法，移除流程控制 |

## 12. 兼容性

- `GameController` 保持不变
- `ElfManager` 保持不变
- `SkillExecutor` 保持不变
- `settings.json` / `elves.json` 保持不变
- 现有模板文件路径不变
