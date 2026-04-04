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

```
main.py                  # 程序入口，初始化组件并运行主循环
├── src/
│   ├── state_machine.py # 战斗状态机 (BattleStateMachine)
│   │                     # 状态: IDLE → START_CHALLENGE → SPEED_CHECK → SACRIFICE_PHASE → BATTLE_END
│   ├── battle_flow.py   # 战斗流程控制 (BattleFlow)
│   │                     # 负责进入战斗、速度检测、送死序列、结束处理
│   ├── controller.py    # 游戏控制器 (GameController)
│   │                     # 封装 win_util，提供找图/点击/键盘/OCR
│   ├── elf_manager.py   # 精灵管理器 (ElfManager)
│   │                     # 管理精灵配置，按角色(final/sacrifice/reserve)分类
│   ├── skill_executor.py # 技能执行器 (SkillExecutor)
│   │                     # 释放技能(彗星/防御)、切换精灵、聚能
│   ├── window.py        # 窗口查找 (find_window)
│   ├── logger.py        # 日志配置 (loguru)
│   └── exceptions.py    # 自定义异常
├── win_util/            # Windows UI 自动化工具（本地依赖）
│   ├── controller.py    # WinController 整合图像识别/键鼠控制/OCR
│   ├── image.py         # ImageFinder 图像识别
│   ├── mouse.py         # MouseController 鼠标控制
│   ├── keyboard.py      # KeyboardController 键盘控制
│   └── ocr.py           # CommonOcr 文字识别
├── config/
│   ├── settings.json    # 主配置（超时、相似度、日志级别）
│   └── elves.json       # 精灵配置（template 支持单字符串或数组）
└── assets/templates/   # 图像识别模板
    ├── battle/          # 战斗相关 (start_challenge, battle_end, retry)
    ├── skills/          # 技能图标 (comet, defense)
    ├── elves/           # 精灵头像 (tree3, otter2, pig3, scepter3)
    ├── dots/            # 圆点状态 (dot_active, dot_inactive)
    └── popup/           # 弹窗 (confirm, insufficient)
```

## 核心模块说明

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

## 注意事项

- 中文路径截图读取：`PIL.Image.open()` + `cv2.cvtColor()`，不用 `cv2.imread`
- 后台点击不生效时使用前台点击 `left_click`
- 弹窗确认按钮点击 `confirm.png` 模板位置，而非弹窗本身
- 精灵面板切换无明确图标，用左侧区域(x<600)精灵头像检测替代
