# 闪耀大赛自动化脚本 - 设计分析文档

> 生成日期：2026-04-11
> 更新日期：2026-04-11（根据第一轮评审修正）
> 分析方法：第一性原理 + 代码审查

---

## 1. 项目概述

洛克王国闪耀大赛自动化脚本，通过图像识别实现游戏战斗自动化。

### 1.1 技术架构

```
main.py → EventDispatcher 主循环
           ├── EventDetector 图像检测（每轮单截图）
           ├── GameContext 共享状态
           └── Handlers 事件处理器（自注册）
```

**核心循环**：
```python
while running:
    controller.capture()        # 每轮只截一次图
    detected = detector.scan_all()  # 检测所有12种事件
    for event in detected:
        handler.handle(ctx, pos)   # 分发处理
```

### 1.2 核心组件

| 组件 | 路径 | 职责 |
|------|------|------|
| EventDispatcher | src/event_dispatcher.py | 主循环协调 |
| EventDetector | src/detector.py | 图像检测引擎 |
| GameContext | src/context.py | 共享状态存储 |
| ElfManager | src/elf_manager.py | 精灵配置管理 |
| SkillExecutor | src/skill_executor.py | 技能执行 |
| EventRegistry | src/registry.py | 事件自注册表 |

---

## 2. 战斗流程详解

### 2.1 进入战斗

```
检测 start_challenge.png → 点击"开始挑战"
       ↓
检测 insufficient.png → 精灵不足弹窗（需处理）
       ↓
检测 confirm_lineups.png → 选择首发精灵（final）
       ↓
检测 confirm.png → 确认选择
       ↓
等待战斗开始...
```

### 2.2 速度判断机制

通过 **inactive dot** 数量判断谁先行动。**游戏内没有速度条、没有死亡动画可检测**，唯一可判断的就是这个圆点。

| 情况 | 判定 | 流程 |
|------|------|------|
| 我方有 inactive dot 且敌方无 | 敌方更快 | SLOWER |
| 敌方有 inactive dot 且我方无 | 我方更快 | FASTER |

**代码位置**：`src/handlers/dots_changed.py`

```python
# 基于 inactive dot 数量判断速度优势
if ctx.my_inactive > 0 and ctx.enemy_inactive == 0:
    ctx.set_slower(True)   # 敌方更快
elif ctx.enemy_inactive > 0 and ctx.my_inactive == 0:
    ctx.set_slower(False)  # 我方更快
```

### 2.3 送死顺序策略

| 速度 | 送死顺序 |
|------|----------|
| 我方更快 (FASTER) | final → sacrifice → sacrifice → reserve |
| 敌方更快 (SLOWER) | reserve → sacrifice → sacrifice → final |

**设计目的**：最终用 reserve 收割，需要保证 reserve 是满血

### 2.4 技能策略

**彗星技能**（攻击）：**死够3个就不打**，不是检测存活数，而是检测死亡数。

| 流程 | 条件 | 行为 |
|------|------|------|
| SLOWER | 敌方 inactive < 3 | 打彗星 |
| SLOWER | 敌方 inactive >= 3 | 不打（敌方死够3个） |
| FASTER | 我方 inactive >= 3 | 不打 |
| FASTER | 我方 inactive < 3 | 打彗星 |

**防御技能**：

| 流程 | 条件 | 行为 |
|------|------|------|
| SLOWER | 敌方 inactive >= 3 | 不打 |
| SLOWER | 敌方 inactive < 3 | 打防御 |
| FASTER | 我方 inactive < 3 | 打防御 |
| FASTER | 我方 inactive >= 3 | 不打 |

### 2.5 切换精灵逻辑

**SLOWER 流程**：
- 敌方 inactive >= 3 时切换
- 优先切换到 reserve，失败则切换到 sacrifice

**FASTER 流程**：
- 我方 inactive < 3 时切换到 sacrifice
- 我方 inactive >= 3 时切换到 reserve

---

## 3. 事件系统

### 3.1 事件驱动设计的理由

当前事件驱动设计是**有意为之**，目的是防止时序依赖导致链路崩塌：
- 如果前置条件因为识图问题检测失败，后续流程就无法执行
- 轮询设计让每个事件都能独立检测，不依赖上一个事件的结果

`DOTS_CHANGED` 和 `SWITCH_ELF` 的检测区域**不是全屏**，而是限定了区域，避免误触发。

### 3.2 12 种事件

| 事件 | 触发条件 | Handler |
|------|----------|---------|
| COMET_APPEARED | 检测到彗星技能图标 | CometAppearedHandler |
| DEFENSE_APPEARED | 检测到防御技能图标 | DefenseAppearedHandler |
| BATTLE_END | 检测到战斗结束 | BattleEndHandler |
| START_CHALLENGE | 检测到开始挑战按钮 | StartChallengeHandler |
| CONFIRM_LINEUPS | 检测到阵容确认界面 | SelectFirstElfHandler |
| RETRY | 检测到再次切磋按钮 | RetryHandler |
| CONFIRM | 检测到确认按钮 | ConfirmHandler |
| ENEMY_AVATAR | 检测到敌方精灵头像 | EnemyAvatarHandler |
| ALLY_AVATAR | 检测到我方精灵头像 | (未实现) |
| SWITCH_ELF | 检测到切换精灵面板 | SwitchElfHandler |
| ENEMY_SELF_DESTRUCT | 检测到自爆流敌方 | (半成品) |
| DOTS_CHANGED | 检测到 dot 变化 | DotsChangedHandler |

### 3.3 自注册机制

Handlers 通过 `EventRegistry.register()` 自注册：

```python
# src/handlers/comet.py
EventRegistry.register(
    event=Events.COMET_APPEARED,
    handler_cls=CometAppearedHandler,
    template="skills/comet.png",
    region=(0, 0, 2560, 1440),
    similarity=0.8
)
```

`import src.handlers` 时自动触发所有 Handler 的注册。

---

## 4. 第一性原理分析：问题与改进点

### 4.1 核心问题 1：速度判断基于唯一可用信号

**当前逻辑**：
```python
if ctx.my_inactive > 0 and ctx.enemy_inactive == 0:
    ctx.set_slower(True)
elif ctx.enemy_inactive > 0 and ctx.my_inactive == 0:
    ctx.set_slower(False)
```

**说明**：游戏内没有速度条、没有死亡动画，唯一可判断的就是 inactive dot。这是基于游戏机制的事实选择，不是假设。

**风险**：
- 一旦判断错误，整个送死顺序和技能策略都会错
- **没有回退机制**：如果中途发现判断错误，无法修正

**改进方向**：
1. 增加**多重验证**：结合双方精灵死亡时序交叉验证
2. 增加**回退机制**：如果检测到异常的死亡顺序，触发重新评估

---

### 4.2 核心问题 2：事件驱动设计是防止时序依赖崩塌的刻意选择

**当前设计**：
- 每轮检测所有12种事件
- 事件检测**限定区域**（不是全屏），避免误触发
- DOTS_CHANGED 和 SWITCH_ELF 都有独立的区域限制

**这不是缺陷，而是设计意图**：防止前置条件检测失败导致后续流程无法执行。

---

### 4.3 核心问题 3：技能策略基于死亡数量，不是存活数量

**当前逻辑**：
```python
if ctx.enemy_inactive < 3:
    return  # 死够3个就不打彗星
```

**这是正确的设计**：统计的是死亡数（inactive dot），不是存活数。死够3个意味着敌方快死光了，不需要再浪费技能。

---

### 4.4 核心问题 4：切换精灵面板检测依赖精灵头像

**当前逻辑**：
```python
# wait_for_switch_panel 通过检测 x < 600 的精灵头像判断面板打开
pos = self.ctrl.find_image(elf_template, similarity=0.8)
if pos != (-1, -1) and pos[0] < 600:
    return True
```

**现状**：
- 游戏没有明确的"选择精灵"标识可用
- 只能通过精灵头像出现在左侧区域（x < 600）判断面板打开
- `SkillExecutor.wait_for_switch_panel()` 被 `switch_to_elf()` 调用，但该方法代码在 `switch_to_elf` 流程中似乎是**弃用的**

**改进建议**：
1. 确认 `SkillExecutor.switch_to_elf()` 是否还在使用，如果弃用则移除
2. 增加切换失败的**重试逻辑**

---

### 4.5 核心问题 5：没有超时和异常恢复机制

**当前问题**：
- `controller.find_image_with_timeout` 有超时，但 handler 层面没有
- 如果某个 handler 处理卡住，整个主循环会阻塞
- 战斗异常（如敌方使用特殊技能）没有处理

**改进建议**：
```python
# 给每个 handler 处理增加超时
def handle_with_timeout(self, ctx, position, timeout=5):
    try:
        return asyncio.wait_for(self.handle(ctx, position), timeout)
    except asyncio.TimeoutError:
        logger.error(f"{self.__class__.__name__} 处理超时")
        # 触发异常恢复流程
```

**状态**：暂不改

---

### 4.6 核心问题 6：自爆流检测是"半成品"

**elves.json**：
```json
"selfdestruct_enemies": [
    "elves/butterfly_3.png",  // 蝴蝶是自爆精灵
    ...
]
```

**但 handler 代码**：
```python
class EnemySelfDestructHandler(Handler):
    def handle(self, ctx: GameContext, position=None) -> None:
        pass  # 只检测，不处理
```

**问题**：检测到自爆流敌方但不处理，实际没有用

**改进建议**：
- 检测到自爆流时，切换到特定策略（如优先击杀自爆精灵）
- 或检测到自爆流时，直接逃跑（不值得打）

**状态**：暂不改

---

### 4.7 核心问题 7：12个事件没有优先级

**当前设计**：
```python
for detected_event in detected:
    handler = self.handlers.get(detected_event.event)
    if handler:
        handler.handle(ctx, detected_event.position)
```

**问题**：
- 如果同时检测到多个事件，按遍历顺序处理
- 但有些事件需要优先处理（如 `BATTLE_END` > `SWITCH_ELF`）
- 没有**事件冲突解决**机制

**改进建议**：
```python
# 事件优先级
EVENT_PRIORITY = {
    Events.BATTLE_END: 100,      # 最高
    Events.RETRY: 90,
    Events.SWITCH_ELF: 50,
    Events.COMET_APPEARED: 30,
    Events.DOTS_CHANGED: 10,    # 最低
}

# 按优先级排序处理
detected.sort(key=lambda e: EVENT_PRIORITY.get(e.event, 0), reverse=True)
```

**状态**：暂不改

---

### 4.8 核心问题 8：配置和代码耦合

**问题**：
- `elves.json` 中 `role: "final/sacrifice/reserve"` 是语义角色
- 但代码中 `get_sacrifice_order()` 直接按这个顺序执行
- 如果需要临时调整顺序，必须改代码

**改进建议**：
```json
{
  "elves": [...],
  "strategy": {
    "faster_order": ["final", "sacrifice1", "sacrifice2", "reserve"],
    "slower_order": ["reserve", "sacrifice1", "sacrifice2", "final"]
  }
}
```

---

## 5. 已修复问题

### 5.1 inactive_dot 识别不准确

**问题现象**：
- inactive dot 识别不到，一直是 0
- 单测中能正常识别，实际运行识别不到

**根本原因**：
`win_util/image.py` 中 `ScreenCapture.capture_window_region()` 有硬编码的偏移量 `+8` 和 `+31`，但全屏游戏窗口不需要这个偏移，导致截图区域错位，dot 位置匹配失败。

**修复方案**：
修改 `win_util/image.py`，去掉 `+8` 和 `+31` 的偏移计算。

---

## 6. 改进优先级

| 优先级 | 问题 | 影响 | 改进难度 | 状态 |
|--------|------|------|----------|------|
| **高** | inactive_dot 识别不准确 | 速度判断失效 | 已修复 | 已解决 |
| **高** | 速度判断无回退机制 | 判断错误无法修正 | 中 | 待处理 |
| **中** | 切换精灵面板检测脆弱 | 切换可能失败 | 低 | 待处理 |
| **中** | switch_to_elf 弃用代码未清理 | 代码冗余 | 低 | 待处理 |
| **低** | 4.5 无异常恢复机制 | 卡住需手动干预 | 中 | 暂不改 |
| **低** | 4.6 自爆流检测不处理 | 特殊对局无法应对 | 低 | 暂不改 |
| **低** | 4.7 事件无优先级 | 时序可能混乱 | 低 | 暂不改 |

---

## 7. 架构建议：状态机 vs 事件驱动

**当前系统是"事件驱动"**，对于闪耀大赛这种**流程相对固定**的战斗，**状态机驱动**可能更合适：

```
WAITING → ENTERING → SPEED_CHECK → SACRIFICE → CLEANUP → BATTLE_END
```

**事件驱动优点**：
- 响应性好，实时响应游戏状态变化
- 适合开放式的游戏环境

**状态机优点**：
- 流程清晰，每个阶段有明确的进入/退出条件
- 易于调试和测试
- 容易添加异常处理

**建议**：混合架构
- 外层：状态机控制战斗阶段
- 内层：事件驱动处理各阶段内的实时响应

---

## 8. 待验证问题

1. **inactive dot 出现顺序 = 速度顺序？** 游戏机制确认：目前认为是正确的
2. **敌方精灵数量**：当前假设敌方也是4个精灵，实际可能不同
3. **技能等待时间**：10秒是否足够？reserve 精灵的 switch_sleep=10 是否最优
4. **相似度阈值**：0.7/0.8 在不同光照下的可靠性
5. **offset 修复后 dot 识别效果**：需实际运行验证

---

*文档结束*
