# 事件驱动架构重构实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将洛克王国：世界项目从状态驱动架构重构为纯事件驱动架构，实现高度原子化、可测试的事件处理系统。

**Architecture:** 核心组件包括 EventDispatcher（主循环）、EventDetector（图像检测引擎）、GameContext（共享状态）、EventRegistry（事件注册）。检测与执行分离，Handler 只负责执行，检测由 EventDetector 统一负责。

**Tech Stack:** Python 3.11+, dataclass, Enum, ABC, win_util

---

## 文件结构

```
src/
├── context.py                 # GameContext（新增）
├── detector.py                # EventDetector（新增）
├── registry.py                # EventRegistry（新增）
├── events.py                  # Events 枚举（重构）
├── event_dispatcher.py        # 主循环（重构）
├── handlers/
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
tests/unit/
├── test_context.py           # GameContext 单元测试
├── test_detector.py          # EventDetector 单元测试
├── test_registry.py          # EventRegistry 单元测试
└── test_handlers/            # Handler 单元测试
    ├── test_comet.py
    ├── test_defense.py
    └── ...
```

---

## Phase 1: 核心基础设施

### Task 1: 创建 Events 枚举

**Files:**
- Create: `src/events.py`
- Modify: `src/__init__.py`
- Test: `tests/unit/test_events.py`

- [ ] **Step 1: 创建 tests/unit/test_events.py**

```python
import pytest
from src.events import Events

def test_events_enum_values():
    """验证 Events 枚举值正确"""
    assert Events.COMET_APPEARED.value == "comet_appeared"
    assert Events.DEFENSE_APPEARED.value == "defense_appeared"
    assert Events.BATTLE_END.value == "battle_end"
    assert Events.START_CHALLENGE.value == "start_challenge"
    assert Events.RETRY.value == "retry"
    assert Events.CONFIRM.value == "confirm"
    assert Events.ENEMY_AVATAR.value == "enemy_avatar"
    assert Events.ALLY_AVATAR.value == "ally_avatar"
    assert Events.SWITCH_ELF.value == "switch_elf"
    assert Events.ENEMY_SELF_DESTRUCT.value == "enemy_self_destruct"
    assert Events.DOTS_CHANGED.value == "dots_changed"
    assert Events.SPEED_CHECK.value == "speed_check"

def test_events_count():
    """验证事件数量"""
    assert len(Events) == 13
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/unit/test_events.py -v`
Expected: FAIL - ModuleNotFoundError: No module named 'src.events'

- [ ] **Step 3: 创建 src/events.py**

```python
from enum import Enum
from typing import Union, List


class Events(Enum):
    """事件枚举"""
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

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/unit/test_events.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/events.py tests/unit/test_events.py
git commit -m "feat(events): 添加 Events 枚举定义

- 技能相关: COMET_APPEARED, DEFENSE_APPEARED
- 战斗流程: BATTLE_END, START_CHALLENGE, RETRY, CONFIRM
- 精灵相关: ENEMY_AVATAR, ALLY_AVATAR, SWITCH_ELF
- 状态检测: ENEMY_SELF_DESTRUCT, DOTS_CHANGED, SPEED_CHECK

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 2: 创建 EventConfig 数据类

**Files:**
- Create: `src/event_config.py`
- Modify: `src/events.py`
- Test: `tests/unit/test_event_config.py`

- [ ] **Step 1: 创建 tests/unit/test_event_config.py**

```python
import pytest
from dataclasses import dataclass
from typing import Union, List
from src.events import Events


@dataclass
class EventConfig:
    """事件配置数据类"""
    template: Union[str, List[str]]
    region: tuple[int, int, int, int]
    similarity: float = 0.8


def test_event_config_creation():
    """验证 EventConfig 创建"""
    config = EventConfig(
        template="skills/comet.png",
        region=(0, 0, 2560, 1440),
        similarity=0.8
    )
    assert config.template == "skills/comet.png"
    assert config.region == (0, 0, 2560, 1440)
    assert config.similarity == 0.8

def test_event_config_list_template():
    """验证 EventConfig 支持列表模板"""
    config = EventConfig(
        template=["elves/tree3.png", "elves/otter2.png"],
        region=(0, 0, 700, 320),
        similarity=0.7
    )
    assert isinstance(config.template, list)
    assert len(config.template) == 2
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/unit/test_event_config.py -v`
Expected: FAIL - ModuleNotFoundError

- [ ] **Step 3: 创建 src/event_config.py**

```python
from dataclasses import dataclass
from typing import Union, List


@dataclass
class EventConfig:
    """事件配置数据类

    Args:
        template: 模板路径（支持单字符串或字符串列表）
        region: 检测区域 (x0, y0, x1, y1)
        similarity: 相似度阈值
    """
    template: Union[str, List[str]]
    region: tuple[int, int, int, int]
    similarity: float = 0.8
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/unit/test_event_config.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/event_config.py tests/unit/test_event_config.py
git commit -m "feat(config): 添加 EventConfig 数据类

- 支持 template 为单字符串或字符串列表
- 包含 region 和 similarity 配置

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 3: 创建 EventRegistry

**Files:**
- Create: `src/registry.py`
- Test: `tests/unit/test_registry.py`

- [ ] **Step 1: 创建 tests/unit/test_registry.py**

```python
import pytest
from src.events import Events
from src.event_config import EventConfig


class MockHandler:
    """模拟 Handler 用于测试"""
    pass


def test_registry_register():
    """验证事件注册"""
    from src.registry import EventRegistry

    EventRegistry._handlers.clear()
    EventRegistry._configs.clear()

    EventRegistry.register(
        event=Events.COMET_APPEARED,
        handler_cls=MockHandler,
        template="skills/comet.png",
        region=(0, 0, 2560, 1440),
        similarity=0.8
    )

    assert Events.COMET_APPEARED in EventRegistry._handlers
    assert Events.COMET_APPEARED in EventRegistry._configs
    assert EventRegistry._handlers[Events.COMET_APPEARED] == MockHandler

def test_registry_get_handlers():
    """验证获取所有处理器"""
    from src.registry import EventRegistry

    EventRegistry._handlers.clear()
    EventRegistry._configs.clear()

    EventRegistry.register(Events.COMET_APPEARED, MockHandler, "a.png", (0,0,1,1), 0.8)
    EventRegistry.register(Events.DEFENSE_APPEARED, MockHandler, "b.png", (0,0,1,1), 0.8)

    handlers = EventRegistry.get_handlers()
    assert len(handlers) == 2
    assert Events.COMET_APPEARED in handlers
    assert Events.DEFENSE_APPEARED in handlers

def test_registry_get_configs():
    """验证获取所有配置"""
    from src.registry import EventRegistry

    EventRegistry._handlers.clear()
    EventRegistry._configs.clear()

    EventRegistry.register(Events.COMET_APPEARED, MockHandler, "a.png", (0,0,1,1), 0.8)

    configs = EventRegistry.get_configs()
    assert Events.COMET_APPEARED in configs
    assert isinstance(configs[Events.COMET_APPEARED], EventConfig)
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/unit/test_registry.py -v`
Expected: FAIL - ModuleNotFoundError

- [ ] **Step 3: 创建 src/registry.py**

```python
from typing import Union, List, Dict, Type
from src.events import Events
from src.event_config import EventConfig


class EventRegistry:
    """事件注册表

    负责管理事件与处理器、配置的映射关系。
    使用类方法进行全局注册。
    """
    _handlers: Dict[Events, Type["Handler"]] = {}
    _configs: Dict[Events, EventConfig] = {}

    @classmethod
    def register(
        cls,
        event: Events,
        handler_cls: Type["Handler"],
        template: Union[str, List[str]],
        region: tuple[int, int, int, int],
        similarity: float = 0.8
    ) -> None:
        """注册事件处理器和配置

        Args:
            event: 事件枚举
            handler_cls: 处理器类
            template: 模板路径
            region: 检测区域
            similarity: 相似度阈值
        """
        cls._handlers[event] = handler_cls
        cls._configs[event] = EventConfig(template, region, similarity)

    @classmethod
    def get_handlers(cls) -> Dict[Events, Type["Handler"]]:
        """获取所有已注册处理器"""
        return cls._handlers.copy()

    @classmethod
    def get_configs(cls) -> Dict[Events, EventConfig]:
        """获取所有已注册配置"""
        return cls._configs.copy()

    @classmethod
    def clear(cls) -> None:
        """清空注册表（用于测试）"""
        cls._handlers.clear()
        cls._configs.clear()
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/unit/test_registry.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/registry.py tests/unit/test_registry.py
git commit -m "feat(registry): 添加 EventRegistry 事件注册表

- 提供 register/get_handlers/get_configs 方法
- 支持类方法全局注册

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 4: 创建 GameContext

**Files:**
- Create: `src/context.py`
- Test: `tests/unit/test_context.py`

- [ ] **Step 1: 创建 tests/unit/test_context.py**

```python
import pytest
from dataclasses import dataclass
from typing import Optional


@dataclass
class MockDispatcher:
    """模拟 EventDispatcher 用于测试"""
    controller = None
    elf_manager = None
    skill_executor = None


class TestGameContext:
    """GameContext 单元测试"""

    def test_set_slower_and_is_slower(self):
        """验证 slower 状态设置和获取"""
        from src.context import GameContext

        ctx = GameContext(dispatcher=MockDispatcher())
        assert ctx.slower == False

        ctx.set_slower(True)
        assert ctx.slower == True
        assert ctx.is_slower() == True

        ctx.set_slower(False)
        assert ctx.slower == False

    def test_set_sacrifice_and_is_sacrifice(self):
        """验证 sacrifice 状态设置和获取"""
        from src.context import GameContext

        ctx = GameContext(dispatcher=MockDispatcher())
        assert ctx.sacrifice == False

        ctx.set_sacrifice(True)
        assert ctx.sacrifice == True
        assert ctx.is_sacrifice() == True

    def test_update_inactive(self):
        """验证 inactive 数量更新"""
        from src.context import GameContext

        ctx = GameContext(dispatcher=MockDispatcher())
        ctx.update_inactive(my=2, enemy=1)

        assert ctx.my_inactive == 2
        assert ctx.enemy_inactive == 1

    def test_default_values(self):
        """验证默认值"""
        from src.context import GameContext

        ctx = GameContext(dispatcher=MockDispatcher())

        assert ctx.slower == False
        assert ctx.sacrifice == False
        assert ctx.my_inactive == 0
        assert ctx.enemy_inactive == 0
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/unit/test_context.py -v`
Expected: FAIL - ModuleNotFoundError

- [ ] **Step 3: 创建 src/context.py**

```python
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.event_dispatcher import EventDispatcher


@dataclass
class GameContext:
    """游戏共享状态上下文

    存储跨事件共享的数据，供各 Handler 读写。
    通过 EventDispatcher 注入依赖引用。

    Attributes:
        dispatcher: EventDispatcher 引用
        slower: SLOWER 流程标记
        sacrifice: SACRIFICE 阶段标记
        my_inactive: 我方 inactive dot 数量
        enemy_inactive: 敌方 inactive dot 数量
    """
    dispatcher: "EventDispatcher"
    slower: bool = False
    sacrifice: bool = False
    my_inactive: int = 0
    enemy_inactive: int = 0

    def set_slower(self, value: bool) -> None:
        """设置 SLOWER 流程标记"""
        self.slower = value

    def is_slower(self) -> bool:
        """获取 SLOWER 流程标记"""
        return self.slower

    def set_sacrifice(self, value: bool) -> None:
        """设置 SACRIFICE 阶段标记"""
        self.sacrifice = value

    def is_sacrifice(self) -> bool:
        """获取 SACRIFICE 阶段标记"""
        return self.sacrifice

    def update_inactive(self, my: int, enemy: int) -> None:
        """更新 inactive dot 数量"""
        self.my_inactive = my
        self.enemy_inactive = enemy

    @property
    def controller(self):
        """获取 controller 引用"""
        return self.dispatcher.controller

    @property
    def elf_manager(self):
        """获取 elf_manager 引用"""
        return self.dispatcher.elf_manager

    @property
    def skill_executor(self):
        """获取 skill_executor 引用"""
        return self.dispatcher.skill_executor
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/unit/test_context.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/context.py tests/unit/test_context.py
git commit -m "feat(context): 添加 GameContext 共享状态类

- 存储 slower/sacrifice/my_inactive/enemy_inactive 状态
- 提供具体方法 set_slower/is_slower 等
- 通过 property 访问 dispatcher 的依赖

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 5: 创建 Handler 基类和装饰器

**Files:**
- Create: `src/handlers/base_handler.py`
- Test: `tests/unit/test_base_handler.py`

- [ ] **Step 1: 创建 tests/unit/test_base_handler.py**

```python
import pytest
from abc import ABC


class MockDispatcher:
    """模拟 EventDispatcher"""
    def __init__(self):
        self.controller = None
        self.elf_manager = None
        self.skill_executor = None


class TestBaseHandler:
    """Handler 基类测试"""

    def test_handler_init(self):
        """验证 Handler 初始化"""
        from src.handlers.base_handler import Handler

        class ConcreteHandler(Handler):
            def handle(self, ctx):
                pass

        dispatcher = MockDispatcher()
        handler = ConcreteHandler(dispatcher)

        assert handler.dispatcher == dispatcher
        assert handler.ctrl == dispatcher.controller
        assert handler.elf_mgr == dispatcher.elf_manager
        assert handler.skill == dispatcher.skill_executor

    def test_handler_is_abc(self):
        """验证 Handler 继承自 ABC"""
        from src.handlers.base_handler import Handler

        assert issubclass(Handler, ABC)

    def test_handle_method_is_abstract(self):
        """验证 handle 方法是抽象的"""
        from src.handlers.base_handler import Handler

        with pytest.raises(TypeError):
            Handler(MockDispatcher())
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/unit/test_base_handler.py -v`
Expected: FAIL - ModuleNotFoundError

- [ ] **Step 3: 创建 src/handlers/base_handler.py**

```python
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.event_dispatcher import EventDispatcher


class Handler(ABC):
    """事件处理器基类

    所有事件处理器必须继承此类并实现 handle 方法。

    Args:
        dispatcher: EventDispatcher 引用，用于访问 controller 等依赖
    """

    def __init__(self, dispatcher: "EventDispatcher") -> None:
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
    def handle(self, ctx: "GameContext") -> None:
        """处理事件

        Args:
            ctx: 游戏共享状态上下文
        """
        pass
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/unit/test_base_handler.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/handlers/base_handler.py tests/unit/test_base_handler.py
git commit -m "feat(handler): 添加 Handler 基类和 event_handler 装饰器

- Handler 继承自 ABC
- 通过 dispatcher 属性访问依赖
- event_handler 装饰器用于注册事件处理器

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Phase 2: 基础 Handler

### Task 6: 创建 CometAppearedHandler

**Files:**
- Create: `src/handlers/comet.py`
- Test: `tests/unit/test_handlers/test_comet.py`

- [ ] **Step 1: 创建 tests/unit/test_handlers/test_comet.py**

```python
import pytest
from unittest.mock import Mock, MagicMock


class MockGameContext:
    """模拟 GameContext"""
    def __init__(self):
        self.slower = False
        self.sacrifice = False
        self.my_inactive = 0
        self.enemy_inactive = 0

    def set_slower(self, value):
        self.slower = value

    def is_slower(self):
        return self.slower

    def set_sacrifice(self, value):
        self.sacrifice = value

    def is_sacrifice(self):
        return self.sacrifice

    def update_inactive(self, my, enemy):
        self.my_inactive = my
        self.enemy_inactive = enemy


class TestCometAppearedHandler:
    """CometAppearedHandler 测试"""

    def test_handle_sets_sacrifice_when_slower_and_specific_inactive(self):
        """验证 slower 且特定 inactive 条件时设置 sacrifice"""
        from src.handlers.comet import CometAppearedHandler

        mock_dispatcher = Mock()
        mock_dispatcher.controller = Mock()
        mock_dispatcher.elf_manager = Mock()
        mock_dispatcher.skill_executor = Mock()
        mock_dispatcher.skill_executor.cast_comet = Mock()

        handler = CometAppearedHandler(mock_dispatcher)
        ctx = MockGameContext()
        ctx.slower = True
        ctx.my_inactive = 0
        ctx.enemy_inactive = 1

        handler.handle(ctx)

        assert ctx.sacrifice == True
        mock_dispatcher.skill_executor.cast_comet.assert_called_once()

    def test_handle_calls_cast_comet(self):
        """验证调用 cast_comet"""
        from src.handlers.comet import CometAppearedHandler

        mock_dispatcher = Mock()
        mock_dispatcher.controller = Mock()
        mock_dispatcher.elf_manager = Mock()
        mock_dispatcher.skill_executor = Mock()
        mock_dispatcher.skill_executor.cast_comet = Mock()

        handler = CometAppearedHandler(mock_dispatcher)
        ctx = MockGameContext()

        handler.handle(ctx)

        mock_dispatcher.skill_executor.cast_comet.assert_called_once()
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/unit/test_handlers/test_comet.py -v`
Expected: FAIL - ModuleNotFoundError

- [ ] **Step 3: 创建 src/handlers/comet.py**

```python
from src.handlers.base_handler import Handler
from src.context import GameContext
from src.events import Events
from src.registry import EventRegistry


@EventRegistry.register(
    event=Events.COMET_APPEARED,
    handler_cls=None,  # 填充在类创建后
    template="skills/comet.png",
    region=(0, 0, 2560, 1440),
    similarity=0.8
)
class CometAppearedHandler(Handler):
    """彗星技能可用处理器"""

    def handle(self, ctx: GameContext) -> None:
        """处理彗星技能可用事件

        Args:
            ctx: 游戏共享状态上下文
        """
        # 根据 context 状态决定行为
        if ctx.is_slower() and ctx.my_inactive == 0 and ctx.enemy_inactive == 1:
            ctx.set_sacrifice(True)

        self.skill.cast_comet()


# 装饰器注册需要在类创建后手动关联
EventRegistry._handlers[Events.COMET_APPEARED] = CometAppearedHandler
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/unit/test_handlers/test_comet.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/handlers/comet.py tests/unit/test_handlers/test_comet.py
git commit -m "feat(comet): 添加 CometAppearedHandler

- 响应 COMET_APPEARED 事件
- 调用 skill_executor.cast_comet()

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 7: 创建 DefenseAppearedHandler

**Files:**
- Create: `src/handlers/defense.py`
- Test: `tests/unit/test_handlers/test_defense.py`

- [ ] **Step 1: 创建测试**

```python
import pytest
from unittest.mock import Mock


class MockGameContext:
    """模拟 GameContext"""
    pass


class TestDefenseAppearedHandler:
    """DefenseAppearedHandler 测试"""

    def test_handle_calls_cast_defense(self):
        """验证调用 cast_defense"""
        from src.handlers.defense import DefenseAppearedHandler

        mock_dispatcher = Mock()
        mock_dispatcher.controller = Mock()
        mock_dispatcher.elf_manager = Mock()
        mock_dispatcher.skill_executor = Mock()
        mock_dispatcher.skill_executor.cast_defense = Mock()

        handler = DefenseAppearedHandler(mock_dispatcher)
        ctx = MockGameContext()

        handler.handle(ctx)

        mock_dispatcher.skill_executor.cast_defense.assert_called_once()
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/unit/test_handlers/test_defense.py -v`
Expected: FAIL

- [ ] **Step 3: 创建 src/handlers/defense.py**

```python
from src.handlers.base_handler import Handler
from src.context import GameContext
from src.events import Events
from src.registry import EventRegistry


class DefenseAppearedHandler(Handler):
    """防御技能可用处理器"""

    def handle(self, ctx: GameContext) -> None:
        """处理防御技能可用事件

        Args:
            ctx: 游戏共享状态上下文
        """
        self.skill.cast_defense()


EventRegistry.register(
    event=Events.DEFENSE_APPEARED,
    handler_cls=DefenseAppearedHandler,
    template="skills/defense.png",
    region=(0, 0, 2560, 1440),
    similarity=0.8
)
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/unit/test_handlers/test_defense.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/handlers/defense.py tests/unit/test_handlers/test_defense.py
git commit -m "feat(defense): 添加 DefenseAppearedHandler

- 响应 DEFENSE_APPEARED 事件
- 调用 skill_executor.cast_defense()

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 8: 创建 BattleEndHandler, StartChallengeHandler, ConfirmHandler, RetryHandler

**Files:**
- Create: `src/handlers/battle_end.py`, `src/handlers/start_challenge.py`, `src/handlers/confirm.py`, `src/handlers/retry.py`
- Test: `tests/unit/test_handlers/`

（每个 Handler 的测试和创建步骤类似，以 BattleEndHandler 为例）

**BattleEndHandler:**

- [ ] **Step 1: 创建 tests/unit/test_handlers/test_battle_end.py**

```python
import pytest
from unittest.mock import Mock


class MockGameContext:
    """模拟 GameContext"""
    pass


class TestBattleEndHandler:
    """BattleEndHandler 测试"""

    def test_handle_clicks_battle_end(self):
        """验证点击战斗结束"""
        from src.handlers.battle_end import BattleEndHandler

        mock_dispatcher = Mock()
        mock_dispatcher.controller = Mock()
        mock_dispatcher.controller.find_and_click = Mock()
        mock_dispatcher.elf_manager = Mock()
        mock_dispatcher.skill_executor = Mock()

        handler = BattleEndHandler(mock_dispatcher)
        ctx = MockGameContext()

        handler.handle(ctx)

        mock_dispatcher.controller.find_and_click.assert_called_once()
```

- [ ] **Step 2: 创建 src/handlers/battle_end.py**

```python
from src.handlers.base_handler import Handler
from src.context import GameContext
from src.events import Events
from src.registry import EventRegistry


class BattleEndHandler(Handler):
    """战斗结束处理器"""

    def handle(self, ctx: GameContext) -> None:
        """处理战斗结束事件

        Args:
            ctx: 游戏共享状态上下文
        """
        self.ctrl.find_and_click("battle/battle_end.png")


EventRegistry.register(
    event=Events.BATTLE_END,
    handler_cls=BattleEndHandler,
    template="battle/battle_end.png",
    region=(0, 0, 2560, 1440),
    similarity=0.8
)
```

- [ ] **Step 3: 运行测试验证通过**

Run: `pytest tests/unit/test_handlers/test_battle_end.py -v`
Expected: PASS

- [ ] **Step 4: 提交**

```bash
git add src/handlers/battle_end.py tests/unit/test_handlers/test_battle_end.py
git commit -m "feat(battle_end): 添加 BattleEndHandler

- 响应 BATTLE_END 事件
- 点击 battle_end.png

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

**StartChallengeHandler:**

- [ ] **Step 1: 创建 tests/unit/test_handlers/test_start_challenge.py**

```python
from unittest.mock import Mock

class MockGameContext:
    pass

class TestStartChallengeHandler:
    def test_handle_clicks_start_challenge(self):
        from src.handlers.start_challenge import StartChallengeHandler

        mock_dispatcher = Mock()
        mock_dispatcher.controller = Mock()
        mock_dispatcher.controller.find_and_click = Mock()
        mock_dispatcher.elf_manager = Mock()
        mock_dispatcher.skill_executor = Mock()

        handler = StartChallengeHandler(mock_dispatcher)
        ctx = MockGameContext()

        handler.handle(ctx)

        mock_dispatcher.controller.find_and_click.assert_called_once()
```

- [ ] **Step 2: 创建 src/handlers/start_challenge.py**

```python
from src.handlers.base_handler import Handler
from src.context import GameContext
from src.events import Events
from src.registry import EventRegistry


class StartChallengeHandler(Handler):
    """开始挑战处理器"""

    def handle(self, ctx: GameContext) -> None:
        self.ctrl.find_and_click("battle/start_challenge.png")


EventRegistry.register(
    event=Events.START_CHALLENGE,
    handler_cls=StartChallengeHandler,
    template="battle/start_challenge.png",
    region=(0, 0, 2560, 1440),
    similarity=0.8
)
```

- [ ] **Step 3: 运行测试验证通过**

Run: `pytest tests/unit/test_handlers/test_start_challenge.py -v`
Expected: PASS

- [ ] **Step 4: 提交**

```bash
git add src/handlers/start_challenge.py tests/unit/test_handlers/test_start_challenge.py
git commit -m "feat(start_challenge): 添加 StartChallengeHandler

- 响应 START_CHALLENGE 事件
- 点击 start_challenge.png

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

**ConfirmHandler:**

- [ ] **Step 1: 创建 tests/unit/test_handlers/test_confirm.py**

```python
from unittest.mock import Mock

class MockGameContext:
    pass

class TestConfirmHandler:
    def test_handle_clicks_confirm(self):
        from src.handlers.confirm import ConfirmHandler

        mock_dispatcher = Mock()
        mock_dispatcher.controller = Mock()
        mock_dispatcher.controller.find_and_click = Mock()
        mock_dispatcher.elf_manager = Mock()
        mock_dispatcher.skill_executor = Mock()

        handler = ConfirmHandler(mock_dispatcher)
        ctx = MockGameContext()

        handler.handle(ctx)

        mock_dispatcher.controller.find_and_click.assert_called_once()
```

- [ ] **Step 2: 创建 src/handlers/confirm.py**

```python
from src.handlers.base_handler import Handler
from src.context import GameContext
from src.events import Events
from src.registry import EventRegistry


class ConfirmHandler(Handler):
    """确认处理器"""

    def handle(self, ctx: GameContext) -> None:
        self.ctrl.find_and_click("popup/confirm.png")


EventRegistry.register(
    event=Events.CONFIRM,
    handler_cls=ConfirmHandler,
    template="popup/confirm.png",
    region=(0, 0, 2560, 1440),
    similarity=0.8
)
```

- [ ] **Step 3: 运行测试验证通过**

Run: `pytest tests/unit/test_handlers/test_confirm.py -v`
Expected: PASS

- [ ] **Step 4: 提交**

```bash
git add src/handlers/confirm.py tests/unit/test_handlers/test_confirm.py
git commit -m "feat(confirm): 添加 ConfirmHandler

- 响应 CONFIRM 事件
- 点击 confirm.png

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

**RetryHandler:**

- [ ] **Step 1: 创建 tests/unit/test_handlers/test_retry.py**

```python
from unittest.mock import Mock

class MockGameContext:
    pass

class TestRetryHandler:
    def test_handle_clicks_retry(self):
        from src.handlers.retry import RetryHandler

        mock_dispatcher = Mock()
        mock_dispatcher.controller = Mock()
        mock_dispatcher.controller.find_and_click = Mock()
        mock_dispatcher.elf_manager = Mock()
        mock_dispatcher.skill_executor = Mock()

        handler = RetryHandler(mock_dispatcher)
        ctx = MockGameContext()

        handler.handle(ctx)

        mock_dispatcher.controller.find_and_click.assert_called_once()
```

- [ ] **Step 2: 创建 src/handlers/retry.py**

```python
from src.handlers.base_handler import Handler
from src.context import GameContext
from src.events import Events
from src.registry import EventRegistry


class RetryHandler(Handler):
    """再次切磋处理器"""

    def handle(self, ctx: GameContext) -> None:
        self.ctrl.find_and_click("battle/retry.png")


EventRegistry.register(
    event=Events.RETRY,
    handler_cls=RetryHandler,
    template="battle/retry.png",
    region=(0, 0, 2560, 1440),
    similarity=0.8
)
```

- [ ] **Step 3: 运行测试验证通过**

Run: `pytest tests/unit/test_handlers/test_retry.py -v`
Expected: PASS

- [ ] **Step 4: 提交**

```bash
git add src/handlers/retry.py tests/unit/test_handlers/test_retry.py
git commit -m "feat(retry): 添加 RetryHandler

- 响应 RETRY 事件
- 点击 retry.png

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Phase 3: 精灵相关 Handler

### Task 9: 创建 EnemyAvatarHandler

**Files:**
- Create: `src/handlers/enemy_avatar.py`
- Test: `tests/unit/test_handlers/test_enemy_avatar.py`

- [ ] **Step 1: 创建 tests/unit/test_handlers/test_enemy_avatar.py**

```python
from unittest.mock import Mock

class MockGameContext:
    pass

class TestEnemyAvatarHandler:
    def test_handle_does_nothing(self):
        """验证 EnemyAvatarHandler 正确初始化"""
        from src.handlers.enemy_avatar import EnemyAvatarHandler

        mock_dispatcher = Mock()
        mock_dispatcher.controller = Mock()
        mock_dispatcher.elf_manager = Mock()
        mock_dispatcher.skill_executor = Mock()

        handler = EnemyAvatarHandler(mock_dispatcher)
        ctx = MockGameContext()

        # 此 Handler 主要用于标记敌方精灵出现，不做实际操作
        handler.handle(ctx)
```

- [ ] **Step 2: 创建 src/handlers/enemy_avatar.py**

```python
from src.handlers.base_handler import Handler
from src.context import GameContext
from src.events import Events
from src.registry import EventRegistry


class EnemyAvatarHandler(Handler):
    """敌方精灵头像处理器

    用于检测敌方精灵头像出现，主要作为状态标记。
    实际自爆流检测由 EnemySelfDestructHandler 持续检测。
    """

    def handle(self, ctx: GameContext) -> None:
        """处理敌方精灵头像事件

        Args:
            ctx: 游戏共享状态上下文
        """
        # 此 Handler 主要用于触发 ENEMY_AVATAR 事件
        # 实际行为（如自爆流检测）在检测循环中持续进行
        pass


EventRegistry.register(
    event=Events.ENEMY_AVATAR,
    handler_cls=EnemyAvatarHandler,
    template=[],  # 动态从 elf_manager 获取
    region=(2000, 0, 2560, 320),
    similarity=0.7
)
```

- [ ] **Step 3: 运行测试验证通过**

Run: `pytest tests/unit/test_handlers/test_enemy_avatar.py -v`
Expected: PASS

- [ ] **Step 4: 提交**

```bash
git add src/handlers/enemy_avatar.py tests/unit/test_handlers/test_enemy_avatar.py
git commit -m "feat(enemy_avatar): 添加 EnemyAvatarHandler

- 响应 ENEMY_AVATAR 事件
- 敌方精灵头像出现时标记

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 10: 创建 SwitchElfHandler

**Files:**
- Create: `src/handlers/switch_elf.py`
- Test: `tests/unit/test_handlers/test_switch_elf.py`

- [ ] **Step 1: 创建 tests/unit/test_handlers/test_switch_elf.py**

```python
import pytest
from unittest.mock import Mock


class MockGameContext:
    """模拟 GameContext"""
    def __init__(self):
        self.slower = False
        self.sacrifice = False
        self.my_inactive = 0
        self.enemy_inactive = 0

    def is_slower(self):
        return self.slower

    def is_sacrifice(self):
        return self.sacrifice


class TestSwitchElfHandler:
    """SwitchElfHandler 测试"""

    def test_handle_sacrifice_clicks_sacrifice_elf(self):
        """验证 sacrifice 状态点击送死精灵"""
        from src.handlers.switch_elf import SwitchElfHandler

        mock_dispatcher = Mock()
        mock_dispatcher.controller = Mock()
        mock_dispatcher.controller.find_and_click = Mock()
        mock_dispatcher.elf_manager = Mock()
        mock_dispatcher.elf_manager.get_sacrifice_template = Mock(return_value="elves/pig3.png")
        mock_dispatcher.skill_executor = Mock()

        handler = SwitchElfHandler(mock_dispatcher)
        ctx = MockGameContext()
        ctx.sacrifice = True

        handler.handle(ctx)

        mock_dispatcher.elf_manager.get_sacrifice_template.assert_called_once()
        mock_dispatcher.controller.find_and_click.assert_called_once()

    def test_handle_slower_clicks_reserve_elf(self):
        """验证 slower 状态点击 reserve 精灵"""
        from src.handlers.switch_elf import SwitchElfHandler

        mock_dispatcher = Mock()
        mock_dispatcher.controller = Mock()
        mock_dispatcher.controller.find_and_click = Mock()
        mock_dispatcher.elf_manager = Mock()
        mock_dispatcher.elf_manager.get_reserve_template = Mock(return_value="elves/scepter3.png")
        mock_dispatcher.skill_executor = Mock()

        handler = SwitchElfHandler(mock_dispatcher)
        ctx = MockGameContext()
        ctx.slower = True
        ctx.my_inactive = 0

        handler.handle(ctx)

        mock_dispatcher.elf_manager.get_reserve_template.assert_called_once()
        mock_dispatcher.controller.find_and_click.assert_called_once()
```

- [ ] **Step 2: 创建 src/handlers/switch_elf.py**

```python
from src.handlers.base_handler import Handler
from src.context import GameContext
from src.events import Events
from src.registry import EventRegistry


class SwitchElfHandler(Handler):
    """切换精灵处理器"""

    def handle(self, ctx: GameContext) -> None:
        """处理切换精灵事件

        Args:
            ctx: 游戏共享状态上下文
        """
        if ctx.is_sacrifice():
            # 执行送死精灵切换
            template = self.elf_mgr.get_sacrifice_template()
            self.ctrl.find_and_click(template)
        elif ctx.is_slower() and ctx.my_inactive == 0:
            # SLOWER 流程：切换 reserve 精灵
            template = self.elf_mgr.get_reserve_template()
            self.ctrl.find_and_click(template)


EventRegistry.register(
    event=Events.SWITCH_ELF,
    handler_cls=SwitchElfHandler,
    template=["elves/tree3.png", "elves/otter2.png", "elves/pig3.png", "elves/scepter3.png"],
    region=(0, 0, 700, 320),
    similarity=0.7
)
```

- [ ] **Step 3: 运行测试验证通过**

Run: `pytest tests/unit/test_handlers/test_switch_elf.py -v`
Expected: PASS

- [ ] **Step 4: 提交**

---

### Task 11: 创建 EnemySelfDestructHandler

**Files:**
- Create: `src/handlers/enemy_self_destruct.py`
- Test: `tests/unit/test_handlers/test_enemy_self_destruct.py`

- [ ] **Step 1: 创建 tests/unit/test_handlers/test_enemy_self_destruct.py**

```python
from unittest.mock import Mock

class MockGameContext:
    pass

class TestEnemySelfDestructHandler:
    def test_handle_escapes_and_stops(self):
        """验证检测到自爆流后逃跑并停止"""
        from src.handlers.enemy_self_destruct import EnemySelfDestructHandler

        mock_dispatcher = Mock()
        mock_dispatcher.controller = Mock()
        mock_dispatcher.elf_manager = Mock()
        mock_dispatcher.skill_executor = Mock()
        mock_dispatcher.skill_executor.escape_battle = Mock()
        mock_dispatcher.running = True

        handler = EnemySelfDestructHandler(mock_dispatcher)
        ctx = MockGameContext()

        handler.handle(ctx)

        mock_dispatcher.skill_executor.escape_battle.assert_called_once()
        mock_dispatcher.stop.assert_called_once()
```

- [ ] **Step 2: 创建 src/handlers/enemy_self_destruct.py**

```python
from src.handlers.base_handler import Handler
from src.context import GameContext
from src.events import Events
from src.registry import EventRegistry


class EnemySelfDestructHandler(Handler):
    """敌方自爆流处理器

    检测到敌方自爆流精灵时执行逃跑并停止主循环。
    """

    def handle(self, ctx: GameContext) -> None:
        """处理敌方自爆流事件

        Args:
            ctx: 游戏共享状态上下文
        """
        self.skill.escape_battle()
        self.dispatcher.stop()


EventRegistry.register(
    event=Events.ENEMY_SELF_DESTRUCT,
    handler_cls=EnemySelfDestructHandler,
    template=[],  # 动态从 elf_manager 获取
    region=(2000, 0, 2560, 320),
    similarity=0.7
)
```

- [ ] **Step 3: 运行测试验证通过**

Run: `pytest tests/unit/test_handlers/test_enemy_self_destruct.py -v`
Expected: PASS

- [ ] **Step 4: 提交**

```bash
git add src/handlers/enemy_self_destruct.py tests/unit/test_handlers/test_enemy_self_destruct.py
git commit -m "feat(enemy_self_destruct): 添加 EnemySelfDestructHandler

- 响应 ENEMY_SELF_DESTRUCT 事件
- 检测到自爆流时逃跑并停止

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Phase 4: 状态检测 Handler

### Task 12: 创建 DotsChangedHandler

**Files:**
- Create: `src/handlers/dots_changed.py`
- Test: `tests/unit/test_handlers/test_dots_changed.py`

- [ ] **Step 1: 创建 tests/unit/test_handlers/test_dots_changed.py**

```python
from unittest.mock import Mock

class MockGameContext:
    def __init__(self):
        self.my_inactive = 0
        self.enemy_inactive = 0

    def update_inactive(self, my, enemy):
        self.my_inactive = my
        self.enemy_inactive = enemy

class TestDotsChangedHandler:
    def test_handle_updates_inactive_counts(self):
        """验证更新 inactive dot 数量"""
        from src.handlers.dots_changed import DotsChangedHandler

        mock_dispatcher = Mock()
        mock_dispatcher.controller = Mock()
        mock_dispatcher.controller.find_images_all = Mock(side_effect=[
            [1, 2, 3],  # my_active
            [4, 5],     # enemy_inactive
        ])
        mock_dispatcher.elf_manager = Mock()
        mock_dispatcher.skill_executor = Mock()

        handler = DotsChangedHandler(mock_dispatcher)
        ctx = MockGameContext()

        handler.handle(ctx)

        assert ctx.my_inactive == 3
        assert ctx.enemy_inactive == 2
```

- [ ] **Step 2: 创建 src/handlers/dots_changed.py**

```python
from src.handlers.base_handler import Handler
from src.context import GameContext
from src.events import Events
from src.registry import EventRegistry


class DotsChangedHandler(Handler):
    """Dot 状态变化处理器

    检测到我方 active dot 和敌方 inactive dot 数量变化时更新 context。
    """

    def handle(self, ctx: GameContext) -> None:
        """处理 dot 状态变化事件

        Args:
            ctx: 游戏共享状态上下文
        """
        # 统计我方 active dot
        my_active = self.ctrl.find_images_all(
            "dots/dot_active.png",
            region=(0, 0, 700, 320)
        )
        # 统计敌方 inactive dot
        enemy_inactive = self.ctrl.find_images_all(
            "dots/dot_inactive.png",
            region=(2000, 0, 2560, 320)
        )
        ctx.update_inactive(len(my_active), len(enemy_inactive))


EventRegistry.register(
    event=Events.DOTS_CHANGED,
    handler_cls=DotsChangedHandler,
    template=["dots/dot_active.png", "dots/dot_inactive.png"],
    region=(0, 0, 2560, 1440),
    similarity=0.8
)
```

- [ ] **Step 3: 运行测试验证通过**

Run: `pytest tests/unit/test_handlers/test_dots_changed.py -v`
Expected: PASS

- [ ] **Step 4: 提交**

```bash
git add src/handlers/dots_changed.py tests/unit/test_handlers/test_dots_changed.py
git commit -m "feat(dots): 添加 DotsChangedHandler

- 响应 DOTS_CHANGED 事件
- 统计并更新 inactive dot 数量到 context

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 13: 创建 SpeedCheckHandler

**Files:**
- Create: `src/handlers/speed_check.py`
- Test: `tests/unit/test_handlers/test_speed_check.py`

- [ ] **Step 1: 创建 tests/unit/test_handlers/test_speed_check.py**

```python
from unittest.mock import Mock

class MockGameContext:
    def __init__(self):
        self.my_inactive = 0
        self.enemy_inactive = 0
        self._slower = False

    def set_slower(self, value):
        self._slower = value

    def is_slower(self):
        return self._slower

class TestSpeedCheckHandler:
    def test_handle_sets_slower_when_enemy_faster(self):
        """验证敌方更快时设置 slower=True"""
        from src.handlers.speed_check import SpeedCheckHandler

        mock_dispatcher = Mock()
        mock_dispatcher.controller = Mock()
        mock_dispatcher.elf_manager = Mock()
        mock_dispatcher.skill_executor = Mock()

        handler = SpeedCheckHandler(mock_dispatcher)
        ctx = MockGameContext()
        ctx.my_inactive = 1
        ctx.enemy_inactive = 0

        handler.handle(ctx)

        assert ctx.is_slower() == True

    def test_handle_sets_faster_when_our_faster(self):
        """验证我方更快时设置 slower=False"""
        from src.handlers.speed_check import SpeedCheckHandler

        mock_dispatcher = Mock()
        mock_dispatcher.controller = Mock()
        mock_dispatcher.elf_manager = Mock()
        mock_dispatcher.skill_executor = Mock()

        handler = SpeedCheckHandler(mock_dispatcher)
        ctx = MockGameContext()
        ctx.my_inactive = 0
        ctx.enemy_inactive = 1

        handler.handle(ctx)

        assert ctx.is_slower() == False
```

- [ ] **Step 2: 创建 src/handlers/speed_check.py**

```python
from src.handlers.base_handler import Handler
from src.context import GameContext
from src.events import Events
from src.registry import EventRegistry


class SpeedCheckHandler(Handler):
    """速度检测处理器

    基于 inactive dot 数量判断速度优势，设置 ctx.slower 标志。
    """

    def handle(self, ctx: GameContext) -> None:
        """处理速度检测事件

        Args:
            ctx: 游戏共享状态上下文
        """
        # 如果我方已有 inactive 且敌方无 inactive，说明敌方更快
        if ctx.my_inactive > 0 and ctx.enemy_inactive == 0:
            ctx.set_slower(True)
        # 如果敌方已有 inactive 且我方无 inactive，说明我方更快
        elif ctx.enemy_inactive > 0 and ctx.my_inactive == 0:
            ctx.set_slower(False)


EventRegistry.register(
    event=Events.SPEED_CHECK,
    handler_cls=SpeedCheckHandler,
    template=["dots/dot_active.png", "dots/dot_inactive.png"],
    region=(0, 0, 2560, 1440),
    similarity=0.8
)
```

- [ ] **Step 3: 运行测试验证通过**

Run: `pytest tests/unit/test_handlers/test_speed_check.py -v`
Expected: PASS

- [ ] **Step 4: 提交**

```bash
git add src/handlers/speed_check.py tests/unit/test_handlers/test_speed_check.py
git commit -m "feat(speed_check): 添加 SpeedCheckHandler

- 响应 SPEED_CHECK 事件
- 基于 inactive dot 判断速度优势

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Phase 5: 主循环重构

### Task 14: 创建 EventDetector

**Files:**
- Create: `src/detector.py`
- Test: `tests/unit/test_detector.py`

**注意:** EventDetector 需要 elf_manager 来处理动态模板（ENEMY_SELF_DESTRUCT 等）

- [ ] **Step 1: 创建 tests/unit/test_detector.py**

```python
import pytest
from unittest.mock import Mock, MagicMock


class TestEventDetector:
    """EventDetector 测试"""

    def test_scan_all_returns_detected_events(self):
        """验证 scan_all 返回触发的事件"""
        from src.detector import EventDetector
        from src.events import Events
        from src.event_config import EventConfig

        mock_controller = Mock()
        mock_controller.find_image = Mock(side_effect=[
            True,   # COMET_APPEARED 触发
            False,  # DEFENSE_APPEARED 不触发
        ])
        mock_controller.elf_manager = Mock()

        config = {
            Events.COMET_APPEARED: EventConfig("a.png", (0,0,1,1), 0.8),
            Events.DEFENSE_APPEARED: EventConfig("b.png", (0,0,1,1), 0.8),
        }

        detector = EventDetector(mock_controller, config)
        detected = detector.scan_all()

        assert Events.COMET_APPEARED in detected
        assert Events.DEFENSE_APPEARED not in detected
```

- [ ] **Step 2: 创建 src/detector.py**

```python
from typing import Union, List, Dict, Optional
from src.events import Events
from src.event_config import EventConfig


class EventDetector:
    """图像检测引擎

    负责扫描所有事件配置，检测图像是否出现。
    """

    def __init__(self, controller, config: Dict[Events, EventConfig]):
        """初始化检测器

        Args:
            controller: GameController 实例（需包含 elf_manager 属性）
            config: 事件配置字典
        """
        self.ctrl = controller
        self.elf_manager = controller.elf_manager  # 从 controller 获取 elf_manager
        self.event_configs = config

    def scan_all(self) -> List[Events]:
        """全量检测所有事件

        Returns:
            触发的事件列表
        """
        detected = []
        for event, cfg in self.event_configs.items():
            if self._match_image(event, cfg):
                detected.append(event)
        return detected

    def _match_image(self, event: Events, cfg: EventConfig) -> bool:
        """检测指定事件对应的图像是否出现

        Args:
            event: 事件
            cfg: 事件配置

        Returns:
            是否检测到
        """
        template = self._get_template_for_event(event, cfg)
        if not template:
            return False

        return self.ctrl.find_image(
            template=template,
            similarity=cfg.similarity,
            x0=cfg.region[0],
            y0=cfg.region[1],
            x1=cfg.region[2],
            y1=cfg.region[3]
        ) is not None

    def _get_template_for_event(
        self, event: Events, cfg: EventConfig
    ) -> Union[str, List[str], None]:
        """获取事件的模板

        动态模板从 elf_manager 获取。

        Args:
            event: 事件
            cfg: 事件配置

        Returns:
            模板路径或 None
        """
        # 空列表表示动态模板
        if isinstance(cfg.template, list) and len(cfg.template) == 0:
            if event == Events.ENEMY_SELF_DESTRUCT:
                return self.elf_manager.get_selfdestruct_templates()
            elif event == Events.SWITCH_ELF:
                return self.ctrl.elf_manager.get_switch_templates()
            return None
        return cfg.template
```

- [ ] **Step 3: 运行测试验证通过**

Run: `pytest tests/unit/test_detector.py -v`
Expected: PASS

- [ ] **Step 4: 提交**

---

### Task 15: 重构 EventDispatcher

**Files:**
- Modify: `src/event_dispatcher.py`
- Test: `tests/unit/test_event_dispatcher.py`

- [ ] **Step 1: 创建 tests/unit/test_event_dispatcher.py**

```python
import pytest
from unittest.mock import Mock


class TestEventDispatcher:
    """EventDispatcher 测试"""

    def test_register_handler(self):
        """验证注册处理器"""
        from src.event_dispatcher import EventDispatcher
        from src.events import Events

        mock_controller = Mock()
        mock_elf_manager = Mock()
        mock_skill_executor = Mock()

        dispatcher = EventDispatcher(
            mock_controller, mock_elf_manager, mock_skill_executor, {}
        )

        class MockHandler:
            def handle(self, ctx):
                pass

        dispatcher.register_handler(Events.COMET_APPEARED, MockHandler)

        assert Events.COMET_APPEARED in dispatcher.handlers

    def test_stop_sets_running_false(self):
        """验证 stop 方法"""
        from src.event_dispatcher import EventDispatcher

        dispatcher = EventDispatcher(Mock(), Mock(), Mock(), {})
        dispatcher.running = True

        dispatcher.stop()

        assert dispatcher.running == False
```

- [ ] **Step 2: 重构 src/event_dispatcher.py**

```python
from typing import Dict, Optional
from src.context import GameContext
from src.detector import EventDetector
from src.events import Events
from src.event_config import EventConfig


class EventDispatcher:
    """事件分发器（主循环）

    协调 EventDetector、Handler 和 GameContext。
    """

    def __init__(
        self,
        controller,
        elf_manager,
        skill_executor,
        config: dict
    ):
        self.controller = controller
        self.elf_manager = elf_manager
        self.skill_executor = skill_executor
        self.context = GameContext(dispatcher=self)
        self.detector = EventDetector(controller, config)
        self.handlers: Dict[Events, Handler] = {}
        self.running = False

    def register_handler(self, event: Events, handler: Handler) -> None:
        """注册事件处理器

        Args:
            event: 事件
            handler: 处理器实例
        """
        self.handlers[event] = handler

    def run(self) -> None:
        """运行主循环

        持续检测事件并处理，直到 stop() 被调用。
        """
        self.running = True
        while self.running:
            detected = self.detector.scan_all()
            for event in detected:
                handler = self.handlers.get(event)
                if handler:
                    handler.handle(self.context)

    def stop(self) -> None:
        """停止主循环"""
        self.running = False
```

- [ ] **Step 3: 运行测试验证通过**

Run: `pytest tests/unit/test_event_dispatcher.py -v`
Expected: PASS

- [ ] **Step 4: 提交**

---

### Task 16: 更新 handlers/__init__.py

**Files:**
- Modify: `src/handlers/__init__.py`

- [ ] **Step 1: 更新 src/handlers/__init__.py**

```python
from src.handlers.base_handler import Handler
from src.handlers.comet import CometAppearedHandler
from src.handlers.defense import DefenseAppearedHandler
from src.handlers.battle_end import BattleEndHandler
from src.handlers.start_challenge import StartChallengeHandler
from src.handlers.confirm import ConfirmHandler
from src.handlers.retry import RetryHandler
from src.handlers.switch_elf import SwitchElfHandler
from src.handlers.dots_changed import DotsChangedHandler
from src.handlers.speed_check import SpeedCheckHandler
from src.handlers.enemy_self_destruct import EnemySelfDestructHandler

__all__ = [
    "Handler",
    "CometAppearedHandler",
    "DefenseAppearedHandler",
    "BattleEndHandler",
    "StartChallengeHandler",
    "ConfirmHandler",
    "RetryHandler",
    "SwitchElfHandler",
    "DotsChangedHandler",
    "SpeedCheckHandler",
    "EnemySelfDestructHandler",
]
```

- [ ] **Step 2: 提交**

---

## Phase 6: 清理

### Task 17: 验证和清理

- [ ] 验证新架构运行 10+ 轮战斗
- [ ] 确认 state_machine.py 无引用后可删除
- [ ] 更新 main.py
- [ ] 更新文档

---

## 执行选项

**Plan complete and saved to `docs/superpowers/plans/2026-04-06-event-driven-architecture-plan.md`.**

**Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
