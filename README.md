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

- **全自动战斗流程**：自动进入战斗、检测速度优势、执行送死序列、处理战斗结算
- **智能图像识别**：基于 OpenCV 模板匹配，支持中文路径截图处理
- **灵活精灵管理**：支持首发、送死、备用多种角色配置
- **多种技能执行**：彗星技能、防御姿态、聚能切换
- **后台运行**：无需游戏窗口在前台，支持后台自动化控制

## 待实现功能

- [ ] **敌方阵容识别**：识别对方精灵类型，判断是否为自爆流，针对性调整送死策略
- [ ] **健壮性优化**：增强异常场景处理，提高脚本稳定性
- [ ] **后台点击**：支持后台点击，解放键鼠，边刷视频边挂机

## 项目结构

```
roco-kingdom-world-script/
├── main.py                 # 程序入口
├── src/                    # 核心源代码
│   ├── state_machine.py    # 战斗状态机
│   ├── battle_flow.py      # 战斗流程控制
│   ├── controller.py       # 游戏控制器（封装 win_util）
│   ├── elf_manager.py      # 精灵管理器
│   ├── skill_executor.py   # 技能执行器
│   ├── window.py           # 窗口查找
│   ├── logger.py           # 日志配置
│   └── exceptions.py       # 自定义异常
├── win_util/               # Windows UI 自动化工具
├── config/                 # 配置文件
│   ├── settings.json       # 主配置（超时、相似度）
│   └── elves.json          # 精灵配置
├── assets/templates/       # 图像识别模板
│   ├── battle/            # 战斗相关模板
│   ├── skills/            # 技能图标
│   ├── elves/             # 精灵头像
│   ├── dots/              # 圆点状态
│   └── popup/             # 弹窗按钮
└── tests/                  # 测试套件
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
IDLE → START_CHALLENGE → SPEED_CHECK → SACRIFICE_PHASE → BATTLE_END → RETRY
```

1. **进入战斗**：点击开始挑战 → 检查精灵不足弹窗 → 选择首发 → 确认 → 等待战斗开始
2. **速度检测**：通过检测 inactive dot 出现顺序判断我方/敌方谁先行动
3. **送死序列**：
   - 有速度优势：sacrifice 送死 → reserve → reserve 循环防御/聚能
   - 无速度优势：final 循环防御/聚能 → 等待敌方送死3只 → reserve 送死 → sacrifice 送死 → final 送死
4. **战斗结束**：点击再次切磋 → 退出

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
| 状态 | `dot_active.png` | 活跃圆点 |
| | `dot_inactive.png` | 非活跃圆点 |
| 弹窗 | `confirm.png` | 确认按钮 |
| | `insufficient.png` | 精灵不足提示 |

## 测试

```bash
# 运行所有测试
pytest

# 运行单个测试文件
pytest tests/integration/test_dot_detection.py -v

# 运行单元测试
pytest tests/unit/ -v
```

