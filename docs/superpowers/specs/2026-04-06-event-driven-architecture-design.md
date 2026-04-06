# 洛克王国：世界 - 事件驱动架构重构设计

## 概述

将项目从**状态驱动架构**彻底重构为**纯事件驱动架构**，实现高度原子化、可测试、可组合的事件处理系统。

### 架构迁移策略

**这不是增量修改，而是彻底重构。**

| 对比 | 现有架构 | 重构后架构 |
|------|----------|------------|
| 控制流 | `state -> handler -> while循环` | `scan_all() -> event -> handler.handle(ctx)` |
| Handler 接口 | `handle() -> bool` | `handle(ctx: GameContext) -> None` |
| 状态管理 | `dispatcher.state` + `transition()` | `ctx` 存储共享数据 |
| 循环控制 | handler 返回 bool 控制循环 | handler 执行完自动返回检测循环 |

**迁移原则**：
- 新架构独立实现，不依赖旧代码
- Phase 5 之前新旧架构并行运行
- Phase 6 确认新架构稳定后删除旧代码

## 核心理念

- **事件驱动**：所有行为由图像事件触发，而非状态机流转
- **原子化**：每个事件处理器职责单一，不可再分
- **检测与执行分离**：图像检测由 `EventDetector` 统一负责，Handler 只负责执行
- **共享状态通过 Context**：`GameContext` 存储跨事件共享的数据

## 核心组件

### 1. EventDispatcher（主循环）

```python
class EventDispatcher:
    def __init__(
        self,
        controller: GameController,
        elf_manager: ElfManager,
        skill_executor: SkillExecutor,
        config: dict
    ):
        self.controller = controller
        self.elf_manager = elf_manager
        self.skill_executor = skill_executor
        self.context = GameContext()
        self.detector = EventDetector(controller, config)
        self.handlers: dict[Events, Handler] = {}
        self.running = False

    def register_handler(self, event: Events, handler: Handler) -> None:
        self.handlers[event] = handler

    def run(self) -> None:
        while self.running:
            detected = self.detector.scan_all()  # 全量检测
            for event in detected:
                handler = self.handlers.get(event)
                if handler:
                    handler.handle(self.context)  # 操作同步执行，检测暂停

    def stop(self) -> None:
        self.running = False
```

### 2. GameContext（共享状态）

```python
@dataclass
class GameContext:
    # 依赖引用（由 EventDispatcher 注入）
    dispatcher: EventDispatcher

    # 流程控制标记
    slower: bool = False          # SLOWER 流程标记
    sacrifice: bool = False       # SACRIFICE 阶段标记

    # 状态数据
    my_inactive: int = 0          # 我方 inactive dot 数量
    enemy_inactive: int = 0       # 敌方 inactive dot 数量

    # 流程控制方法
    def set_slower(self, value: bool) -> None:
        self.slower = value

    def is_slower(self) -> bool:
        return self.slower

    def set_sacrifice(self, value: bool) -> None:
        self.sacrifice = value

    def is_sacrifice(self) -> bool:
        return self.sacrifice

    # 状态更新方法
    def update_inactive(self, my: int, enemy: int) -> None:
        self.my_inactive = my
        self.enemy_inactive = enemy

    # 便捷属性访问
    @property
    def controller(self) -> GameController:
        return self.dispatcher.controller

    @property
    def elf_manager(self) -> ElfManager:
        return self.dispatcher.elf_manager

    @property
    def skill_executor(self) -> SkillExecutor:
        return self.dispatcher.skill_executor
```

### 3. EventDetector（图像检测引擎）

```python
class EventDetector:
    def __init__(self, controller: GameController, config: dict):
        self.ctrl = controller
        self.event_configs: dict[Events, EventConfig] = self._load_config(config)

    def scan_all(self) -> list[Events]:
        """全量检测所有事件，返回触发的事件列表"""
        detected = []
        for event, cfg in self.event_configs.items():
            if self._match_image(event, cfg):
                detected.append(event)
        return detected

    def _match_image(self, event: Events, cfg: EventConfig) -> bool:
        """检测指定事件对应的图像是否出现"""
        return self.ctrl.find_image(
            template=cfg.template,
            similarity=cfg.similarity,
            x0=cfg.region[0], y0=cfg.region[1],
            x1=cfg.region[2], y1=cfg.region[3]
        ) is not None
```

### 4. EventConfig（事件配置）

```python
@dataclass
class EventConfig:
    template: Union[str, List[str]]  # 模板路径（支持多模板）
    region: tuple[int, int, int, int]  # 检测区域 (x0, y0, x1, y1)
    similarity: float = 0.8     # 相似度阈值
    # 注：空列表 [] 表示动态模板，由 EventDetector._get_template_for_event() 提供
    # 注：template 为 str 时会自动转换为单元素列表

class Events(Enum):
    # 技能相关
    COMET_APPEARED = "comet_appeared"
    DEFENSE_APPEARED = "defense_appeared"

    # 战斗流程
    BATTLE_END = "battle_end"
    START_CHALLENGE = "start_challenge"
    RETRY = "retry"
    CONFIRM = "confirm"

    # 精灵相关
    ENEMY_AVATAR = "enemy_avatar"
    ALLY_AVATAR = "ally_avatar"
    SWITCH_ELF = "switch_elf"

    # 状态检测
    ENEMY_SELF_DESTRUCT = "enemy_self_destruct"
    DOTS_CHANGED = "dots_changed"

    # 速度检测
    SPEED_CHECK = "speed_check"
```

### 5. Handler（事件处理器）

```python
class Handler(ABC):
    def __init__(self, dispatcher: EventDispatcher):
        self.dispatcher = dispatcher

    @property
    def ctrl(self) -> GameController:
        return self.dispatcher.controller

    @property
    def elf_mgr(self) -> ElfManager:
        return self.dispatcher.elf_manager

    @property
    def skill(self) -> SkillExecutor:
        return self.dispatcher.skill_executor

    @abstractmethod
    def handle(self, ctx: GameContext) -> None:
        """处理事件，无返回值"""
        pass

# 事件注册装饰器
def event_handler(
    event: Events,
    template: Union[str, List[str]],
    region: tuple[int, int, int, int],
    similarity: float = 0.8
):
    def decorator(cls: type[Handler]):
        EventRegistry.register(event, cls, template, region, similarity)
        return cls
    return decorator
```

## 事件定义

### 技能事件

| 事件 | 模板 | 区域 | 说明 |
|------|------|------|------|
| COMET_APPEARED | skills/comet.png | 全屏 | 彗星技能可用 |
| DEFENSE_APPEARED | skills/defense.png | 全屏 | 防御技能可用 |

### 流程事件

| 事件 | 模板 | 区域 | 说明 |
|------|------|------|------|
| START_CHALLENGE | battle/start_challenge.png | 战斗区域 | 开始挑战按钮 |
| BATTLE_END | battle/battle_end.png | 全屏 | 战斗结束界面 |
| RETRY | battle/retry.png | 全屏 | 再次切磋按钮 |
| CONFIRM | popup/confirm.png | 全屏 | 确认按钮 |

### 精灵事件

| 事件 | 模板 | 区域 | 说明 |
|------|------|------|------|
| SWITCH_ELF | 从配置获取（单模板或多模板） | ALLY_REGION | 我方精灵头像（用于切换） |
| ENEMY_AVATAR | 从 elf_manager 动态获取 | ENEMY_REGION | 敌方精灵头像 |

### 状态检测事件

| 事件 | 模板 | 区域 | 说明 |
|------|------|------|------|
| ENEMY_SELF_DESTRUCT | 从 elf_manager 动态获取 | ENEMY_REGION | 敌方自爆流检测 |
| DOTS_CHANGED | 从配置获取 | 战斗区域 | dot 状态变化 |
| SPEED_CHECK | 从配置获取 | 战斗区域 | 速度检测（持续检测） |

### 动态模板说明

某些事件的模板需要动态获取，不在配置中静态指定：

- **ENEMY_AVATAR / ENEMY_SELF_DESTRUCT**：从 `elf_manager.get_selfdestruct_templates()` 获取
- **SWITCH_ELF**：从 `elf_manager` 获取当前角色的所有精灵模板

这些事件在 `EventDetector` 中需要特殊处理：
```python
def _get_template_for_event(self, event: Events) -> Union[str, List[str]]:
    if event == Events.ENEMY_SELF_DESTRUCT:
        return self.ctrl.elf_manager.get_selfdestruct_templates()
    elif event == Events.SWITCH_ELF:
        return self.ctrl.elf_manager.get_switch_templates()
    return self.event_configs[event].template
```

## 处理器示例

### CometAppearedHandler

```python
@event_handler(
    Events.COMET_APPEARED,
    template="skills/comet.png",
    region=(0, 0, 2560, 1440),
    similarity=0.8
)
class CometAppearedHandler(Handler):
    def handle(self, ctx: GameContext) -> None:
        # 根据 context 状态决定行为
        if ctx.is_slower() and ctx.my_inactive == 0 and ctx.enemy_inactive == 1:
            ctx.set_sacrifice(True)

        if ctx.is_sacrifice():
            self.skill.cast_comet()
        else:
            self.skill.cast_comet()
```

### EnemySelfDestructHandler

```python
class EnemySelfDestructHandler(Handler):
    def handle(self, ctx: GameContext) -> None:
        # 发现敌方自爆流则逃跑
        self.skill.escape_battle()
        self.dispatcher.stop()
```

### SpeedCheckHandler

```python
class SpeedCheckHandler(Handler):
    def handle(self, ctx: GameContext) -> None:
        # 每次 DOTS_CHANGED 触发时更新 inactive 数量
        # 这些数据由 dots_changed.py 中的检测逻辑填充到 ctx
        my_dots = self.ctrl.find_images_all("dots/dot_active.png", region=ALLY_REGION)
        enemy_inactive = self.ctrl.find_images_all("dots/dot_inactive.png", region=ENEMY_REGION)

        ctx.update_inactive(len(my_dots), len(enemy_inactive))

        # 判断速度优势并设置 ctx.slower
        # 如果我方已有 inactive 且敌方无 inactive，说明敌方更快
        if ctx.my_inactive > 0 and ctx.enemy_inactive == 0:
            ctx.set_slower(True)
        elif ctx.enemy_inactive > 0 and ctx.my_inactive == 0:
            ctx.set_slower(False)
```

### SwitchElfHandler

```python
class SwitchElfHandler(Handler):
    def handle(self, ctx: GameContext) -> None:
        if ctx.is_sacrifice():
            # 执行送死精灵切换
            self.ctrl.find_and_click(elf_mgr.get_sacrifice_template())
        elif ctx.is_slower() and ctx.my_inactive == 0:
            # SLOWER 流程：切换 reserve 精灵
            self.ctrl.find_and_click(elf_mgr.get_reserve_template())
```

## EventRegistry 与 EventDetector 协作流程

### 初始化流程

```
┌──────────────────────────────────────────────────────────────┐
│                        main.py                                │
│                                                              │
│  1. 创建 EventDispatcher                                    │
│  2. 调用 EventRegistry.get_configs() 获取所有事件配置        │
│  3. 创建 EventDetector(event_configs)                        │
│  4. 遍历所有 Handler 类，通过装饰器注册到 EventRegistry      │
│  5. 每个 Handler 实例注册到 EventDispatcher.handlers        │
└──────────────────────────────────────────────────────────────┘
```

### 注册机制

```python
# registry.py
class EventRegistry:
    _handlers: dict[Events, type[Handler]] = {}
    _configs: dict[Events, EventConfig] = {}

    @classmethod
    def register(
        cls,
        event: Events,
        handler_cls: type[Handler],
        template: Union[str, List[str]],
        region: tuple[int, int, int, int],
        similarity: float
    ):
        cls._handlers[event] = handler_cls
        cls._configs[event] = EventConfig(template, region, similarity)

    @classmethod
    def get_handlers(cls) -> dict[Events, type[Handler]]:
        return cls._handlers.copy()

    @classmethod
    def get_configs(cls) -> dict[Events, EventConfig]:
        return cls._configs.copy()
```

### 检测与处理流程

```
┌──────────────────────────────────────────────────────────────┐
│                    EventDispatcher.run()                      │
│                                                              │
│  while running:                                              │
│    ┌──────────────────────────────────────────────────────┐  │
│    │  EventDetector.scan_all()                            │  │
│    │    - 遍历所有 EventConfig                            │  │
│    │    - 调用 controller.find_image() 检测图像           │  │
│    │    - 返回触发的事件列表 [Event1, Event2, ...]        │  │
│    └──────────────────────────────────────────────────────┘  │
│                           │                                   │
│                           ▼                                   │
│    ┌──────────────────────────────────────────────────────┐  │
│    │  for event in detected:                              │  │
│    │    handler = handlers[event]                        │  │
│    │    handler.handle(ctx)  # 操作同步执行                │  │
│    └──────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

## 目录结构

```
src/
├── __init__.py
├── main.py                    # 程序入口
├── event_dispatcher.py        # 主循环（重构）
├── context.py                 # GameContext（新增）
├── detector.py                # EventDetector（新增）
├── registry.py                # EventRegistry（新增）
├── events.py                  # Events 枚举（重构）
├── handlers/
│   ├── __init__.py
│   ├── base_handler.py        # Handler 基类（重构）
│   ├── comet.py               # COMET_APPEARED 处理器
│   ├── defense.py             # DEFENSE_APPEARED 处理器
│   ├── battle_end.py          # BATTLE_END 处理器
│   ├── start_challenge.py     # START_CHALLENGE 处理器
│   ├── confirm.py             # CONFIRM 处理器
│   ├── enemy_avatar.py        # ENEMY_AVATAR 处理器
│   ├── switch_elf.py          # SWITCH_ELF 处理器
│   ├── dots_changed.py        # DOTS_CHANGED 处理器
│   ├── speed_check.py         # SPEED_CHECK 处理器
│   ├── enemy_self_destruct.py # ENEMY_SELF_DESTRUCT 处理器
│   └── retry.py               # RETRY 处理器
├── controller.py              # 游戏控制器
├── elf_manager.py              # 精灵管理器
├── skill_executor.py           # 技能执行器
├── state_machine.py           # 保留（仅用于类型引用）
└── exceptions.py
```

## 配置结构（settings.json）

```json
{
  "events": {
    "comet_appeared": {
      "template": "skills/comet.png",
      "region": [0, 0, 2560, 1440],
      "similarity": 0.8
    },
    "defense_appeared": {
      "template": "skills/defense.png",
      "region": [0, 0, 2560, 1440],
      "similarity": 0.8
    },
    "battle_end": {
      "template": "battle/battle_end.png",
      "region": [0, 0, 2560, 1440],
      "similarity": 0.8
    },
    "start_challenge": {
      "template": "battle/start_challenge.png",
      "region": [0, 0, 2560, 1440],
      "similarity": 0.8
    },
    "retry": {
      "template": "battle/retry.png",
      "region": [0, 0, 2560, 1440],
      "similarity": 0.8
    },
    "confirm": {
      "template": "popup/confirm.png",
      "region": [0, 0, 2560, 1440],
      "similarity": 0.8
    },
    "switch_elf": {
      "template": ["elves/tree3.png", "elves/otter2.png", "elves/pig3.png", "elves/scepter3.png"],
      "region": [0, 0, 700, 320],
      "similarity": 0.7
    },
    "dots_changed": {
      "template": ["dots/dot_active.png", "dots/dot_inactive.png"],
      "region": [0, 0, 2560, 1440],
      "similarity": 0.8
    }
  },
  "enemy_region": [2000, 0, 2560, 320],
  "ally_region": [0, 0, 700, 320],
  "enemy_self_destruct_region": [2000, 0, 2560, 320],
  "similarity": 0.8
}
```

## 检测循环流程

```
┌─────────────────────────────────────────┐
│           EventDispatcher.run()          │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │    while running:                 │   │
│  │      detected = scan_all()       │   │
│  │      for event in detected:       │   │
│  │        handler.handle(ctx)        │   │
│  │        # 操作同步执行              │   │
│  │        # 检测暂停                  │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

### 持续检测状态

某些状态需要持续检测（如 SPEED_CHECK），通过多次循环实现：

```python
class SpeedCheckHandler(Handler):
    def handle(self, ctx: GameContext) -> None:
        # 每触发一次 DOTS_CHANGED 事件，更新 context
        # 持续检测直到满足条件才退出
        my_dots = self.ctrl.find_images_all("dots/dot_active.png", region=ALLY_REGION)
        enemy_dots = self.ctrl.find_images_all("dots/dot_inactive.png", region=ENEMY_REGION)

        ctx.update_inactive(len(my_dots), len(enemy_dots))

        # 判断速度：敌方先出现 inactive 则我方 faster
        if ctx.enemy_inactive > 0 and ctx.my_inactive == 0:
            ctx.set_slower(False)  # 我方更快
        elif ctx.my_inactive > 0:
            ctx.set_slower(True)   # 敌方更快
```

## 错误处理

- **图像未找到**：正常情况，跳过继续检测
- **图像检测异常**：记录日志，停止脚本
- **处理器执行异常**：
  - 记录日志，包含异常堆栈
  - 设置 `dispatcher.running = False`
  - 可选：触发 ERROR 事件进行恢复

## 实施步骤（分阶段）

### Phase 1: 核心基础设施

1. 创建 `context.py` - GameContext 类
2. 创建 `detector.py` - EventDetector 类
3. 创建 `registry.py` - EventRegistry 类
4. 重构 `events.py` - 补充事件枚举

### Phase 2: 基础 Handler

5. 创建 `handlers/base_handler.py` - Handler 基类
6. 创建简单事件处理器：
   - `comet.py`
   - `defense.py`
   - `start_challenge.py`
   - `confirm.py`
   - `battle_end.py`
   - `retry.py`

### Phase 3: 精灵相关 Handler

7. 创建精灵相关处理器：
   - `enemy_avatar.py`
   - `switch_elf.py`
   - `enemy_self_destruct.py`

### Phase 4: 状态检测 Handler

8. 创建状态检测处理器：
   - `dots_changed.py`
   - `speed_check.py`

### Phase 5: 主循环重构

9. 重构 `event_dispatcher.py` - 主循环
10. 更新 `main.py` - 初始化新架构
11. 更新 `handlers/__init__.py` - 注册所有 Handler

### Phase 6: 清理

**前提：确认新架构稳定运行至少 N 轮战斗**

12. 迁移 `state_machine.py` 中的枚举到 `events.py`
    - `BattleState` → 确认无引用后删除
    - `SacrificeSubState` → 已不需要，删除
13. 删除 `battle_flow.py`（如果存在）
14. 删除旧的 `handlers/battle.py`
15. 删除旧的 `handlers/base_handler.py`（如有冲突）
16. 更新 `main.py`，移除旧架构初始化代码
17. 更新测试适配新架构
18. 更新文档

**删除前的验证清单**：
- [ ] 新架构运行 10+ 轮战斗无异常
- [ ] 所有事件处理器正常工作
- [ ] `state_machine.py` 无任何导入引用

## 注意事项

- 所有代码使用类型提示
- 事件处理器原子化，一个事件一个类
- Context 使用具体方法（set_slower/get_slower）而非通用 set/get
- 检测循环在操作执行时暂停，操作同步完成
- 不需要事件优先级，多个事件按自然顺序处理
- Handler 通过 EventDispatcher 注入依赖，而非直接注入
- template 支持单字符串或字符串数组
