# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

洛克王国：世界 - 闪耀大赛自动化脚本。通过图像识别实现游戏战斗自动化。

## 开发环境

```bash
# 安装依赖
pip install -e .

# 或安装本地 win_util 工具包
pip install -e F:/Users/56440/PythonProjects/roco-kingdom-world-script/win_util

# 运行测试
pytest

# 运行单个测试文件
pytest tests/integration/test_dot_detection.py -v
```

## 架构

### 事件驱动架构（新版）

```
main.py                  # 程序入口，调用 setup_logger() 初始化日志
├── src/
│   ├── events.py       # Events 枚举（12 个事件类型）
│   ├── event_config.py # EventConfig 数据类
│   ├── registry.py     # EventRegistry 事件注册表
│   ├── context.py      # GameContext 共享状态
│   ├── detector.py     # EventDetector 图像检测引擎
│   ├── event_dispatcher.py # 主循环（事件驱动）
│   └── handlers/
│       ├── base_handler.py      # Handler 基类
│       ├── battle_end.py        # 战斗结束（UI 过渡）
│       ├── quit_handler.py       # 退出（根据 ctx.enemy_self_destruct 判断）
│       ├── retry.py             # 再次切磋
│       ├── skill_castable.py     # 技能释放 + 自爆流检测
│       └── ...                  # 其他 handler

### Handler 自动注册机制
- `handlers/__init__.py` 通过 `importlib` 自动发现并导入所有 handler 模块
- 每个 handler 文件底部调用 `EventRegistry.register()` 自注册
- 新增 handler 只需创建文件并调用注册，无需手动 import
- 排除列表：`_EXCLUDE = {"__init__", "base_handler", "error", "battle", "insufficient"}`
```

### SkillExecutor 方法
- `cast_skill("comet")` - 释放彗星技能
- `press_defense()` - 释放防御技能
- `escape_battle()` - 执行逃跑（点击 escape.png → confirm.png）
- `switch_to_elf(elf)` - 切换精灵
- `press_energy()` - 聚能

### GameContext 关键字段
- `enemy_self_destruct` - 敌方是否为自爆流（SkillCastableHandler 写入，跨 handler 共享）

### 重要初始化
- `main.py` 必须调用 `setup_logger()` 启用日志文件输出
- `controller.elf_manager = elf_manager` - EventDetector 依赖此引用

### 旧架构（待废弃）
- `state_machine.py` - 战斗状态机
- `battle_flow.py` - 战斗流程控制
- `handlers/battle.py` - 旧战斗 Handler
- `handlers/select_elf.py` - 旧选精灵 Handler
- `handlers/error.py` - 旧错误 Handler

## 核心模块说明

### 战斗结束流程（重要：battle_end → retry/quit 解耦）

- **battle_end**：纯 UI 过渡事件，点击后切换到 retry + quit 共存画面
- **retry / quit**：共存的两个退出选项，retry = 再次切磋（自爆流），quit = 退出（其他情况）
- **自爆流判断**：SkillCastableHandler 在战斗过程中检测，结果写入 `ctx.enemy_self_destruct`，各 handler 自行判断
- **关键约束**：BattleEndHandler 不含任何业务判断，业务逻辑分散在各退出 handler 中

### 战斗流程
1. `run_entry_flow()` - 进入战斗：点击开始挑战 → 检查精灵不足弹窗 → 选择首发 → 确认 → 等待战斗开始
2. `detect_speed_advantage()` - 通过检测 inactive dot 出现顺序判断速度优势
3. `faster_flow()` / `slower_flow()` - 根据速度优势执行不同送死顺序
4. `handle_battle_end()` - 处理战斗结束，点击再次切磋

### 图像识别
- `GameController.find_image()` 支持单字符串或字符串列表，自动遍历查找
- `GameController.find_images_all()` 查找所有匹配位置
- `GameController.find_image_with_timeout()` 带超时等待
- 模板路径相对于 `assets/templates/`

### 精灵角色
- `final` - 首发精灵，最后送死
- `sacrifice` - 送死精灵
- `reserve` - 备用精灵

### 关键配置 (settings.json)
- `similarity`: 图像识别相似度阈值 (默认 0.6)
- `skill_wait_after_cast`: 技能释放后等待时间
- `timeouts.*`: 各种操作超时配置
- `loop_count`: 循环执行轮数

## 测试

- `tests/conftest.py` - 共享 fixtures，包含中文路径截图加载辅助函数 `imread_unicode`
- `tests/integration/` - 集成测试，使用真实游戏截图验证
- `tests/unit/` - 单元测试

### 测试要求
- **测试用例必须调用真实代码**：测试用例应调用实际的项目模块（如 `win_util.image.ImageFinder.bg_find_pic_all`），而非在测试文件中重新实现相同的匹配逻辑
- 禁止在测试文件中重复实现已存在的功能代码，确保测试验证的是真实代码流程

## 行为准则

- **先自己找问题，再提问**：当用户描述问题时，先主动阅读相关代码、排查可能原因、尝试分析，不要在未进行任何分析的情况下直接向用户提问。确实无法解决时再提问，并说明已尝试的排查思路和结论

## 代码规范

### 禁止使用 dict 表示业务实体
- **必须使用类替代 dict**：如 `Elf` 类替代精灵 dict
- **类属性、参数、返回值必须声明类型**
- 配置数据从 dict 解析后应转换为类型对象

### Elf 类规范
```python
class Elf:
    """精灵数据类"""
    name: str
    templates: List[str]
    role: str
    switch_sleep: Optional[int]

    def __init__(self, name: str, templates: str | List[str], role: str, switch_sleep: Optional[int] = None):
        self.name = name
        self.templates = [templates] if isinstance(templates, str) else templates
        self.role = role
        self.switch_sleep = switch_sleep

    @property
    def template(self) -> str:
        """获取第一个模板路径（兼容接口）"""
        return self.templates[0]
```

## 注意事项

- 中文路径截图读取：`PIL.Image.open()` + `cv2.cvtColor()`，不用 `cv2.imread`
- 后台点击不生效时使用前台点击 `left_click`
- `setup_logger()` 只在 `main.py` 中调用一次，不要在模块中重复初始化

## 重要

- 在我没下指令前，禁止直接 push 代码