# 洛克王国：世界 - 闪耀大赛自动化

> [!WARNING]
> 本脚本仅供学习交流与研究使用，**禁止用于任何商业目的**。游戏官方明确禁止使用任何脚本、辅助工具及外挂，**使用本脚本风险自负**。因使用本脚本导致的任何后果（包括但不限于账号封禁、游戏数据异常等），作者不承担任何责任。

基于 OpenCV 图像识别的游戏战斗自动化工具，专为洛克王国 PC 版"闪耀大赛"刷金币场景设计。

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Platform](https://img.shields.io/badge/Platform-Windows-green.svg)
[![OpenCV](https://img.shields.io/badge/OpenCV-Template%20Matching-red.svg)

## 功能特性

| 特性 | 说明 |
|------|------|
| **事件驱动架构** | 插件式事件处理器，扩展方便 |
| **全自动战斗** | 自动进入、速度检测、送死序列、战斗结算 |
| **智能图像识别** | OpenCV 模板匹配，支持中文路径 |
| **自爆流检测** | 自动识别蝴蝶等自爆精灵，触发紧急退出 |
| **后台运行** | 无需游戏窗口在前台 |

## 快速开始

### 环境要求

- Python 3.10+ / Windows 10/11
- 游戏分辨率：2560×1440 全屏，画质：超高
- 洛克王国：世界 PC 版

### 安装

```bash
git clone https://github.com/your-repo/roco-kingdom-world-script.git
cd roco-kingdom-world-script
python -m venv .venv
.venv\Scripts\activate
pip install -e .
```

### 运行

> [!NOTE]
> 在闪耀大赛界面，看到 **"开始挑战"** 按钮后启动脚本。

```bash
python main.py
```

## 项目结构

```
roco-kingdom-world-script/
├── main.py                      # 程序入口
├── src/
│   ├── detector.py              # 图像检测引擎
│   ├── registry.py              # 事件注册表
│   ├── context.py               # 游戏共享状态
│   ├── event_dispatcher.py      # 主循环
│   ├── skill_executor.py        # 技能执行器
│   ├── elf_manager.py           # 精灵管理器
│   └── handlers/                 # 事件处理器（插件式）
├── win_util/                    # Windows UI 自动化工具
├── config/
│   ├── settings.json            # 主配置
│   └── elves.json               # 精灵配置
├── assets/templates/            # 图像识别模板
└── tests/                      # 测试套件
```

## 架构

```
┌─────────────┐     ┌──────────────┐     ┌─────────┐
│ EventDetector │ ──▶ │ EventDispatcher │ ──▶ │ Handler │
│  (图像检测)   │     │    (主循环)     │     │(处理器) │
└─────────────┘     └──────────────┘     └─────────┘
                          │
                    ┌─────▼─────┐
                    │ GameContext │
                    │ (共享状态)  │
                    └───────────┘
```

| 组件 | 职责 |
|------|------|
| EventDetector | 图像检测引擎，支持模板匹配、区域限定、超时等待 |
| EventRegistry | 事件注册表，管理事件与处理器映射 |
| EventDispatcher | 主循环，协调检测与分发 |
| Handler | 事件处理器，实现具体业务逻辑 |

### 支持的事件

`COMET_APPEARED` · `DEFENSE_APPEARED` · `DOTS_CHANGED` · `ENEMY_AVATAR` · `ENEMY_SELF_DESTRUCT` · `SWITCH_ELF` · `BATTLE_END` · `START_CHALLENGE` · `CONFIRM` · `RETRY`

## 战斗流程

```
进入战斗 → 速度检测 → 送死序列 → 战斗结算
```

### 速度检测

通过检测 **inactive dot** 出现顺序判断先手：
- 先出现在我方区域 → 我方先手（走快速流程）
- 先出现在敌方区域 → 敌方先手（走慢速流程）

### 精灵角色

| 角色 | 行为 |
|------|------|
| `final` | 首发，最后送死（收割位） |
| `sacrifice` | 送死精灵，先送死触发敌方技能 |
| `reserve` | 备用，补充伤害 |

### 完整序列

**我方先手（faster_flow）**：
1. sacrifice 上场送死
2. reserve 收割
3. final 补刀

**敌方先手（slower_flow）**：
1. final 站场骗技能
2. sacrifice 收割
3. reserve 补刀

### 自爆流处理

检测到蝴蝶等自爆精灵 → 标记 `enemy_self_destruct = True` → 点击 **retry** 继续打

非自爆流 → 点击 **quit** 退出重开

## 配置

### config/settings.json

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `similarity` | 图像识别相似度阈值 | 0.8 |
| `skill_wait_after_cast` | 技能释放后等待时间(秒) | 10 |
| `loop_count` | 循环执行轮数 | 10 |

### config/elves.json

```json
{
  "elves": [
    {"name": "幽影树", "template": ["elves/tree3.png"], "role": "final"},
    {"name": "獠牙猪", "template": "elves/pig3.png", "role": "sacrifice"},
    {"name": "权杖", "template": "elves/scepter3.png", "role": "reserve"}
  ]
}
```

## 测试

```bash
# 运行所有测试
pytest

# 运行单个测试
pytest tests/integration/test_dot_detection.py -v
```
