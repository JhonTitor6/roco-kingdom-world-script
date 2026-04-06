# 敌方自爆流检测与退出实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在战斗开始后检测敌方精灵是否为自爆流，如果不是则退出战斗

**Architecture:** 在现有事件驱动状态机基础上，新增敌方自爆流检测逻辑。当检测到非自爆流时，设置 `_exit_directly` flag，触发逃跑流程并跳过再次切磋。

**Tech Stack:** Python + loguru + win_util (GameController)

---

## 文件变更概览

| 文件 | 变更类型 | 职责 |
|------|----------|------|
| `src/elf_manager.py` | 修改 | 添加 `SELFDESTRUCT` 常量和 `get_selfdestruct_templates()` 方法 |
| `src/handlers/battle.py` | 修改 | 添加 `_check_enemy_selfdestruct()` 和 `_escape_battle()` 方法，修改 `_handle_battle_start()` |
| `src/handlers/battle_end.py` | 修改 | 修改 `handle()` 方法检查 `_exit_directly` flag |
| `src/event_dispatcher.py` | 修改 | 初始化并重置 `_exit_directly` flag |
| `config/settings.json` | 修改 | 添加 `enemy_region` 字段 |
| `config/elves.json` | 修改 | 添加 `selfdestruct` 角色精灵配置 |

---

## Task 1: EventDispatcher 添加 _exit_directly 初始化

**Files:**
- Modify: `src/event_dispatcher.py:48-50` (__init__)
- Modify: `src/event_dispatcher.py:55-57` (run 循环)

- [ ] **Step 1: 在 __init__ 中初始化 _exit_directly**

  修改 `src/event_dispatcher.py` 第 48 行后添加：
  ```python
  self._exit_directly = False  # 直接退出标志
  ```

- [ ] **Step 2: 在 run() 循环中重置标志**

  修改 `src/event_dispatcher.py` 第 56 行后添加：
  ```python
  self._exit_directly = False  # 重置直接退出标志
  ```

- [ ] **Step 3: 验证代码导入无错误**

  Run: `python -c "from src.event_dispatcher import EventDispatcher; print('OK')"`
  Expected: `OK`

- [ ] **Step 4: 提交**

  ```bash
  git add src/event_dispatcher.py
  git commit -m "feat(dispatcher): 添加 _exit_directly 标志初始化和重置"
  ```

---

## Task 2: ElfManager 添加自爆流支持

**Files:**
- Modify: `src/elf_manager.py:9-14` (ElfRole 类)
- Modify: `src/elf_manager.py` (新增 get_selfdestruct_templates 方法)

- [ ] **Step 1: 在 ElfRole 类中添加 SELFDESTRUCT 常量**

  修改 `src/elf_manager.py` 第 9-14 行：

  ```python
  class ElfRole:
      """精灵角色常量"""
      SACRIFICE = "sacrifice"  # 送死精灵
      FINAL = "final"         # 最后送死
      RESERVE = "reserve"     # 备用
      SELFDESTRUCT = "selfdestruct"  # 自爆流敌方精灵（用于检测）
  ```

- [ ] **Step 2: 添加 get_selfdestruct_templates() 方法**

  在 `ElfManager` 类末尾添加：

  ```python
  def get_selfdestruct_templates(self) -> List[str]:
      """获取自爆流敌方精灵的头像模板列表"""
      templates = []
      for elf in self.elves:
          if elf.get("role") == ElfRole.SELFDESTRUCT:
              template = elf.get("template")
              if isinstance(template, str):
                  templates.append(template)
              elif isinstance(template, list):
                  templates.extend(template)
      return templates
  ```

- [ ] **Step 3: 验证代码导入无错误**

  Run: `python -c "from src.elf_manager import ElfManager, ElfRole; print(ElfRole.SELFDESTRUCT)"`
  Expected: `selfdestruct`

- [ ] **Step 4: 提交**

  ```bash
  git add src/elf_manager.py
  git commit -m "feat(elf_manager): 添加 SELFDESTRUCT 角色和 get_selfdestruct_templates 方法"
  ```

---

## Task 3: settings.json 添加 enemy_region 配置

**Files:**
- Modify: `config/settings.json`

- [ ] **Step 1: 添加 enemy_region 字段**

  修改 `config/settings.json`，在末尾添加：
  ```json
  ,
  "enemy_region": [2090, 14, 2273, 181]
  ```

- [ ] **Step 2: 验证 JSON 格式正确**

  Run: `python -c "import json; f=open('config/settings.json'); json.load(f); print('OK')"`
  Expected: `OK`

- [ ] **Step 3: 提交**

  ```bash
  git add config/settings.json
  git commit -m "feat(config): 添加 enemy_region 敌方头像检测区域"
  ```

---

## Task 4: elves.json 添加自爆流精灵配置

**Files:**
- Modify: `config/elves.json`

- [ ] **Step 1: 添加 selfdestruct 角色精灵**

  修改 `config/elves.json`，在 elves 数组中添加：
  ```json
  {"name": "蝴蝶", "template": "elves/butterfly_3.png", "role": "selfdestruct"}
  ```

- [ ] **Step 2: 验证 JSON 格式正确**

  Run: `python -c "import json; f=open('config/elves.json'); json.load(f); print('OK')"`
  Expected: `OK`

- [ ] **Step 3: 提交**

  ```bash
  git add config/elves.json
  git commit -m "feat(config): 添加自爆流敌方精灵配置（蝴蝶）"
  ```

---

## Task 5: BattleHandler 添加自爆流检测方法

**Files:**
- Modify: `src/handlers/battle.py` (新增方法 + 修改 _handle_battle_start)

- [ ] **Step 1: 在 BattleHandler 类中添加 _escape_battle() 方法**

  在 `_handle_battle_start()` 方法之后添加：

  ```python
  def _escape_battle(self) -> bool:
      """执行逃跑操作：点击 escape.png → confirm.png"""
      if not self.ctrl.find_and_click_with_timeout("skills/escape.png", timeout=5, similarity=0.8):
          return False
      random_sleep(0.5)
      if not self.ctrl.find_and_click_with_timeout("popup/confirm.png", timeout=5, similarity=0.8):
          return False
      return True
  ```

- [ ] **Step 2: 在 BattleHandler 类中添加 _check_enemy_selfdestruct() 方法**

  在 `_escape_battle()` 方法之后添加：

  ```python
  def _check_enemy_selfdestruct(self) -> bool:
      """检测敌方是否为自爆流，不是则退出战斗

      Returns:
          True: 敌方是自爆流，继续战斗流程
          False: 敌方不是自爆流，已触发退出（BATTLE_END 或 ERROR）
      """
      # 1. 获取 selfdestruct 角色的敌方头像模板列表
      selfdestruct_templates = self.elf_mgr.get_selfdestruct_templates()
      if not selfdestruct_templates:
          logger.warning("未配置自爆流敌方精灵，继续战斗")
          return True

      # 2. 在 enemy_region 区域查找敌方头像
      enemy_region = self.ctrl.settings.get(
          "enemy_region",
          [2090, 14, 2273, 181]  # 默认值
      )
      for template in selfdestruct_templates:
          pos = self.ctrl.find_image(
              template,
              similarity=self.ctrl.settings.get("similarity", 0.6),
              x0=enemy_region[0], y0=enemy_region[1],
              x1=enemy_region[2], y1=enemy_region[3]
          )
          if pos != (-1, -1):
              logger.info(f"检测到敌方自爆流精灵: {template}")
              return True

      # 3. 未匹配到自爆流，执行退出
      logger.info("敌方不是自爆流，执行退出")
      self.dispatcher._exit_directly = True  # 设置直接退出标记

      if not self._escape_battle():
          logger.error("逃跑失败，进入 ERROR 状态")
          self.transition(BattleState.ERROR)
          return False

      self.transition(BattleState.BATTLE_END)
      return False
  ```

- [ ] **Step 3: 修改 _handle_battle_start() 方法**

  将原 `_handle_battle_start()` 方法（第 48-60 行）修改为：

  ```python
  def _handle_battle_start(self) -> bool:
      """等待战斗开始（comet.png 出现）"""
      if self.ctrl.find_image_with_timeout(
          "skills/comet.png",
          timeout=self.ctrl.settings["timeouts"]["battle_start"],
          similarity=0.8
      ) is None:
          logger.error("等待战斗开始超时")
          return False

      logger.info("战斗已开始")
      # 新增：检测敌方是否为自爆流
      if not self._check_enemy_selfdestruct():
          return True  # 已触发退出（BATTLE_END 或 ERROR 状态）
      self.transition(BattleState.SPEED_CHECK)
      return True
  ```

- [ ] **Step 4: 验证代码导入无错误**

  Run: `python -c "from src.handlers.battle import BattleHandler; print('OK')"`
  Expected: `OK`

- [ ] **Step 5: 提交**

  ```bash
  git add src/handlers/battle.py
  git commit -m "feat(battle): 添加敌方自爆流检测和退出逻辑"
  ```

---

## Task 6: BattleEndHandler 支持直接退出

**Files:**
- Modify: `src/handlers/battle_end.py:11-41` (修改 handle 方法)

- [ ] **Step 1: 修改 BattleEndHandler.handle() 方法**

  将原 `handle()` 方法（第 11-41 行）修改为：

  ```python
  def handle(self) -> bool:
      """处理战斗结束，点击再次切磋"""
      # 点击战斗结束按钮
      battle_end = self.ctrl.find_image_with_timeout(
          "battle/battle_end.png",
          timeout=self.ctrl.settings["timeouts"]["battle_end"],
          similarity=0.9
      )
      if battle_end is None:
          logger.warning("未检测到战斗结束标志")
          return False

      logger.info("战斗结束")
      self.ctrl.click_at(*battle_end)

      # 检测是否需要直接退出（由 _check_enemy_selfdestruct 设置的 flag）
      if getattr(self.dispatcher, '_exit_directly', False):
          logger.info("直接退出，不进行再次切磋")
          self.transition(BattleState.QUIT)
          return True

      # 点击再次切磋
      if self.ctrl.find_and_click_with_timeout("battle/retry.png", timeout=3):
          random_sleep(10)

      # 检测对手是否不想再切磋
      if self.ctrl.find_image_with_timeout(
          "battle/opponent_dont_want_to_retry.png", timeout=10
      ) is not None:
          # 对手不想再切磋 → 点击退出
          self.ctrl.find_and_click_with_timeout("battle/quit.png", timeout=2)
          self.transition(BattleState.QUIT)
      else:
          # 可以继续 → 进入 RETRY 状态等待
          self.transition(BattleState.RETRY)

      return True
  ```

- [ ] **Step 2: 验证代码导入无错误**

  Run: `python -c "from src.handlers.battle_end import BattleEndHandler; print('OK')"`
  Expected: `OK`

- [ ] **Step 3: 提交**

  ```bash
  git add src/handlers/battle_end.py
  git commit -m "feat(battle_end): 支持直接退出跳过再次切磋"
  ```

---

## Task 7: 运行完整测试验证

**Files:**
- Test: `tests/unit/test_elf_manager.py`
- Test: `tests/unit/test_battle_handler.py`

- [ ] **Step 1: 运行 ElfManager 单元测试**

  Run: `pytest tests/unit/test_elf_manager.py -v`
  Expected: 所有测试通过

- [ ] **Step 2: 运行 BattleHandler 单元测试**

  Run: `pytest tests/unit/test_battle_handler.py -v`
  Expected: 所有测试通过

- [ ] **Step 3: 运行全部测试**

  Run: `pytest tests/ -v`
  Expected: 所有测试通过

---

## Task 8: 最终提交和验证

- [ ] **Step 1: 确认所有文件变更正确**

  Run: `git diff --stat`
  Expected:
  ```
  config/elves.json         |  2 ++
  config/settings.json      |  2 ++
  src/elf_manager.py        | 12 +++++++++
  src/handlers/battle.py    | 50 ++++++++++++++++++++++++++++++++++
  src/handlers/battle_end.py | 15 +++++++++-
  src/event_dispatcher.py   |  4 +++
  ```

- [ ] **Step 2: 最终提交（显式添加文件，不使用 -A）**

  ```bash
  git add config/elves.json config/settings.json src/elf_manager.py src/handlers/battle.py src/handlers/battle_end.py src/event_dispatcher.py
  git commit -m "$(cat <<'EOF'
  feat: 实现敌方自爆流检测和退出功能

  - ElfManager 添加 SELFDESTRUCT 角色和 get_selfdestruct_templates 方法
  - EventDispatcher 添加 _exit_directly 标志初始化和重置
  - settings.json 添加 enemy_region 敌方头像检测区域
  - elves.json 添加自爆流敌方精灵配置（蝴蝶）
  - BattleHandler 添加 _check_enemy_selfdestruct 和 _escape_battle 方法
  - BattleEndHandler 支持直接退出跳过再次切磋

  Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
  EOF
  )"
  ```

- [ ] **Step 3: 验证提交成功**

  Run: `git log --oneline -3`
  Expected: 最新提交包含 "敌方自爆流检测" 相关信息
