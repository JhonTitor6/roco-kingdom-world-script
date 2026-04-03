# 洛克王国闪耀大赛自动化 - Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现洛克王国 PC 客户端闪耀大赛自动刷金币脚本，通过图像识别和后台模拟输入完成自动化战斗。

**Architecture:** 状态机 + 配置驱动。GameController 封装 win_util 提供统一的识图/点击/按键接口；ElfManager 管理精灵配置和存活数检测；SkillExecutor 执行技能和切换；BattleFlow 实现战斗逻辑；StateMachine 协调状态流转。

**Tech Stack:** Python 3.x / win_util (OpenCV + EasyOCR + win32) / JSON 配置

---

## File Structure

```
roco-kingdom-world-script/
├── main.py                     # 程序入口
├── run.bat                     # 运行脚本
├── requirements.txt            # 依赖
├── config/
│   ├── settings.json          # 全局设置
│   └── elves.json             # 精灵配置
├── assets/
│   └── templates/             # 模板图像（用户截取）
│       ├── skills/
│       │   ├── comet.png     # 彗星
│       │   └── defense.png   # 防御
│       ├── battle/
│       │   ├── battle_start.png  # 战斗开始（彗星出现）
│       │   ├── battle_end.png    # 战斗结束
│       │   ├── retry.png         # 再次切磋
│       │   └── quit.png          # 退出
│       ├── dots/
│       │   ├── dot_active.png    # 亮着的小圆点
│       │   └── dot_inactive.png  # 熄灭的小圆点
│       ├── elves/
│       │   └── elf_*.png         # 精灵头像
│       └── popup/
│           ├── insufficient.png   # 精灵数不足
│           ├── confirm.png        # 确认按钮
│           ├── select_first.png   # 选择首发精灵界面
│           └── switch_panel.png   # 切换精灵面板
└── src/
    ├── __init__.py
    ├── exceptions.py          # 自定义异常
    ├── logger.py              # 日志模块
    ├── window.py              # 窗口查找
    ├── controller.py          # 游戏控制器
    ├── elf_manager.py         # 精灵管理器
    ├── skill_executor.py      # 技能执行器
    ├── battle_flow.py         # 战斗流程
    └── state_machine.py       # 状态机
```

---

## Phase 1: 基础设施

### Task 1: 项目配置和入口

**Files:**
- Modify: `pyproject.toml`
- Create: `requirements.txt`
- Create: `run.bat`
- Create: `config/settings.json`
- Create: `config/elves.json`
- Create: `main.py`
- Create: `src/__init__.py`

- [ ] **Step 1: 更新 pyproject.toml**

```toml
[project]
name = "roco-kingdom-script"
version = "0.1.0"
dependencies = [
    "win-util @ file:///F:/Users/56440/PythonProjects/roco-kingdom-world-script/win_util",
    "loguru>=0.7.0",
    "numpy>=1.26.0",
]

[project.scripts]
roco = "main:main"
```

- [ ] **Step 2: 创建 requirements.txt**

```
loguru>=0.7.0
numpy>=1.26.0
opencv-python>=4.8.0
easyocr>=1.7.0
pywin32>=300
Pillow>=10.0.0
mss>=10.0.0
```

- [ ] **Step 3: 创建 run.bat**

```bat
@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat
python main.py
pause
```

- [ ] **Step 4: 创建 config/settings.json**

```json
{
  "similarity": 0.8,
  "timeouts": {
    "battle_start": 10,
    "skill_cast": 5,
    "switch_elf": 3,
    "battle_end": 10
  },
  "loop_count": 10,
  "screenshot_debug": "on_failure",
  "log_level": "DEBUG",
  "window": {
    "class_name": "UnrealWindow",
    "title": "洛克王国：世界"
  }
}
```

- [ ] **Step 5: 创建 config/elves.json（示例配置）**

```json
{
  "elves": [
    {"name": "精灵A", "template": "elves/elf_1.png", "role": "sacrifice"},
    {"name": "精灵B", "template": "elves/elf_2.png", "role": "sacrifice"},
    {"name": "精灵C", "template": "elves/elf_3.png", "role": "final"},
    {"name": "精灵D", "template": "elves/elf_4.png", "role": "reserve"}
  ],
  "final_action": "energy"
}
```

- [ ] **Step 6: 创建 src/__init__.py**

```python
"""洛克王国闪耀大赛自动化脚本"""
__version__ = "0.1.0"
```

- [ ] **Step 7: 创建 main.py**

```python
"""程序入口"""
import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.logger import setup_logger
from src.window import find_window
from src.controller import GameController
from src.elf_manager import ElfManager
from src.skill_executor import SkillExecutor
from src.battle_flow import BattleFlow
from src.state_machine import BattleStateMachine
from src.exceptions import GameWindowNotFoundError
import json


def load_settings() -> dict:
    settings_path = Path(__file__).parent / "config" / "settings.json"
    with open(settings_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_elves_config() -> dict:
    elves_path = Path(__file__).parent / "config" / "elves.json"
    with open(elves_path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    settings = load_settings()
    logger = setup_logger(settings["log_level"])

    logger.info("=" * 50)
    logger.info("洛克王国闪耀大赛自动化脚本启动")
    logger.info("=" * 50)

    # 查找游戏窗口
    try:
        hwnd = find_window(
            class_name=settings["window"]["class_name"],
            title=settings["window"]["title"]
        )
    except GameWindowNotFoundError as e:
        logger.error(str(e))
        return

    # 初始化组件
    controller = GameController(hwnd=hwnd, settings=settings)
    elf_manager = ElfManager(config=load_elves_config(), controller=controller)
    skill_executor = SkillExecutor(controller=controller)
    battle_flow = BattleFlow(
        controller=controller,
        elf_manager=elf_manager,
        skill_executor=skill_executor,
        settings=settings
    )
    state_machine = BattleStateMachine(battle_flow=battle_flow)

    # 运行主循环
    logger.info(f"开始执行 {settings['loop_count']} 轮战斗")
    try:
        state_machine.run(loop_count=settings["loop_count"])
    except KeyboardInterrupt:
        logger.info("用户中断，程序退出")
    except GameWindowNotFoundError:
        logger.error("游戏窗口已关闭，程序退出")
    finally:
        logger.info("脚本已停止")


if __name__ == "__main__":
    main()
```

- [ ] **Step 8: Commit**

```bash
git add pyproject.toml requirements.txt run.bat config/settings.json config/elves.json main.py src/__init__.py
git commit -m "feat: 项目基础结构和入口"
```

---

### Task 2: 日志模块和自定义异常

**Files:**
- Create: `src/logger.py`
- Create: `src/exceptions.py`

- [ ] **Step 1: 创建 src/exceptions.py**

```python
"""自定义异常"""


class RocoBaseError(Exception):
    """项目基础异常"""
    pass


class GameWindowNotFoundError(RocoBaseError):
    """游戏窗口未找到"""
    pass


class ImageNotFoundError(RocoBaseError):
    """图像识别失败"""
    pass


class BattleTimeoutError(RocoBaseError):
    """战斗超时"""
    pass


class ConfigError(RocoBaseError):
    """配置错误"""
    pass


class ElfNotFoundError(RocoBaseError):
    """精灵未找到"""
    pass
```

- [ ] **Step 2: 创建 src/logger.py**

```python
"""日志模块"""
import sys
from pathlib import Path
from loguru import logger


def setup_logger(level: str = "DEBUG") -> logger:
    """配置日志

    Args:
        level: 日志级别 DEBUG / INFO / WARNING

    Returns:
        logger 实例
    """
    # 移除默认 handler
    logger.remove()

    # 添加控制台输出
    logger.add(
        sys.stderr,
        level=level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        colorize=True
    )

    # 添加文件输出
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    logger.add(
        log_dir / "roco_{time:YYYY-MM-DD}.log",
        level="DEBUG",
        rotation="00:00",
        retention="7 days",
        encoding="utf-8",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}"
    )

    return logger


def get_logger():
    """获取 logger 实例（方便导入）"""
    return logger
```

- [ ] **Step 3: Commit**

```bash
git add src/exceptions.py src/logger.py
git commit -m "feat: 日志模块和自定义异常"
```

---

### Task 3: 窗口查找模块

**Files:**
- Create: `src/window.py`

- [ ] **Step 1: 创建 src/window.py**

```python
"""窗口查找模块"""
import win32gui
from loguru import logger
from src.exceptions import GameWindowNotFoundError


def find_window(class_name: str = "UnrealWindow", title: str = "洛克王国：世界") -> int:
    """查找游戏窗口

    Args:
        class_name: 窗口类名
        title: 窗口标题（部分匹配）

    Returns:
        窗口句柄 (hwnd)

    Raises:
        GameWindowNotFoundError: 未找到窗口
    """
    # 先尝试精确标题匹配
    hwnd = win32gui.FindWindow(class_name, title)
    if hwnd:
        logger.info(f"找到游戏窗口: hwnd={hwnd}, title='{title}'")
        return hwnd

    # 尝试部分匹配（枚举所有窗口）
    result = []

    def enum_callback(hwnd, extra):
        window_title = win32gui.GetWindowText(hwnd)
        if title in window_title:
            result.append(hwnd)

    win32gui.EnumWindows(enum_callback, None)

    if result:
        hwnd = result[0]
        logger.info(f"通过部分匹配找到窗口: hwnd={hwnd}, title='{win32gui.GetWindowText(hwnd)}'")
        return hwnd

    raise GameWindowNotFoundError(f"未找到游戏窗口: class_name={class_name}, title={title}")


def is_window_valid(hwnd: int) -> bool:
    """检查窗口是否有效"""
    try:
        return win32gui.IsWindow(hwnd) and win32gui.IsWindowVisible(hwnd)
    except Exception:
        return False


def get_window_rect(hwnd: int) -> tuple:
    """获取窗口客户区矩形 (left, top, right, bottom)"""
    return win32gui.GetClientRect(hwnd)
```

- [ ] **Step 2: Commit**

```bash
git add src/window.py
git commit -m "feat: 窗口查找模块"
```

---

## Phase 2: 核心控制器

### Task 4: 游戏控制器

**Files:**
- Create: `src/controller.py`

- [ ] **Step 1: 创建 src/controller.py**

```python
"""游戏控制器 - 封装 win_util"""
from pathlib import Path
from typing import Optional, Tuple, List
import time

from loguru import logger
from win_util import WinController

from src.exceptions import ImageNotFoundError


class GameController:
    """封装 win_util 的游戏控制器"""

    # 模板基础路径
    TEMPLATE_BASE = Path(__file__).parent.parent / "assets" / "templates"

    def __init__(self, hwnd: int, settings: dict):
        self.hwnd = hwnd
        self.settings = settings
        self.win = WinController(hwnd=hwnd)
        self._similarity = settings.get("similarity", 0.8)

    def capture(self) -> None:
        """更新截图缓存"""
        self.win.update_screenshot_cache()

    def get_screenshot(self):
        """获取当前截图"""
        return self.win.image_finder.screenshot_cache

    def find_image(self, template_path: str, similarity: float = None) -> Tuple[int, int]:
        """在截图缓存中查找图像

        Args:
            template_path: 相对于 TEMPLATE_BASE 的路径
            similarity: 相似度阈值

        Returns:
            (x, y) 坐标，未找到返回 (-1, -1)
        """
        sim = similarity or self._similarity
        full_path = self.TEMPLATE_BASE / template_path

        # 更新截图
        self.capture()

        result = self.win.image_finder.bg_find_pic_by_cache(
            str(full_path),
            similarity=sim
        )

        if result == (-1, -1):
            logger.debug(f"图像未找到: {template_path}")
            return -1, -1

        logger.debug(f"图像找到: {template_path} @ {result}")
        return result

    def find_image_with_timeout(
        self, template_path: str, timeout: float = 5, similarity: float = None
    ) -> Optional[Tuple[int, int]]:
        """等待图像出现

        Args:
            template_path: 模板路径
            timeout: 超时时间（秒）
            similarity: 相似度

        Returns:
            (x, y) 或 None
        """
        start = time.time()
        while time.time() - start < timeout:
            pos = self.find_image(template_path, similarity)
            if pos != (-1, -1):
                return pos
            time.sleep(0.3)
        return None

    def wait_for_image_disappear(
        self, template_path: str, timeout: float = 5, similarity: float = None
    ) -> bool:
        """等待图像消失"""
        start = time.time()
        while time.time() - start < timeout:
            pos = self.find_image(template_path, similarity)
            if pos == (-1, -1):
                return True
            time.sleep(0.3)
        return False

    def click_at(self, x: int, y: int, x_range: int = 20, y_range: int = 20) -> bool:
        """在指定位置点击"""
        return self.win.mouse.bg_left_click((x, y), x_range=x_range, y_range=y_range)

    def find_and_click(self, template_path: str, similarity: float = None) -> bool:
        """查找图像并点击"""
        pos = self.find_image(template_path, similarity)
        if pos == (-1, -1):
            return False
        return self.click_at(*pos)

    def press_key(self, key: str) -> None:
        """按键"""
        self.win.keyboard.bg_press_key(key)

    def ocr_text(self, image) -> List[str]:
        """OCR 识别文本"""
        return self.win.ocr.find_all_texts(image)

    def find_text_position(self, text: str, similarity: float = 0.3) -> Optional[Tuple[int, int]]:
        """查找文本位置"""
        screenshot = self.get_screenshot()
        if screenshot is None:
            return None
        return self.win.ocr.find_text_position(screenshot, text, similarity_threshold=similarity)

    def save_debug_screenshot(self, name: str) -> Path:
        """保存调试截图"""
        import cv2
        screenshot = self.get_screenshot()
        if screenshot is None:
            return None
        debug_dir = Path(__file__).parent.parent / "logs" / "debug"
        debug_dir.mkdir(exist_ok=True)
        path = debug_dir / f"{name}_{int(time.time())}.png"
        cv2.imwrite(str(path), screenshot)
        logger.debug(f"调试截图已保存: {path}")
        return path
```

- [ ] **Step 2: Commit**

```bash
git add src/controller.py
git commit -m "feat: 游戏控制器封装"
```

---

### Task 5: 精灵管理器

**Files:**
- Create: `src/elf_manager.py`

- [ ] **Step 1: 创建 src/elf_manager.py**

```python
"""精灵管理器"""
from typing import List, Dict, Optional
from loguru import logger

from src.controller import GameController
from src.exceptions import ElfNotFoundError


class ElfRole:
    """精灵角色常量"""
    SACRIFICE = "sacrifice"  # 送死精灵
    FINAL = "final"         # 最后送死
    RESERVE = "reserve"     # 备用


class ElfManager:
    """管理精灵配置和状态"""

    def __init__(self, config: dict, controller: GameController):
        self.config = config
        self.controller = controller
        self.elves: List[Dict] = config["elves"]
        self.final_action = config.get("final_action", "energy")

        # 按角色分类
        self._final_elf = self._get_elf_by_role(ElfRole.FINAL)
        self._reserve_elf = self._get_elf_by_role(ElfRole.RESERVE)
        self._sacrifice_elves = self._get_elves_by_role(ElfRole.SACRIFICE)

    def _get_elf_by_role(self, role: str) -> Optional[Dict]:
        """获取指定角色的第一个精灵"""
        for elf in self.elves:
            if elf.get("role") == role:
                return elf
        return None

    def _get_elves_by_role(self, role: str) -> List[Dict]:
        """获取指定角色的所有精灵"""
        return [elf for elf in self.elves if elf.get("role") == role]

    @property
    def final_elf(self) -> Dict:
        """获取 final 精灵"""
        if not self._final_elf:
            raise ValueError("配置中未找到 final 精灵")
        return self._final_elf

    @property
    def reserve_elf(self) -> Dict:
        """获取 reserve 精灵"""
        if not self._reserve_elf:
            raise ValueError("配置中未找到 reserve 精灵")
        return self._reserve_elf

    @property
    def sacrifice_elves(self) -> List[Dict]:
        """获取 sacrifice 精灵列表"""
        return self._sacrifice_elves

    def count_alive_elves(self) -> int:
        """统计我方存活精灵数（通过识别小圆点）"""
        # 识图查找亮着的小圆点数量
        # 小圆点排列区域需要通过截图确定具体位置
        # 这里先用固定区域，运行时可能需要调整
        active_dots = self.controller.find_images_all(
            "dots/dot_active.png",
            similarity=0.8
        )
        count = len(active_dots)
        logger.debug(f"检测到存活精灵数: {count}")
        return count

    def find_elf_position(self, elf: Dict) -> Optional[tuple]:
        """在切换精灵面板中查找精灵位置

        Args:
            elf: 精灵配置 dict

        Returns:
            (x, y) 或 None
        """
        template = elf["template"]
        pos = self.controller.find_image(template, similarity=0.8)
        if pos == (-1, -1):
            logger.warning(f"未找到精灵: {elf['name']} ({template})")
            return None
        return pos

    def get_sacrifice_order(self, faster: bool) -> List[Dict]:
        """获取送死顺序

        Args:
            faster: True=我方速度快，False=对方速度快

        Returns:
            按送死顺序排列的精灵列表
        """
        if faster:
            # 我方先手: final -> sacrifice -> sacrifice -> reserve
            order = [self.final_elf] + self.sacrifice_elves + [self.reserve_elf]
        else:
            # 对方先手: reserve -> sacrifice -> sacrifice -> final
            order = [self.reserve_elf] + self.sacrifice_elves + [self.final_elf]
        return order

    def get_final_action(self) -> str:
        """获取最后精灵的动作"""
        return self.final_action
```

- [ ] **Step 2: Commit**

```bash
git add src/elf_manager.py
git commit -m "feat: 精灵管理器"
```

---

## Phase 3: 战斗执行

### Task 6: 技能执行器

**Files:**
- Create: `src/skill_executor.py`

- [ ] **Step 1: 创建 src/skill_executor.py**

```python
"""技能执行器"""
import time
from loguru import logger

from src.controller import GameController


class SkillExecutor:
    """执行技能和精灵切换"""

    def __init__(self, controller: GameController):
        self.ctrl = controller

    def cast_skill(self, skill_name: str) -> bool:
        """释放技能（通过识图点击技能栏）

        Args:
            skill_name: 技能名 (comet / defense)

        Returns:
            是否成功
        """
        template_map = {
            "comet": "skills/comet.png",
            "defense": "skills/defense.png",
        }
        template = template_map.get(skill_name)
        if not template:
            logger.error(f"未知技能: {skill_name}")
            return False

        pos = self.ctrl.find_image(template, similarity=0.8)
        if pos == (-1, -1):
            logger.warning(f"技能图标未找到: {skill_name}")
            return False

        self.ctrl.click_at(*pos)
        logger.info(f"释放技能: {skill_name}")
        return True

    def press_energy(self) -> None:
        """聚能（按 X 键）"""
        self.ctrl.press_key('X')
        logger.info("聚能 (X)")

    def press_defense(self) -> None:
        """防御（按 4 键，识图点击）"""
        self.cast_skill("defense")

    def switch_to_elf(self, elf) -> bool:
        """切换到指定精灵

        Args:
            elf: 精灵配置 dict

        Returns:
            是否成功
        """
        # 按 E 打开切换面板
        self.ctrl.press_key('E')
        time.sleep(0.5)

        # 识图查找目标精灵
        pos = self.ctrl.find_image(elf["template"], similarity=0.8)
        if pos == (-1, -1):
            logger.warning(f"切换精灵失败: {elf['name']}")
            self.ctrl.press_key('E')  # 关闭面板
            return False

        self.ctrl.click_at(*pos)
        logger.info(f"切换精灵: {elf['name']}")
        return True

    def select_first_elf(self, elf) -> bool:
        """在选择首发精灵界面选择精灵

        Args:
            elf: 精灵配置 dict

        Returns:
            是否成功
        """
        pos = self.ctrl.find_image(elf["template"], similarity=0.8)
        if pos == (-1, -1):
            logger.warning(f"选择首发精灵失败: {elf['name']}")
            return False

        self.ctrl.click_at(*pos)
        logger.info(f"选择首发精灵: {elf['name']}")
        return True

    def confirm_selection(self) -> bool:
        """确认选择"""
        return self.ctrl.find_and_click("popup/confirm.png")

    def wait_for_switch_panel(self, timeout: float = 3) -> bool:
        """等待切换面板出现"""
        pos = self.ctrl.find_image_with_timeout("popup/switch_panel.png", timeout=timeout)
        return pos is not None
```

- [ ] **Step 2: Commit**

```bash
git add src/skill_executor.py
git commit -m "feat: 技能执行器"
```

---

### Task 7: 战斗流程

**Files:**
- Create: `src/battle_flow.py`

- [ ] **Step 1: 创建 src/battle_flow.py**

```python
"""战斗流程"""
import time
from loguru import logger

from src.controller import GameController
from src.elf_manager import ElfManager, ElfRole
from src.skill_executor import SkillExecutor
from src.exceptions import ImageNotFoundError, BattleTimeoutError


class BattleFlow:
    """战斗流程控制"""

    def __init__(
        self,
        controller: GameController,
        elf_manager: ElfManager,
        skill_executor: SkillExecutor,
        settings: dict
    ):
        self.ctrl = controller
        self.elf_mgr = elf_manager
        self.skill = skill_executor
        self.settings = settings

    def run_entry_flow(self) -> bool:
        """进入战斗的流程

        Returns:
            是否成功进入战斗
        """
        timeouts = self.settings["timeouts"]

        # 1. 点击开始挑战
        if not self.ctrl.find_and_click("battle/start_challenge.png"):
            logger.warning("未找到「开始挑战」按钮")
            return False
        time.sleep(0.5)

        # 2. 检查精灵数不足弹窗
        insufficient_pos = self.ctrl.find_image("popup/insufficient.png", similarity=0.8)
        if insufficient_pos != (-1, -1):
            logger.info("检测到精灵数不足弹窗，点击确认")
            self.ctrl.click_at(*insufficient_pos)
            time.sleep(0.3)

        # 3. 选择首发精灵（final 精灵）
        if not self.skill.select_first_elf(self.elf_mgr.final_elf):
            logger.error("选择首发精灵失败")
            return False
        time.sleep(0.3)

        # 4. 确认首发
        if not self.skill.confirm_selection():
            logger.error("确认首发失败")
            return False

        # 5. 等待战斗开始
        battle_start = self.ctrl.find_image_with_timeout(
            "skills/comet.png",
            timeout=timeouts["battle_start"],
            similarity=0.8
        )
        if battle_start is None:
            logger.error("等待战斗开始超时")
            return False

        logger.info("战斗已开始")
        return True

    def detect_speed_advantage(self) -> bool:
        """检测速度优势（通过判断我方是否先送死）

        Returns:
            True=我方速度快，False=对方速度快
        """
        # 等待一轮行动，看我方精灵是否先减少
        initial_count = self.elf_mgr.count_alive_elves()
        logger.debug(f"初始精灵数: {initial_count}")

        # 等待约 2 秒检测变化
        for _ in range(10):
            time.sleep(0.3)
            current_count = self.elf_mgr.count_alive_elves()
            if current_count < initial_count:
                logger.info(f"我方先送死，速度优势")
                return True

        logger.info(f"对方先送死，速度劣势")
        return False

    def wait_for_enemy_sacrifice(self, target: int = 3) -> bool:
        """等待对方送死指定数量

        Args:
            target: 目标送死数量

        Returns:
            是否等到

        Note:
            敌方小圆点区域在屏幕右上区域（相对于游戏窗口），
            具体坐标需要根据实际截图确定。当前使用固定区域搜索。
            闪耀大赛固定 4v4，敌方初始4只。
        """
        initial_enemy_count = 4  # 闪耀大赛固定 4v4

        for _ in range(30):  # 最多等 30 * 0.5 = 15 秒
            time.sleep(0.5)

            # 识图查找敌方小圆点（右上区域）
            # TODO: 替换为实际测量的区域坐标
            # enemy_dots = self.ctrl.find_images_all(
            #     "dots/dot_active.png",
            #     x0=窗口宽度//2, y0=0, x1=窗口宽度, y1=窗口高度//2,
            #     similarity=0.8
            # )
            # enemy_count = len(enemy_dots)
            #
            # if enemy_count <= initial_enemy_count - target:
            #     logger.info(f"敌方已送死 {target} 只，当前剩余 {enemy_count}")
            #     return True

            pass  # TODO: 根据实际截图确定区域后实现

        logger.warning(f"等待对方送死超时（等待 {target} 只）")
        return False

    def sacrifice_sequence(self, order: list) -> None:
        """执行送死序列

        Args:
            order: 送死顺序的精灵列表
        """
        for i, elf in enumerate(order):
            logger.info(f"送死 #{i+1}: {elf['name']}")
            # 释放彗星
            if not self.skill.cast_skill("comet"):
                logger.warning(f"释放彗星失败: {elf['name']}")
            time.sleep(1)

            # 如果是最后一只，执行最终动作
            if i == len(order) - 1:
                action = self.elf_mgr.get_final_action()
                if action == "energy":
                    self.skill.press_energy()
                else:
                    self.skill.cast_skill("defense")

    def faster_flow(self) -> None:
        """我方速度快的流程"""
        logger.info("=== 速度优势流程 ===")

        # 1. final 先送死
        logger.info("Final 精灵送死")
        self.skill.cast_skill("comet")
        time.sleep(1)

        # 2. sacrifice 精灵送死
        for elf in self.elf_mgr.sacrifice_elves:
            logger.info(f"送死: {elf['name']}")
            self.skill.cast_skill("comet")
            time.sleep(1)

        # 3. 等待对方送死 3 只
        logger.info("等待对方送死 3 只...")
        self.wait_for_enemy_sacrifice(3)

        # 4. 切换到 reserve
        logger.info("切换到 reserve 精灵")
        self.skill.switch_to_elf(self.elf_mgr.reserve_elf)

        # 5. reserve 执行最终动作
        action = self.elf_mgr.get_final_action()
        if action == "energy":
            self.skill.press_energy()
        else:
            self.skill.cast_skill("defense")

    def slower_flow(self) -> None:
        """我方速度慢的流程"""
        logger.info("=== 速度劣势流程 ===")

        # 1. final 防御/聚能
        logger.info("Final 精灵防御/聚能")
        action = self.elf_mgr.get_final_action()
        if action == "energy":
            self.skill.press_energy()
        else:
            self.skill.cast_skill("defense")

        # 2. 等待对方送死 3 只
        logger.info("等待对方送死 3 只...")
        self.wait_for_enemy_sacrifice(3)

        # 3. 切换到 reserve
        logger.info("切换到 reserve 精灵")
        self.skill.switch_to_elf(self.elf_mgr.reserve_elf)

        # 4. reserve 送死
        self.skill.cast_skill("comet")
        time.sleep(1)

        # 5. sacrifice 精灵送死
        for elf in self.elf_mgr.sacrifice_elves:
            logger.info(f"送死: {elf['name']}")
            self.skill.cast_skill("comet")
            time.sleep(1)

        # 6. final 送死
        logger.info("Final 精灵送死")
        self.skill.cast_skill("comet")

    def handle_battle_end(self) -> bool:
        """处理战斗结束

        Returns:
            是否应该继续下一轮
        """
        # 检测战斗结束图标
        battle_end = self.ctrl.find_image_with_timeout(
            "battle/battle_end.png",
            timeout=self.settings["timeouts"]["battle_end"],
            similarity=0.8
        )
        if battle_end is None:
            logger.warning("未检测到战斗结束标志")
            return False

        logger.info("战斗结束")

        # 点击再次切磋
        if self.ctrl.find_and_click("battle/retry.png"):
            time.sleep(0.5)
            # 检测对方不想切磋
            if self.ctrl.find_image("battle/quit.png", similarity=0.8) != (-1, -1):
                logger.info("对方不想切磋，点击退出")
                self.ctrl.find_and_click("battle/quit.png")
                time.sleep(0.5)
            return True

        return False
```

- [ ] **Step 2: Commit**

```bash
git add src/battle_flow.py
git commit -m "feat: 战斗流程实现"
```

---

### Task 8: 状态机

**Files:**
- Create: `src/state_machine.py`

- [ ] **Step 1: 创建 src/state_machine.py**

```python
"""状态机"""
import time
from enum import Enum
from loguru import logger

from src.battle_flow import BattleFlow
from src.exceptions import GameWindowNotFoundError


class BattleState(Enum):
    """战斗状态枚举"""
    IDLE = "idle"
    START_CHALLENGE = "start_challenge"
    CHECK_INSUFFICIENT = "check_insufficient"
    SELECT_FIRST = "select_first"
    CONFIRM_FIRST = "confirm_first"
    BATTLE_START = "battle_start"
    SPEED_CHECK = "speed_check"
    SACRIFICE_PHASE = "sacrifice_phase"
    FINAL_PHASE = "final_phase"
    SWITCH_ELF = "switch_elf"
    BATTLE_END = "battle_end"
    RETRY = "retry"
    QUIT = "quit"
    ERROR = "error"


class BattleStateMachine:
    """战斗状态机"""

    def __init__(self, battle_flow: BattleFlow):
        self.state = BattleState.IDLE
        self.flow = battle_flow
        self.error_count = 0
        self.max_errors = 3

    def transition(self, new_state: BattleState) -> None:
        """状态切换"""
        logger.debug(f"状态: {self.state.value} -> {new_state.value}")
        self.state = new_state

    def run(self, loop_count: int) -> None:
        """运行主循环"""
        for i in range(loop_count):
            logger.info(f"========== 第 {i+1}/{loop_count} 轮 ==========")
            success = self._run_one_round()
            if not success:
                self.error_count += 1
                logger.warning(f"第 {i+1} 轮执行失败 (error_count={self.error_count})")
                if self.error_count >= self.max_errors:
                    logger.error("连续错误过多，停止脚本")
                    break
                time.sleep(2)  # 出错后等待
            else:
                self.error_count = 0  # 成功后重置计数

        logger.info(f"完成 {loop_count} 轮")

    def _run_one_round(self) -> bool:
        """执行一轮战斗"""
        try:
            self.transition(BattleState.START_CHALLENGE)

            # 进入战斗流程
            if not self.flow.run_entry_flow():
                logger.error("进入战斗失败")
                return False

            self.transition(BattleState.SPEED_CHECK)

            # 检测速度优势
            faster = self.flow.detect_speed_advantage()

            self.transition(BattleState.SACRIFICE_PHASE)

            # 执行对应流程
            if faster:
                self.flow.faster_flow()
            else:
                self.flow.slower_flow()

            self.transition(BattleState.BATTLE_END)

            # 处理战斗结束
            return self.flow.handle_battle_end()

        except GameWindowNotFoundError:
            logger.error("游戏窗口已关闭")
            raise
        except Exception as e:
            logger.exception(f"执行异常: {e}")
            self.transition(BattleState.ERROR)

            # 保存调试截图
            self.flow.ctrl.save_debug_screenshot(f"error_{int(time.time())}")

            return False
```

- [ ] **Step 2: Commit**

```bash
git add src/state_machine.py
git commit -m "feat: 状态机实现"
```

---

## Phase 4: 收尾

### Task 9: 清理和验证

- [ ] **Step 1: 创建 .gitignore**

```
# Python
__pycache__/
*.py[cod]
*.egg-info/
.venv/

# Logs
logs/*.log
logs/debug/*.png

# Assets templates (用户提供的截图)
assets/templates/**/*.png
!assets/templates/.gitkeep
```

- [ ] **Step 2: 创建 assets/templates/.gitkeep**

```bash
# placeholder for template images
```

- [ ] **Step 3: 提交**

```bash
git add .gitignore assets/templates/.gitkeep
git commit -m "chore: 添加 .gitignore 和 assets 占位文件"
```

- [ ] **Step 4: 验证整体结构**

```bash
tree -L 3 --dirsfirst
```

---

## Implementation Order

```
Phase 1: 基础设施
  Task 1 → Task 2 → Task 3

Phase 2: 核心控制器
  Task 4 → Task 5

Phase 3: 战斗执行
  Task 6 → Task 7 → Task 8

Phase 4: 收尾
  Task 9
```

**总 Commit 数**: 约 10 个

---

## Notes

1. **精灵数量检测**: `ElfManager.count_alive_elves()` 和敌方精灵数检测需要根据实际截图确定区域坐标（血条下方的小圆点区域位置）。界面上我方小圆点在左下，敌方小圆点在右上，区域坐标需要实测后硬编码或配置化。
2. **敌方存活数检测**: `wait_for_enemy_sacrifice()` 需要识别敌方小圆点区域（右上区域），计算亮着的点数。当前为占位实现，需根据实际截图确定搜索区域。
3. **模板路径**: 所有模板路径都相对于 `assets/templates/`，用户截取后放到对应子目录即可。
4. **调试截图**: 仅在 `ERROR` 状态时保存，策略为 `on_failure`。
5. **战斗流程逻辑澄清**: 根据 spec Section 4.5:
   - `faster_flow`: final 先送死 → sacrifice 送死 → reserve 防御/聚能
   - `slower_flow`: final 防御/聚能 → 对方送死3只 → reserve 送死 → sacrifice 送死 → final 送死
6. **battle_start.png**: 用于检测战斗开始的标志（彗星技能出现），在 spec 中已列出。

