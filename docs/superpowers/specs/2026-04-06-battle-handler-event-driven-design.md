# 战斗处理器事件驱动重构设计

## 1. 背景

当前 `src/handlers/battle.py` 中的 `_faster_loop()` 和 `_slower_loop()` 使用顺序执行的 `while` 循环轮询等待条件（如 `dot_inactive` 数量）。这种固化流程难以处理中途启动、异常中断等场景，程序健壮性不足。

## 2. 目标

- 将固化流程改为事件驱动 + 状态机混合架构
- 每次检测到精灵切换面板打开（`SWITCH_PANEL_DETECTED`）时，根据 `(flow_type, ally_dot_count)` 决策下一步操作
- 提高程序健壮性，支持中途启动

## 3. 整体架构

```
EventDispatcher（主循环）
│
├── 每次循环：capture() → 检测事件 → 分发到 Handler
│
└── BattleHandler（SACRIFICE_PHASE）
    │
    ├── FASTER 分支：决策表驱动
    │   └── _faster_decide(ally_dots) → 执行对应操作
    │
    └── SLOWER 分支：子状态机
        ├── SLOWER_DEFENSE（防御期）
        └── SLOWER_SAC（送死期）
```

**核心变化**：
- `BattleHandler._faster_loop()` 和 `_slower_loop()` 的 `while` 循环 → 改为事件驱动
- 每次 `SWITCH_PANEL_DETECTED` 触发决策，替代原有的轮询阻塞

## 4. 决策逻辑（FASTER 分支）

### 4.1 FASTER 决策表

| ally_dot_count | 操作 |
|----------------|------|
| 0 | 切换到第1个 sacrifice 精灵，释放 comet |
| 1 | 切换到第2个 sacrifice 精灵，释放 comet |
| 2 | 切换到第3个 sacrifice 精灵，释放 comet |
| 3 | 切换到 reserve 精灵 → 进入 FINAL_PHASE |

### 4.2 实现

```python
def _faster_decide(self, ally_dots: int) -> Action:
    """FASTER 流程决策表"""
    elf_map = {
        0: self.elf_mgr.sacrifice_elves[0] if len(self.elf_mgr.sacrifice_elves) > 0 else None,
        1: self.elf_mgr.sacrifice_elves[1] if len(self.elf_mgr.sacrifice_elves) > 1 else None,
        2: self.elf_mgr.sacrifice_elves[2] if len(self.elf_mgr.sacrifice_elves) > 2 else None,
        3: self.elf_mgr.reserve_elf,
    }
    elf = elf_map.get(ally_dots)
    if elf is None:
        return Action.WAIT
    if ally_dots == 3:
        return (Action.SWITCH, elf)  # 切换到 reserve 后进入 FINAL_PHASE
    return (Action.SWITCH_AND_CAST, elf)  # 切换 + 释放 comet
```

## 5. 子状态设计（SLOWER 分支）

### 5.1 子状态枚举

```python
class SacrificeSubState(Enum):
    """SACRIFICE_PHASE 的子状态"""
    SLOWER_DEFENSE = auto()   # 防御期：轮询 enemy_dots < 3
    SLOWER_SAC = auto()       # 送死期：按顺序送死
    SLOWER_RESERVE = auto()   # 切换 reserve
    SLOWER_FINAL = auto()     # final 送死 → FINAL_PHASE
```

### 5.2 SLOWER 流程状态转换

```
SLOWER_DEFENSE
├── enemy_dots >= 3 → SLOWER_SAC（step=0）
└── (每帧) 检测可释放技能 → cast defense / press_energy

SLOWER_SAC（step=0~2）
├── step=0: switch sacrifice[0] → cast comet → step=1
├── step=1: switch sacrifice[1] → cast comet → step=2
├── step=2: switch sacrifice[2] → cast comet → step=3
└── step=3: switch final → SLOWER_RESERVE

SLOWER_RESERVE
└── switch reserve → cast comet → SLOWER_FINAL

SLOWER_FINAL
└── switch final → cast comet → FINAL_PHASE
```

## 6. SWITCH_PANEL_DETECTED 事件检测

位置：`SkillExecutor.wait_for_switch_panel()` 已实现，逻辑复用：

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

## 7. 数据流

```
每帧主循环（EventDispatcher.run）：
1. capture()
2. 获取当前状态的 Handler
3. 调用 Handler.handle()
   └→ BattleHandler.handle()
       └→ _handle_sacrifice_phase()
           ├→ 获取 flow_type（FASTER / SLOWER）
           ├→ 统计 ally_dots / enemy_dots
           └→ FASTER: _faster_decide(ally_dots)
              SLOWER: _slower_state_machine() → 按子状态执行

注意：SWITCH_PANEL_DETECTED 事件在 SkillExecutor.switch_to_elf() 内部检测，
不是独立事件触发。决策在 BattleHandler.handle() 每帧执行。
```

## 8. Action 枚举

```python
class Action(Enum):
    """操作枚举"""
    WAIT = auto()                    # 等待，什么都不做
    SWITCH_AND_CAST = auto()         # 切换精灵 + 释放 comet
    SWITCH = auto()                  # 仅切换精灵
    CAST_DEFENSE = auto()           # 释放防御
    PRESS_ENERGY = auto()            # 聚能
```

## 9. 错误处理

| 场景 | 处理方式 |
|------|----------|
| 切换面板超时未出现 | `switch_to_elf()` 返回 False → 记录日志，继续轮询 |
| 技能图标未找到 | 返回 False → 进入 ERROR 状态 |
| 决策表未匹配（ally_dots 异常） | 日志警告 + WAIT，继续观察 |
| SLOWER 防御期超时 | 超时 → 强制进入 SLOWER_SAC（保险机制） |

## 10. 文件变更

| 文件 | 变更内容 |
|------|----------|
| `src/handlers/battle.py` | 重构 `_faster_loop`、`_slower_loop`，新增决策表、子状态机逻辑 |
| `src/events.py` | 新增 `DOT_INACTIVE_CHANGED` 事件（可选，备用） |
| `src/state_machine.py` | 新增 `SacrificeSubState` 枚举 |

## 11. 测试策略

- **单元测试**：
  - `_faster_decide()` 决策表逻辑验证
  - SLOWER 子状态转换验证
- **集成测试**：
  - 使用真实截图验证精灵切换面板检测
