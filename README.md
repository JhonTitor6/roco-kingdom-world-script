> [!WARNING]
> **免责声明 - 务必阅读**
>
> - 本脚本仅供学习交流与研究使用，**禁止用于任何商业目的**
> - 游戏官方明确禁止使用任何脚本、辅助工具及外挂，**使用本脚本风险自负**
> - 因使用本脚本导致的任何后果（包括但不限于账号封禁、游戏数据异常等），作者不承担任何责任
> - 请在充分理解相关风险后再使用本项目

---

# 洛克王国：世界 - 闪耀大赛自动化脚本

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-green.svg)
![OpenCV](https://img.shields.io/badge/OpenCV-Template%20Matching-red.svg)

基于图像识别的游戏战斗自动化工具，专为洛克王国 PC 版的"闪耀大赛"刷金币场景设计。

## 功能特性

- **事件驱动架构**：基于 `EventDetector` + `EventRegistry` 的图像检测引擎，支持插件式事件处理器
- **全自动战斗流程**：自动进入战斗、检测速度优势、执行送死序列、处理战斗结算
- **智能图像识别**：基于 OpenCV 模板匹配，支持中文路径截图处理
- **敌方自爆流检测**：自动识别敌方自爆流精灵（蝴蝶），触发紧急退出
- **灵活精灵管理**：支持首发、送死、备用多种角色配置
- **多种技能执行**：彗星技能、防御姿态、聚能切换、精灵切换
- **后台运行**：无需游戏窗口在前台，支持后台自动化控制

## 项目结构

```
roco-kingdom-world-script/
├── main.py                     # 程序入口
├── src/                        # 核心源代码
│   ├── detector.py             # EventDetector 图像检测引擎
│   ├── registry.py             # EventRegistry 事件注册表
│   ├── event_config.py         # EventConfig 事件配置
│   ├── events.py               # Events 事件枚举
│   ├── context.py              # GameContext 游戏共享状态
│   ├── event_dispatcher.py     # EventDispatcher 主循环
│   ├── skill_executor.py       # SkillExecutor 技能执行器
│   ├── elf_manager.py          # ElfManager 精灵管理器
│   ├── controller.py           # GameController 游戏控制器
│   └── handlers/                # 事件处理器
│       ├── base_handler.py      # Handler 基类
│       ├── comet.py             # 彗星技能处理器
│       ├── defense.py           # 防御技能处理器
│       ├── dots_changed.py      # 圆点变化处理器（含速度检测）
│       ├── enemy_avatar.py      # 敌方精灵头像处理器
│       ├── enemy_self_destruct.py # 敌方自爆流处理器
│       ├── switch_elf.py        # 切换精灵处理器
│       ├── battle_end.py        # 战斗结束处理器
│       ├── start_challenge.py   # 开始挑战处理器
│       ├── confirm.py           # 确认处理器
│       └── retry.py             # 再次切磋处理器
├── win_util/                   # Windows UI 自动化工具
├── config/                     # 配置文件
│   ├── settings.json           # 主配置（超时、相似度）
│   └── elves.json              # 精灵配置
├── assets/templates/           # 图像识别模板
│   ├── battle/                 # 战斗相关模板
│   ├── skills/                 # 技能图标
│   ├── elves/                  # 精灵头像
│   ├── dots/                  # 圆点状态
│   └── popup/                  # 弹窗按钮
└── tests/                      # 测试套件
```

## 快速开始

### 环境要求

- Python 3.10+
- Windows 10/11
- 洛克王国：世界 PC 版
- 游戏分辨率：2560×1440 全屏，画质：超高（**暂不支持其他分辨率，其他画质未测试**）

### 安装依赖

```bash
# 克隆项目
git clone https://github.com/your-repo/roco-kingdom-world-script.git
cd roco-kingdom-world-script

# 创建虚拟环境（推荐）
python -m venv .venv
.venv\Scripts\activate

# 安装依赖
pip install -e .
```

### 运行

> [!NOTE]
> 在闪耀大赛界面，看到 **"开始挑战"** 按钮后启动脚本。

```bash
python main.py
```

## 架构说明

### 事件驱动架构

```
EventDetector (图像检测) → EventDispatcher (主循环) → Handler (事件处理器)
                                                        ↓
                                                   GameContext (共享状态)
```

1. **EventDetector**：图像检测引擎，支持模板匹配、区域限定、超时等待
2. **EventRegistry**：事件注册表，管理事件与处理器的映射关系
3. **EventDispatcher**：主循环，协调检测与分发
4. **Handler**：事件处理器，实现具体业务逻辑
5. **GameContext**：游戏共享状态，在处理器间传递数据

### 支持的事件类型

| 事件 | 处理器 | 说明 |
|------|--------|------|
| `COMET_APPEARED` | CometHandler | 彗星技能出现 |
| `DEFENSE_APPEARED` | DefenseHandler | 防御姿态出现 |
| `DOTS_CHANGED` | DotsChangedHandler | 圆点状态变化（含速度检测） |
| `ENEMY_AVATAR` | EnemyAvatarHandler | 敌方精灵头像出现 |
| `ENEMY_SELF_DESTRUCT` | EnemySelfDestructHandler | 敌方自爆流检测 |
| `SWITCH_ELF` | SwitchElfHandler | 切换精灵时机 |
| `BATTLE_END` | BattleEndHandler | 战斗结束 |
| `START_CHALLENGE` | StartChallengeHandler | 开始挑战 |
| `CONFIRM` | ConfirmHandler | 确认按钮 |
| `RETRY` | RetryHandler | 再次切磋 |

## 配置说明

### 主配置 (config/settings.json)

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `similarity` | 图像识别相似度阈值 | 0.8 |
| `skill_wait_after_cast` | 技能释放后等待时间(秒) | 10 |
| `loop_count` | 循环执行轮数 | 10 |
| `timeouts.*` | 各种操作超时配置 | - |

### 精灵配置 (config/elves.json)

```json
{
  "elves": [
    {"name": "幽影树", "template": ["elves/tree3.png", "elves/tree3_lineup.png"], "role": "final"},
    {"name": "獠牙猪", "template": "elves/pig3.png", "role": "sacrifice"},
    {"name": "獭", "template": "elves/otter2.png", "role": "sacrifice"},
    {"name": "权杖", "template": "elves/scepter3.png", "role": "reserve"}
  ]
}
```

**角色说明**：
- `final` - 首发精灵，如果速度慢最后送死
- `sacrifice` - 送死精灵，猪、獭等
- `reserve` - 存活精灵，权杖，如果首发速度快最后送死

## 战斗流程

```
进入战斗 → 速度检测 → 送死序列 → 战斗结束 → 再次切磋
```

1. **进入战斗**：点击开始挑战 → 检查精灵不足弹窗 → 选择首发 → 确认 → 等待战斗开始
2. **速度检测**：通过检测 inactive dot 出现顺序判断我方/敌方谁先行动
3. **送死序列**：
   - 有速度优势：sacrifice 送死 → reserve → reserve 循环防御/聚能
   - 无速度优势：final 循环防御/聚能 → 等待敌方送死3只 → reserve 送死 → sacrifice 送死 → final 送死
4. **敌方自爆流**：检测到蝴蝶等自爆精灵时，触发紧急退出
5. **战斗结束**：点击再次切磋 → 自动进入下一轮

## 图像识别模板

模板文件存放在 `assets/templates/` 目录：

| 类别 | 模板文件 | 用途 |
|------|----------|------|
| 战斗 | `start_challenge.png` | 开始挑战按钮 |
| | `battle_end.png` | 战斗结束标识 |
| | `retry.png` | 再次切磋按钮 |
| 技能 | `comet.png` | 彗星技能 |
| | `defense.png` | 防御姿态 |
| | `energy.png` | 聚能图标 |
| | `switch.png` | 切换精灵 |
| | `escape.png` | 逃跑技能 |
| 状态 | `dot_active.png` | 活跃圆点 |
| | `dot_inactive.png` | 非活跃圆点 |
| 弹窗 | `confirm.png` | 确认按钮 |
| | `insufficient.png` | 精灵不足提示 |
| | `yes.png` | 是/确认按钮 |

## 测试

```bash
# 运行所有测试
pytest

# 运行单个测试文件
pytest tests/integration/test_dot_detection.py -v

# 运行单元测试
pytest tests/unit/ -v
```

