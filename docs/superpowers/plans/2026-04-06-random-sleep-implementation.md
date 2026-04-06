# 随机延迟方法实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将项目核心代码中的 `time.sleep` 替换为 `random_sleep` 函数，实现基于中心值 ±0.5s 的随机延迟，防止游戏封号检测。

**Architecture:** 新建 `src/utils.py` 存放通用工具函数，核心业务代码（controller, skill_executor, state_machine, battle_flow）各自添加 `from src.utils import random_sleep` 导入并替换 `time.sleep` 调用。

**Tech Stack:** Python 标准库（time, random），无新增依赖。

---

## File Structure

```
src/utils.py              # 新建 - random_sleep 工具函数
src/controller.py         # 修改 - 2处 time.sleep
src/skill_executor.py      # 修改 - 14处 time.sleep
src/state_machine.py       # 修改 - 1处 time.sleep
src/battle_flow.py         # 修改 - 9处 time.sleep
```

---

## 任务列表

### Task 1: 创建 utils.py 工具模块

**Files:**
- Create: `src/utils.py`
- Reference: `docs/superpowers/specs/2026-04-06-random-sleep-design.md`

- [ ] **Step 1: 编写实现代码**

```python
"""通用工具模块"""
import time
import random


def random_sleep(base: float) -> None:
    """随机休眠，基于中心值 ±0.5s 浮动，最小 0.05s

    用于防止游戏检测自动化脚本的固定延迟模式。

    Args:
        base: 中心延迟时间（秒）
    """
    offset = random.uniform(-0.5, 0.5)
    sleep_time = max(0.05, base + offset)
    time.sleep(sleep_time)
```

- [ ] **Step 2: 提交**

```bash
git add src/utils.py
git commit -m "feat: 添加 random_sleep 工具函数"
```

---

### Task 2: 修改 controller.py

**Files:**
- Modify: `src/controller.py:132`, `src/controller.py:144`
- Add import: `from src.utils import random_sleep`

- [ ] **Step 1: 添加导入**

在 `import time` 下方添加：
```python
from src.utils import random_sleep
```

- [ ] **Step 2: 替换第 132 行**

将 `time.sleep(0.3)` 改为 `random_sleep(0.3)`

- [ ] **Step 3: 替换第 144 行**

将 `time.sleep(0.3)` 改为 `random_sleep(0.3)`

- [ ] **Step 4: 提交**

```bash
git add src/controller.py
git commit -m "refactor(controller): time.sleep 改为 random_sleep"
```

---

### Task 3: 修改 skill_executor.py

**Files:**
- Modify: `src/skill_executor.py:39,44,48,50,58,64,73,96,105,117,119,123,143,189`
- Add import: `from src.utils import random_sleep`

> **注意:** Spec 文档中 skill_executor.py 记载的是 7 处，但实际代码中有 14 处 `time.sleep` 调用。本 plan 以实际代码为准。

- [ ] **Step 1: 添加导入**

在 `import time` 下方添加：
```python
from src.utils import random_sleep
```

- [ ] **Step 2: 替换所有 time.sleep 调用**

逐行替换以下位置：
- 第 39 行: `time.sleep(3)` → `random_sleep(3)`
- 第 44 行: `time.sleep(1)` → `random_sleep(1)`
- 第 48 行: `time.sleep(wait_time)` → `random_sleep(wait_time)`
- 第 50 行: `time.sleep(1)` → `random_sleep(1)`
- 第 58 行: `time.sleep(1)` → `random_sleep(1)`
- 第 64 行: `time.sleep(wait_time)` → `random_sleep(wait_time)`
- 第 73 行: `time.sleep(8)` → `random_sleep(8)`
- 第 96 行: `time.sleep(2)` → `random_sleep(2)`
- 第 105 行: `time.sleep(2)` → `random_sleep(2)`
- 第 117 行: `time.sleep(0.5)` → `random_sleep(0.5)`
- 第 119 行: `time.sleep(0.05)` → `random_sleep(0.05)`
- 第 123 行: `time.sleep(switch_sleep)` → `random_sleep(switch_sleep)`
- 第 143 行: `time.sleep(0.3)` → `random_sleep(0.3)`
- 第 189 行: `time.sleep(0.2)` → `random_sleep(0.2)`

- [ ] **Step 3: 提交**

```bash
git add src/skill_executor.py
git commit -m "refactor(skill_executor): time.sleep 改为 random_sleep"
```

---

### Task 4: 修改 state_machine.py

**Files:**
- Modify: `src/state_machine.py:53`
- Add import: `from src.utils import random_sleep`

- [ ] **Step 1: 添加导入**

在 `import time` 下方添加：
```python
from src.utils import random_sleep
```

- [ ] **Step 2: 替换第 53 行**

将 `time.sleep(2)` 改为 `random_sleep(2)`

- [ ] **Step 3: 提交**

```bash
git add src/state_machine.py
git commit -m "refactor(state_machine): time.sleep 改为 random_sleep"
```

---

### Task 5: 修改 battle_flow.py

**Files:**
- Modify: `src/battle_flow.py:43,49,56,63,93,125,153,179,239`
- Add import: `from src.utils import random_sleep`

- [ ] **Step 1: 添加导入**

在 `import time` 下方添加：
```python
from src.utils import random_sleep
```

- [ ] **Step 2: 替换所有 time.sleep 调用**

逐行替换以下位置：
- 第 43 行: `time.sleep(1)` → `random_sleep(1)`
- 第 49 行: `time.sleep(5)` → `random_sleep(5)`
- 第 56 行: `time.sleep(1)` → `random_sleep(1)`
- 第 63 行: `time.sleep(10)` → `random_sleep(10)`
- 第 93 行: `time.sleep(1)` → `random_sleep(1)`
- 第 125 行: `time.sleep(1)` → `random_sleep(1)`
- 第 153 行: `time.sleep(3)` → `random_sleep(3)`
- 第 179 行: `time.sleep(1)` → `random_sleep(1)`
- 第 239 行: `time.sleep(10)` → `random_sleep(10)`

- [ ] **Step 3: 提交**

```bash
git add src/battle_flow.py
git commit -m "refactor(battle_flow): time.sleep 改为 random_sleep"
```

---

## 验证

完成所有任务后，运行以下命令确认修改正确：

```bash
# 检查 random_sleep 是否被正确使用
grep -r "random_sleep" src/

# 检查是否还有遗漏的 time.sleep（排除 random_sleep 内部调用，使用单词边界精确匹配）
grep -r "\btime\.sleep\b" src/
```

**预期输出：**
- `random_sleep` 出现约 26 处（2+14+1+9）
- `time.sleep` 仅在 `src/utils.py` 的 `random_sleep` 函数定义中出现（使用 `\btime\.sleep\b` 精确匹配，排除 `mytime.sleep` 等误匹配）
